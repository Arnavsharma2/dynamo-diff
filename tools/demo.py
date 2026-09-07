"""Reproduce the bundled before/after comparison without PyTorch or network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from dynamo_diff.compare import compare_runs
from dynamo_diff.render import render_comparison
from dynamo_diff.store import Store


def demonstrate(root: Path, store_path: Path, *, as_json: bool = False) -> None:
    store = Store(store_path)
    captures = []
    for name in ["edit_before", "edit_after"]:
        bundle = root / name
        captures.append(store.import_trace(bundle / "report", manifest_path=bundle / "manifest.json"))
    report = compare_runs(store, captures[0].id, captures[1].id)
    row = next(row for row in report.functions if row.baseline and row.baseline[0].source.function == "compute")
    checks = [report.workload_comparability == "manifest_consistent", row.match_status == "matched",
        row.match_method == "source_diff_function_boundary", row.baseline_counts.completed == 3,
        row.candidate_counts.completed == 1, row.baseline_counts.confirmed_successful_recompilations == 2,
        row.candidate_counts.confirmed_successful_recompilations == 0, report.candidate_counts.completed == 2,
        report.performance_conclusion == "not_measured"]
    if not all(checks):
        raise SystemExit("The demonstration did not match its independently specified expected counts and correspondence.")
    print(json.dumps(report.model_dump(), indent=2) if as_json else render_comparison(report, markdown=True), end="\n" if as_json else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, default=Path(__file__).resolve().parents[1] / "fixtures/captures")
    parser.add_argument("--store", type=Path, help="Optional persistent store; otherwise a temporary store is removed on exit")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.store:
        demonstrate(args.captures, args.store, as_json=args.json)
    else:
        with tempfile.TemporaryDirectory(prefix="dynamo-diff-demo-") as temporary:
            demonstrate(args.captures, Path(temporary), as_json=args.json)


if __name__ == "__main__":
    main()
