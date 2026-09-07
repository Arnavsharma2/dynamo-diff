from pathlib import Path
import json

import pytest

from dynamo_diff.adapters.tlparse import analyze_report

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "fixtures/expected.json").read_text())["cases"]


@pytest.mark.parametrize("case,expected", CASES.items())
def test_real_compiler_event_semantics(case, expected):
    root = ROOT / "fixtures/captures" / case
    result = analyze_report(root / "report", manifest=json.loads((root / "manifest.json").read_text()), manifest_root=root)
    actual = result.counts.model_dump()
    assert {key: actual[key] for key in expected} == expected
    assert result.validity.artifact_structure == "valid"
    assert result.validity.workload_completion == "unknown"  # Parseability alone proves no workload completion.
    for event in result.compilations:
        for reason in event.reasons:
            assert reason.evidence_id in result.evidence
            assert "User stack trace" not in reason.summary
            assert "return x.sin()" not in reason.summary
        if event.outcome == "completed":
            assert event.terminal_evidence_id in result.evidence


@pytest.mark.parametrize("case,category", [("shape", "tensor_shape_stride"), ("scalar", "python_scalar"),
                                           ("grad", "grad_mode"), ("identity", "type_identity_dispatch")])
def test_real_guard_categories(case, category):
    capture = analyze_report(ROOT / "fixtures/captures" / case / "report")
    reasons = [reason for event in capture.compilations for reason in event.reasons]
    assert reasons
    assert all(category in reason.categories for reason in reasons)


def test_reuse_and_dynamic_generalization_have_independent_oracles():
    expected = {"stable": [1, 1, 1], "shape": [1, 2, 2], "scalar": [1, 2, 2],
                "dynamic": [1, 2, 2], "multiple_guards": [1, 2, 3]}
    for case, calls in expected.items():
        result = json.loads((ROOT / "fixtures/captures" / case / "workload-result.json").read_text())
        assert [call["backend_calls_so_far"] for call in result["calls"]] == calls
        assert all(call["output_correct"] for call in result["calls"])


def test_rejected_variants_are_not_counted_as_recompilations():
    capture = analyze_report(ROOT / "fixtures/captures/multiple_guards/report")
    assert len(capture.compilations[-1].reasons) == 2
    assert capture.counts.confirmed_successful_recompilations == 2
    assert capture.counts.guard_reason_entries == 3


def test_identity_partition_is_distinct_from_an_identity_guard_recompile():
    root = ROOT / "fixtures/captures"
    ordinary = analyze_report(root / "identity/report")
    partitioned = analyze_report(root / "identity_partitioned/report")
    assert ordinary.counts.completed == partitioned.counts.completed == 3
    assert ordinary.counts.confirmed_successful_recompilations == 2
    assert partitioned.counts.confirmed_successful_recompilations == 0
