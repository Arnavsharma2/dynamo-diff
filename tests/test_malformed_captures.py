import json
from pathlib import Path
import shutil

import pytest

from dynamo_diff.adapters.tlparse import analyze_report
from dynamo_diff.errors import DynamoDiffError
from dynamo_diff.model import Limits

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/captures"


def copy_capture(tmp_path, name="stable"):
    target = tmp_path / "report with spaces"
    shutil.copytree(FIXTURES / name / "report", target)
    return target


def change_records(report, transform):
    path = report / "raw.jsonl"
    data = [json.loads(line) for line in path.read_text().splitlines()]
    path.write_text("\n".join(json.dumps(item) for item in transform(data)) + "\n")


def test_missing_terminal_leaves_outcome_unknown(tmp_path):
    report = copy_capture(tmp_path)
    change_records(report, lambda records: [r for r in records if "compilation_metrics" not in r])
    result = analyze_report(report)
    assert result.counts.completed == 0
    assert result.counts.unknown_outcomes == 1
    assert result.validity.workload_completion == "unknown"


def test_clean_truncation_does_not_prove_workload_completed(tmp_path):
    report = copy_capture(tmp_path, "multiple_guards")
    change_records(report, lambda records: records[:9])
    result = analyze_report(report)
    assert result.counts.completed == 1
    assert result.validity.workload_completion == "unknown"


def test_malformed_line_is_visible_and_preserves_usable_evidence(tmp_path):
    report = copy_capture(tmp_path)
    with (report / "raw.jsonl").open("a") as stream:
        stream.write('{"truncated":')
    result = analyze_report(report)
    assert result.counts.completed == 1
    assert result.validity.artifact_structure == "partial"
    assert any(n.code == "malformed_record" and n.evidence_ids for n in result.notices)


def test_missing_payload_preserves_terminal_reason_but_marks_partial(tmp_path):
    report = copy_capture(tmp_path, "scalar")
    next(report.rglob("recompile_reasons*.json")).unlink()
    result = analyze_report(report)
    assert result.counts.confirmed_successful_recompilations == 1
    assert result.validity.artifact_structure == "partial"
    assert any(n.code == "missing_payload" for n in result.notices)


@pytest.mark.parametrize("field,value,code", [("compiled_autograd_id", 0, "unsupported_scope"),
                                               ("attempt", -1, "invalid_attempt")])
def test_unsupported_or_invalid_identity(tmp_path, field, value, code):
    report = copy_capture(tmp_path)
    def transform(records):
        records[2][field] = value
        return records
    change_records(report, transform)
    if code == "unsupported_scope":
        with pytest.raises(DynamoDiffError, match="Compiled-autograd"):
            analyze_report(report)
    else:
        assert any(n.code == code for n in analyze_report(report).notices)


def test_mixed_ranks_are_rejected(tmp_path):
    report = copy_capture(tmp_path)
    def transform(records):
        records[2]["rank"] = 0
        records[-1]["rank"] = 1
        return records
    change_records(report, transform)
    with pytest.raises(DynamoDiffError) as error:
        analyze_report(report)
    assert error.value.code == "unsupported_scope"


def test_unknown_producer_version_is_rejected(tmp_path):
    report = copy_capture(tmp_path)
    def transform(records):
        records[-1]["compilation_metrics"]["pytorch_version"] = "99.0.0"
        return records
    change_records(report, transform)
    with pytest.raises(DynamoDiffError) as error:
        analyze_report(report)
    assert error.value.code == "unsupported_version"


@pytest.mark.parametrize("symlink", [False, True])
def test_payload_cannot_escape_report_root(tmp_path, symlink):
    report = copy_capture(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("should never become evidence")
    reference = "../outside.txt"
    if symlink:
        (report / "escape").symlink_to(outside)
        reference = "escape"
    def transform(records):
        records[1]["payload_filename"] = reference
        return records
    change_records(report, transform)
    with pytest.raises(DynamoDiffError) as error:
        analyze_report(report)
    assert error.value.code == "unsafe_path"


def test_metadata_resource_limit(tmp_path):
    report = copy_capture(tmp_path)
    with pytest.raises(DynamoDiffError) as error:
        analyze_report(report, limits=Limits(record_bytes=64))
    assert error.value.code == "resource_limit"


def test_duplicate_terminal_is_unresolved(tmp_path):
    report = copy_capture(tmp_path)
    change_records(report, lambda records: [*records, records[-1]])
    result = analyze_report(report)
    assert result.counts.completed == 0
    assert result.counts.unknown_outcomes == 1
    assert result.validity.artifact_structure == "partial"
