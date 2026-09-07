import hashlib
import json
from pathlib import Path
import shutil

import pytest

from dynamo_diff.adapters.tlparse import analyze_report
from dynamo_diff.compare import compare_runs
from dynamo_diff.errors import DynamoDiffError
from dynamo_diff.model import Limits
from dynamo_diff.store import Store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/captures"


@pytest.mark.parametrize("value", ["NaN", "Infinity", "1e999", '"\\ud800"', '{"x":1,"x":2}', '[' * 70 + '0' + ']' * 70])
def test_noncanonical_manifest_json_rejected_before_import(tmp_path, value):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"custom":' + value + '}')
    store = Store(tmp_path / "store")
    with pytest.raises(DynamoDiffError) as error:
        store.import_trace(FIXTURES / "stable/report", manifest_path=manifest)
    assert error.value.code == "malformed_manifest"
    assert not store.root.exists()


@pytest.mark.parametrize("manifest", [
    {"source": {"files": [None]}},
    {"source": {"files": [{"snapshot": []}]}},
    {"capture": {"raw_traces": ["bad"]}},
    {"producer": {"torch": ["2.14.0"]}},
    {"capture": {"workload_completed": 1}},
    {"capture": {"workload_completed": True, "process_exit_code": False}},
    {"capture": {"converter_exit_code": False}},
])
def test_nested_manifest_types_cannot_crash_or_forge_completion(tmp_path, manifest):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(DynamoDiffError) as error:
        Store(tmp_path / "store").import_trace(FIXTURES / "stable/report", manifest_path=path)
    assert error.value.code == "malformed_manifest"


@pytest.mark.parametrize("line", ['{"artifact":{"name":[]}}', '{"artifact":{"name":{}}}', '{"extra":NaN}', '{"x":1,"x":2}'])
def test_malformed_record_retained_as_partial_evidence(tmp_path, line):
    report = tmp_path / "report"
    shutil.copytree(FIXTURES / "stable/report", report)
    with (report / "raw.jsonl").open("a") as stream:
        stream.write(line + "\n")
    capture = Store(tmp_path / "store").import_trace(report)
    assert capture.validity.artifact_structure == "partial"
    assert capture.counts.completed == 1
    assert any(n.code == "malformed_record" and n.evidence_ids for n in capture.notices)


def test_manifest_cannot_overwrite_imported_source_at_reserved_path(tmp_path):
    root = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "stable", root)
    manifest = json.loads((root / "manifest.json").read_text())
    entry = manifest["source"]["files"][0]
    data = (root / entry["snapshot"]).read_bytes()
    (root / "manifest.json").write_bytes(data)
    entry["snapshot"] = "./manifest.json"
    entry["sha256"] = hashlib.sha256(data).hexdigest()
    (root / "declaration.json").write_text(json.dumps(manifest))
    with pytest.raises(DynamoDiffError) as error:
        Store(tmp_path / "store").import_trace(root / "report", manifest_path=root / "declaration.json")
    assert error.value.code == "unsafe_path"


def test_aggregate_limit_counts_irrelevant_payloads(tmp_path):
    root = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "stable", root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    # An unrelated exported artifact is still copied, so it must count toward the budget.
    (root / "report/padding.txt").write_bytes(b"a" * 200_000)
    with (root / "report/raw.jsonl").open("a") as stream:
        stream.write(json.dumps({"artifact": {"name": "uninterpreted"}, "payload_filename": "padding.txt"}) + "\n")
    manifest["capture"].pop("report_sha256")
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(DynamoDiffError) as error:
        Store(tmp_path / "store", limits=Limits(input_bytes=100_000)).import_trace(root / "report", manifest_path=manifest_path)
    assert error.value.code == "resource_limit"


def test_aggregate_limit_counts_untraced_source_snapshots(tmp_path):
    root = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "stable", root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    source = root / "sources/untraced.py"
    source.write_bytes(b"# untraced source snapshot\n" * 8_000)
    manifest["source"]["files"].append({"captured_path": "/untraced.py", "relative_path": "untraced.py",
        "snapshot": "sources/untraced.py", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(DynamoDiffError) as error:
        Store(tmp_path / "store", limits=Limits(input_bytes=100_000)).import_trace(root / "report", manifest_path=manifest_path)
    assert error.value.code == "resource_limit"


@pytest.mark.parametrize("graph", [None, False, []])
def test_malformed_graph_output_cannot_establish_success(tmp_path, graph):
    report = tmp_path / "report"
    shutil.copytree(FIXTURES / "stable/report", report)
    metadata = report / "raw.jsonl"
    records = [json.loads(line) for line in metadata.read_text().splitlines()]
    for record in records:
        if "dynamo_output_graph" in record:
            record["dynamo_output_graph"] = graph
    metadata.write_text("\n".join(json.dumps(record) for record in records) + "\n")
    capture = analyze_report(report)
    assert capture.counts.completed == 0
    assert capture.counts.unknown_outcomes == 1
    assert capture.validity.artifact_structure == "partial"


def test_named_pipe_payload_cannot_block_import(tmp_path):
    import os
    if not hasattr(os, "mkfifo"):
        pytest.skip("Named pipes are not available on this platform")
    report = tmp_path / "report"
    shutil.copytree(FIXTURES / "stable/report", report)
    os.mkfifo(report / "pipe")
    with (report / "raw.jsonl").open("a") as stream:
        stream.write(json.dumps({"artifact": {"name": "torch_version"}, "payload_filename": "pipe"}) + "\n")
    capture = Store(tmp_path / "store").import_trace(report)
    assert capture.validity.artifact_structure == "partial"
    assert any(n.code == "missing_payload" for n in capture.notices)


def test_resource_limits_cover_records_events_payloads_and_sources(tmp_path):
    for limits, case in [(Limits(records=2), "stable"), (Limits(events=1), "shape"), (Limits(payload_bytes=32), "stable")]:
        with pytest.raises(DynamoDiffError) as error:
            analyze_report(FIXTURES / case / "report", limits=limits)
        assert error.value.code == "resource_limit"
    store = Store(tmp_path / "store", limits=Limits(source_analysis_bytes=1))
    capture = store.import_trace(FIXTURES / "edit_before/report", manifest_path=FIXTURES / "edit_before/manifest.json")
    assert capture.compilations[0].source.snapshot_sha256
    assert capture.compilations[0].source.function_sha256 is None
    assert compare_runs(store, capture.id, capture.id).functions[0].match_status == "ambiguous"
    assert store.get_source(capture.id, "rank-unspecified:0")["text"]


def test_normalization_and_comparison_options_cannot_reuse_wrong_cached_identity(tmp_path):
    normal = Store(tmp_path / "store")
    limited = Store(tmp_path / "store", limits=Limits(source_analysis_bytes=1))
    path = FIXTURES / "edit_before"
    before = normal.import_trace(path / "report", manifest_path=path / "manifest.json")
    restricted = limited.import_trace(path / "report", manifest_path=path / "manifest.json")
    assert before.id != restricted.id
    after = normal.import_trace(FIXTURES / "edit_after/report", manifest_path=FIXTURES / "edit_after/manifest.json")
    ordinary = compare_runs(normal, before.id, after.id)
    bounded_store = Store(normal.root, limits=Limits(source_diff_line_pairs=1))
    bounded = compare_runs(bounded_store, before.id, after.id)
    assert ordinary.id != bounded.id
    assert any(row.match_method == "source_diff_function_boundary" for row in ordinary.functions)
    assert any(row.match_status == "ambiguous" for row in bounded.functions)


def test_adapter_and_schema_versions_invalidate_capture_keys(tmp_path, monkeypatch):
    import dynamo_diff.store as module
    store = Store(tmp_path)
    first = store.import_trace(FIXTURES / "stable/report")
    for name in ("ADAPTER_VERSION", "SCHEMA_VERSION"):
        with monkeypatch.context() as patch:
            patch.setattr(module, name, "future-test-version")
            with pytest.raises(DynamoDiffError) as error:
                store.load(first.id)
            assert error.value.code == "unsupported_cache"
            assert store.import_trace(FIXTURES / "stable/report").id != first.id
