import json
from pathlib import Path
import subprocess
import sys

import pytest

from dynamo_diff.compare import compare_runs
from dynamo_diff.errors import DynamoDiffError
from dynamo_diff.store import Store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/captures"


def imported(store, case, manifest=True):
    path = FIXTURES / case
    return store.import_trace(path / "report", manifest_path=path / "manifest.json" if manifest else None)


def test_real_body_edit_matches_despite_changed_frame_ids(tmp_path):
    store = Store(tmp_path)
    baseline, candidate = imported(store, "edit_before"), imported(store, "edit_after")
    report = compare_runs(store, baseline.id, candidate.id)
    assert report.workload_comparability == "manifest_consistent"
    row = next(row for row in report.functions if row.baseline and row.baseline[0].source.function == "compute")
    assert row.match_status == "matched"
    assert row.match_method == "source_diff_function_boundary"
    assert row.baseline[0].id != row.candidate[0].id
    assert row.baseline[0].source.function_sha256 != row.candidate[0].source.function_sha256
    assert row.baseline_counts.completed == 3
    assert row.candidate_counts.completed == 1
    assert row.delta["confirmed_successful_recompilations"] == -2
    helper = next(row for row in report.functions if row.candidate[0].source.function == "helper")
    assert helper.match_status == "unmatched"
    assert report.candidate_counts.completed == 2  # New helper remains in capture-wide totals.
    assert report.performance_conclusion == "not_measured"


def test_changed_workload_is_confounded(tmp_path):
    store = Store(tmp_path)
    baseline, candidate = imported(store, "stable"), imported(store, "shape")
    report = compare_runs(store, baseline.id, candidate.id)
    assert report.workload_comparability == "confounded"
    assert any(d["field"] == "workload.calls" for d in report.comparability_differences)


def test_missing_snapshots_do_not_create_a_confident_match(tmp_path):
    store = Store(tmp_path)
    baseline, candidate = imported(store, "stable", False), imported(store, "shape", False)
    report = compare_runs(store, baseline.id, candidate.id)
    assert report.workload_comparability == "unknown"
    assert report.functions[0].match_status == "ambiguous"


def test_explicit_source_map_and_identity_validation(tmp_path):
    store = Store(tmp_path)
    baseline, candidate = imported(store, "stable", False), imported(store, "shape", False)
    mapping = {"rank-unspecified:0": "rank-unspecified:0"}
    report = compare_runs(store, baseline.id, candidate.id, source_map=mapping)
    assert report.functions[0].match_method == "explicit_source_mapping"
    with pytest.raises(DynamoDiffError) as error:
        compare_runs(store, baseline.id, candidate.id, source_map={"missing": "rank-unspecified:0"})
    assert error.value.code == "invalid_source_map"


@pytest.mark.parametrize("malformation", ["conflicting_duplicate", "non_object", "deeply_nested"])
def test_cli_rejects_ambiguous_or_malformed_source_mapping(tmp_path, malformation):
    store = Store(tmp_path / "store")
    baseline, candidate = imported(store, "edit_before"), imported(store, "edit_after")
    report = compare_runs(store, baseline.id, candidate.id)
    matched = next(row for row in report.functions if row.match_status == "matched")
    helper = next(row for row in report.functions if row.match_status == "unmatched")
    source_id = json.dumps(matched.baseline[0].id)
    correct_id = json.dumps(matched.candidate[0].id)
    wrong_id = json.dumps(helper.candidate[0].id)
    # Conflicting duplicate keys must not silently map compute to helper.
    text = {
        "conflicting_duplicate": f'{{{source_id}:{correct_id},{source_id}:{wrong_id}}}',
        "non_object": "[]",
        "deeply_nested": "[" * 1000 + "0" + "]" * 1000,
    }[malformation]
    mapping = tmp_path / "mapping.json"
    mapping.write_text(text)
    run = subprocess.run(
        [sys.executable, "-m", "dynamo_diff.cli", "--store", str(store.root), "compare",
         baseline.id, candidate.id, "--source-map", str(mapping), "--format", "json"],
        capture_output=True, text=True, timeout=30,
    )
    assert run.returncode == 2, run.stdout
    assert not run.stdout
    assert json.loads(run.stderr)["error"]["code"] == "invalid_source_map"


def test_fallback_and_failure_never_get_a_speed_verdict(tmp_path):
    store = Store(tmp_path)
    baseline, candidate = imported(store, "multiple_guards"), imported(store, "limit")
    report = compare_runs(store, baseline.id, candidate.id)
    assert report.candidate_counts.completed < report.baseline_counts.completed
    assert report.candidate_counts.compiler_limit_events == 1
    assert report.performance_conclusion == "not_measured"
    assert any(notice.code == "non_successful_compiler_behavior" for notice in report.notices)


def test_cli_matches_library_and_returns_structured_errors(tmp_path):
    store = Store(tmp_path)
    baseline, candidate = imported(store, "edit_before"), imported(store, "edit_after")
    command = [sys.executable, "-m", "dynamo_diff.cli", "--store", str(tmp_path)]
    run = subprocess.run([*command, "compare", baseline.id, candidate.id, "--format", "json"], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout) == compare_runs(store, baseline.id, candidate.id).model_dump()
    error = subprocess.run([*command, "analyze", "../escape"], capture_output=True, text=True, timeout=30)
    assert error.returncode == 2
    assert json.loads(error.stderr)["error"]["code"] == "invalid_capture_id"


@pytest.mark.parametrize("output_format", ["text", "markdown"])
def test_cli_displays_guard_categories_on_both_sides_of_an_edit(tmp_path, output_format):
    store = Store(tmp_path)
    before, after = imported(store, "edit_before"), imported(store, "edit_after")
    command = [sys.executable, "-m", "dynamo_diff.cli", "--store", str(tmp_path), "compare"]
    for baseline, candidate, categories in (
        (before, after, "python_scalar → none recorded"),
        (after, before, "none recorded → python_scalar"),
    ):
        run = subprocess.run(
            [*command, baseline.id, candidate.id, "--format", output_format],
            capture_output=True, text=True, timeout=30,
        )
        assert run.returncode == 0, run.stderr
        # The original baseline has explicit scalar guards. Removing them must
        # not make the entire comparison say that no guards were recorded.
        assert categories in run.stdout
        assert "function absent" in run.stdout  # The added/removed helper has no counterpart.
        assert "Application performance: not measured." in run.stdout


@pytest.mark.parametrize("value", [None, "", "  "])
def test_unknown_declarations_do_not_make_workload_consistent(tmp_path, value):
    from dynamo_diff.compare import comparability
    store = Store(tmp_path)
    before, after = imported(store, "edit_before"), imported(store, "edit_after")
    before.manifest["workload"]["backend"] = value
    after.manifest["workload"]["backend"] = value
    status, differences = comparability(before, after)
    assert status == "unknown"
    assert {"field": "workload.backend", "status": "missing"} in differences


def test_public_comparison_schema_is_available_from_cli():
    from dynamo_diff.compare import Comparison
    run = subprocess.run([sys.executable, "-m", "dynamo_diff.cli", "schema", "--kind", "comparison"], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout) == Comparison.model_json_schema()


def test_explicit_automatic_dynamic_policy_is_a_known_declaration(tmp_path):
    from dynamo_diff.compare import comparability
    capture = imported(Store(tmp_path), "dynamic")
    assert capture.manifest["workload"]["dynamic"] is None
    assert comparability(capture, capture)[0] == "manifest_consistent"


def test_duplicate_source_functions_cannot_be_confidently_matched(tmp_path):
    import hashlib
    import shutil
    root = tmp_path / "duplicate-source-identity"
    shutil.copytree(FIXTURES / "stable", root)
    metadata = root / "report/raw.jsonl"
    records = [json.loads(line) for line in metadata.read_text().splitlines()]
    # A synthetic robustness input: two distinct frames expose the same source identity.
    # Neither event sequence nor its count is claimed to be a new compiler recording.
    copies = [{**record, "frame_id": record["frame_id"] + 100} for record in records if "frame_id" in record]
    metadata.write_text("\n".join(json.dumps(record) for record in [*records, *copies]) + "\n")
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["capture"].pop("report_sha256")  # The synthetic input has no valid completion declaration.
    (root / "manifest.json").write_text(json.dumps(manifest))
    store = Store(tmp_path / "store")
    before = store.import_trace(root / "report", manifest_path=root / "manifest.json")
    report = compare_runs(store, before.id, before.id)
    assert len(report.functions) == 1
    row = report.functions[0]
    assert row.match_status == "ambiguous"
    assert row.match_method == "non_unique_source_identity"
    assert len(row.baseline) == len(row.candidate) == 2
    assert report.baseline_counts.completed == row.baseline_counts.completed == 2
    assert report.performance_conclusion == "not_measured"


def test_changed_library_version_is_confounded_and_missing_is_unknown(tmp_path):
    from dynamo_diff.compare import comparability
    store = Store(tmp_path)
    before, after = imported(store, "edit_before"), imported(store, "edit_after")
    before.manifest["producer"]["transformers"] = "5.10.1"
    after.manifest["producer"]["transformers"] = "different-version"
    status, differences = comparability(before, after)
    assert status == "confounded"
    assert any(d["field"] == "producer.transformers" and d["status"] == "different" for d in differences)
    del after.manifest["producer"]["transformers"]
    assert comparability(before, after)[0] == "unknown"
