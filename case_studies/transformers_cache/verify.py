"""Inspect the retained real-project pair without importing PyTorch or Transformers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from dynamo_diff.compare import compare_runs
from dynamo_diff.store import Store

HERE = Path(__file__).resolve().parent


def evidence_text(store: Store, capture_id: str, evidence_id: str) -> str:
    pieces, offset = [], 0
    while True:
        page = store.get_evidence(capture_id, evidence_id, offset=offset)
        pieces.append(page["text"])
        if page["next_offset"] is None:
            return "".join(pieces)
        offset = page["next_offset"]


def verify(captures: Path, store: Store) -> dict:
    expected = json.loads((HERE / "expected.json").read_text())
    imported = []
    results = []
    checks = []
    for variant in ("baseline", "candidate"):
        bundle = captures / variant
        manifest = json.loads((bundle / "manifest.json").read_text())
        result_bytes = (bundle / "workload-result.json").read_bytes()
        assert hashlib.sha256(result_bytes).hexdigest() == manifest["capture"]["result_sha256"]
        result = json.loads(result_bytes)
        results.append(result)
        target = expected[variant]
        assert [c["backend_calls_after"] for c in result["calls"]] == target["backend_totals_after_requests"]
        assert len(result["backend_calls"]) == target["completed"]
        for call in result["calls"]:
            assert call["output_correct"] is True
            assert call["maximum_logit_error"] == 0.0
            assert call["output_tokens"] == result["oracle"]["output_tokens"]
            assert call["output_logits_sha256"] == result["oracle"]["output_logits_sha256"]
        # Count retained compiler terminals directly, independently of the adapter.
        # A graph alone would not pass these assertions.
        records = [json.loads(line) for line in (bundle / "report/raw.jsonl").read_text().splitlines()]
        terminals = [r for r in records if "compilation_metrics" in r]
        assert len(terminals) == target["completed"]
        assert {(r["frame_id"], r["frame_compile_id"]) for r in terminals} == {(0, i) for i in range(target["completed"])}
        for terminal in terminals:
            metrics = terminal["compilation_metrics"]
            assert metrics["has_guarded_code"] is True
            assert metrics["fail_type"] is None
            assert metrics["graph_op_count"] > 0
        recompiles = [r for r in records if r.get("artifact", {}).get("name") == "recompile_reasons"]
        assert len(recompiles) == target["confirmed_successful_recompilations"]
        capture = store.import_trace(bundle / "report", manifest_path=bundle / "manifest.json")
        imported.append(capture)
        assert capture.validity.artifact_structure == "valid"
        assert capture.validity.workload_completion == "declared_completed"
        for field in ("completed", "confirmed_successful_recompilations", "guard_reason_entries"):
            assert getattr(capture.counts, field) == target[field], (variant, field)
        for field, value in expected["unchanged"].items():
            assert getattr(capture.counts, field) == value, (variant, field)
        for event in capture.compilations:
            terminal = evidence_text(store, capture.id, event.terminal_evidence_id)
            assert json.loads(terminal)["compilation_metrics"]["has_guarded_code"] is True
        checks.append(f"{variant}: finalization, raw terminals, recompile artifacts, normalized events, backend totals and eager-output evidence")

    assert results[0]["parameter_hashes"] == results[1]["parameter_hashes"]
    for before, after in zip(results[0]["calls"], results[1]["calls"], strict=True):
        assert before["output_tokens"] == after["output_tokens"]
        assert before["output_logits_sha256"] == after["output_logits_sha256"]
    report = compare_runs(store, *[capture.id for capture in imported])
    assert report.workload_comparability == expected["workload_comparability"]
    assert report.performance_conclusion == expected["performance_conclusion"]
    assert len(report.functions) == 1
    row = report.functions[0]
    assert row.match_status == "matched" and row.match_method == "unique_function_structure"
    assert row.baseline[0].source.qualified_name == expected["source_function"]
    assert row.delta["confirmed_successful_recompilations"] == -1
    before_reasons = [r for e in imported[0].compilations for r in e.reasons]
    after_reasons = [r for e in imported[1].compilations for r in e.reasons]
    initialization = [r for r in before_reasons if "is_initialized == False" in r.summary]
    assert len(initialization) == 1 and initialization[0].categories == ["python_scalar"]
    assert not any("is_initialized" in r.summary for r in after_reasons)
    assert len(after_reasons) == 1 and after_reasons[0].categories == ["tensor_shape_stride"]
    evidence = store.get_evidence(imported[0].id, initialization[0].evidence_id)
    assert "transformers/cache_utils.py:352" in evidence["text"]
    checks.append("matched wrapper, one fewer completed recompile, cache-initialization reason removed, shape specialization retained, no speed verdict")
    return {"checks": checks, "comparison": report.model_dump(), "review_status": expected["review_status"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, default=HERE / "captures")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="dynamo-diff-case-") as temporary:
        result = verify(args.captures, Store(Path(temporary)))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "comparison"}, indent=2))


if __name__ == "__main__":
    main()
