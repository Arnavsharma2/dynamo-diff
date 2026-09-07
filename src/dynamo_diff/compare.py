"""Conservative source correspondence and descriptive compiler differences."""

from __future__ import annotations

from collections import defaultdict
import difflib
import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field

from .errors import DynamoDiffError
from .io import hash_file, read_text, within
from .model import ADAPTER_VERSION, SCHEMA_VERSION, Capture, CaptureValidity, Compilation, Counts, Model, Notice, Source, count_compilations
from .store import Store, canonical

COMPARISON_VERSION = "4"


class FunctionGroup(Model):
    id: str
    source: Source
    compilation_ids: list[str]
    counts: Counts
    guard_categories: list[str]
    evidence_ids: list[str]
    graph_break_sites: list[str] = Field(default_factory=list)


class FunctionComparison(Model):
    match_status: Literal["matched", "ambiguous", "unmatched"]
    match_method: str
    baseline: list[FunctionGroup]
    candidate: list[FunctionGroup]
    baseline_counts: Counts
    candidate_counts: Counts
    delta: dict[str, int]
    interpretation: str


class Comparison(Model):
    schema_version: str = SCHEMA_VERSION
    adapter_version: str = ADAPTER_VERSION
    comparison_version: str = COMPARISON_VERSION
    id: str
    baseline_id: str
    candidate_id: str
    capture_validity: dict[str, CaptureValidity]
    workload_comparability: Literal["manifest_consistent", "confounded", "unknown"]
    comparability_differences: list[dict] = Field(default_factory=list)
    baseline_counts: Counts
    candidate_counts: Counts
    functions: list[FunctionComparison]
    notices: list[Notice] = Field(default_factory=list)
    performance_conclusion: Literal["not_measured"] = "not_measured"


def groups(capture: Capture) -> dict[str, FunctionGroup]:
    events: dict[str, list[Compilation]] = defaultdict(list)
    for event in capture.compilations:
        events[f"rank-{event.rank if event.rank is not None else 'unspecified'}:{event.frame_id}"].append(event)
    result = {}
    for identifier, values in events.items():
        source = next((event.source for event in values if event.source.captured_path), values[0].source)
        result[identifier] = FunctionGroup(id=identifier, source=source,
            compilation_ids=[event.id for event in values], counts=count_compilations(values),
            guard_categories=sorted({category for event in values for reason in event.reasons for category in reason.categories}),
            evidence_ids=list(dict.fromkeys(reference for event in values for reference in event.evidence_ids)),
            graph_break_sites=sorted({item.site for event in values for item in event.graph_breaks if item.site}))
    return result


def _sum(values: list[FunctionGroup]) -> Counts:
    fields = Counts.model_fields
    data = {key: sum(getattr(value.counts, key) for value in values) for key in fields}
    data["unique_graph_break_sites"] = len({site for value in values for site in value.graph_break_sites})
    return Counts(**data)


def _source_key(group: FunctionGroup) -> tuple:
    source = group.source
    return (source.relative_path or source.captured_path, source.qualified_name or source.function,
            source.generated_resume)


def _snapshot(store: Store, capture: Capture, source: Source) -> list[str] | None:
    if not source.snapshot or not source.snapshot_sha256:
        return None
    path = within(store.capture_dir(capture.id) / "context", source.snapshot)
    if hash_file(path, store.limits.payload_bytes) != source.snapshot_sha256:
        raise DynamoDiffError("corrupt_store", "Source snapshot changed after import")
    if path.stat().st_size > store.limits.source_analysis_bytes:
        return None
    return read_text(path, store.limits.payload_bytes).splitlines()


def _match_method(store: Store, baseline: Capture, candidate: Capture, left: Source, right: Source) -> str | None:
    if left.generated_resume or right.generated_resume:
        # Resume names encode line positions and may split/merge after graph breaks.
        if left.snapshot_sha256 and left.snapshot_sha256 == right.snapshot_sha256 and left.function == right.function and left.first_line == right.first_line:
            return "same_snapshot_resume_region"
        return None
    if left.qualified_name and right.qualified_name and left.function_sha256 and left.function_sha256 == right.function_sha256:
        return "unique_function_structure"
    before = _snapshot(store, baseline, left)
    after = _snapshot(store, candidate, right)
    if before is not None and after is not None and left.qualified_name == right.qualified_name and left.qualified_name and left.first_line and right.first_line:
        if len(before) * len(after) > store.limits.source_diff_line_pairs:
            return None
        old, new = left.first_line - 1, right.first_line - 1
        matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
        for block in matcher.get_matching_blocks():
            if block.a <= old < block.a + block.size and block.b + old - block.a == new:
                return "source_diff_function_boundary"
    return None


def comparability(baseline: Capture, candidate: Capture) -> tuple[str, list[dict]]:
    before, after = baseline.manifest or {}, candidate.manifest or {}
    differences = []
    missing = False
    def absent(values: dict, key: str) -> bool:
        # torch.compile(dynamic=None) is an explicit automatic-shape policy.
        return key not in values or (values[key] is None and key != "dynamic") or (isinstance(values[key], str) and not values[key].strip())
    required = ["calls", "seed", "backend", "dynamic", "device", "warmup_calls", "cache_policy", "environment"]
    for key in required:
        left, right = before.get("workload", {}), after.get("workload", {})
        if absent(left, key) or absent(right, key):
            missing = True
            differences.append({"field": f"workload.{key}", "status": "missing"})
        elif canonical(left[key]) != canonical(right[key]):
            differences.append({"field": f"workload.{key}", "status": "different", "baseline": left[key], "candidate": right[key]})
    for key in ["torch", "torch_git", "python"]:
        left, right = before.get("producer", {}), after.get("producer", {})
        if absent(left, key) or absent(right, key):
            missing = True
            differences.append({"field": f"producer.{key}", "status": "missing"})
        elif left[key] != right[key]:
            differences.append({"field": f"producer.{key}", "status": "different", "baseline": left[key], "candidate": right[key]})
    # Library/converter versions (for example Transformers) can change behavior
    # even when Python and PyTorch are identical. Preserve every declared producer field.
    left, right = before.get("producer", {}), after.get("producer", {})
    for key in sorted((set(left) | set(right)) - {"torch", "torch_git", "python"}):
        if absent(left, key) or absent(right, key):
            missing = True
            differences.append({"field": f"producer.{key}", "status": "missing"})
        elif canonical(left[key]) != canonical(right[key]):
            differences.append({"field": f"producer.{key}", "status": "different", "baseline": left[key], "candidate": right[key]})
    # Preserve unanticipated workload metadata instead of silently ignoring changes.
    left, right = before.get("workload", {}), after.get("workload", {})
    for key in sorted((set(left) | set(right)) - set(required)):
        if left.get(key) != right.get(key):
            differences.append({"field": f"workload.{key}", "status": "different", "baseline": left.get(key), "candidate": right.get(key)})
    for key in sorted(set(baseline.observed_configurations) | set(candidate.observed_configurations)):
        left_hashes = baseline.observed_configurations.get(key)
        right_hashes = candidate.observed_configurations.get(key)
        if left_hashes != right_hashes:
            differences.append({"field": f"observed.{key}", "status": "different",
                                "baseline": left_hashes, "candidate": right_hashes})
    if any(value["status"] == "different" for value in differences):
        return "confounded", differences
    return ("unknown" if missing else "manifest_consistent"), differences


def compare_runs(store: Store, baseline_id: str, candidate_id: str, *, source_map: dict[str, str] | None = None) -> Comparison:
    baseline, candidate = store.load(baseline_id), store.load(candidate_id)
    left, right = groups(baseline), groups(candidate)
    source_map = {} if source_map is None else source_map
    if not isinstance(source_map, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in source_map.items()):
        raise DynamoDiffError("invalid_source_map", "Source map must map baseline function IDs to candidate function IDs")
    if any(key not in left or value not in right for key, value in source_map.items()) or len(set(source_map.values())) != len(source_map):
        raise DynamoDiffError("invalid_source_map", "Source mappings must exist and be one-to-one")
    rows = []

    def add(before: list[FunctionGroup], after: list[FunctionGroup], status: str, method: str) -> None:
        bc, cc = _sum(before), _sum(after)
        delta = {key: getattr(cc, key) - getattr(bc, key) for key in Counts.model_fields}
        interpretation = "Observed compiler-event difference; application performance was not measured."
        if status != "matched":
            interpretation = "Source correspondence is unresolved; these counts do not establish a function-level regression."
        rows.append(FunctionComparison(match_status=status, match_method=method, baseline=before, candidate=after,
                    baseline_counts=bc, candidate_counts=cc, delta=delta, interpretation=interpretation))

    for key, value in sorted(source_map.items()):
        add([left.pop(key)], [right.pop(value)], "matched", "explicit_source_mapping")
    lb: dict[tuple, list[FunctionGroup]] = defaultdict(list)
    rb: dict[tuple, list[FunctionGroup]] = defaultdict(list)
    for group in left.values():
        lb[_source_key(group)].append(group)
    for group in right.values():
        rb[_source_key(group)].append(group)
    for key in sorted(set(lb) | set(rb), key=repr):
        before, after = lb.get(key, []), rb.get(key, [])
        if not before or not after:
            add(before, after, "unmatched", "no_source_counterpart")
        elif len(before) != 1 or len(after) != 1 or key[0] is None or key[1] is None:
            add(before, after, "ambiguous", "non_unique_source_identity")
        else:
            method = _match_method(store, baseline, candidate, before[0].source, after[0].source)
            add(before, after, "matched" if method else "ambiguous", method or "unverified_source_correspondence")
    status, differences = comparability(baseline, candidate)
    notices = []
    if status != "manifest_consistent":
        notices.append(Notice(code="workload_not_comparable", message="Workload metadata differs or is incomplete; event deltas cannot be attributed solely to a source edit."))
    if any(c.validity.workload_completion != "declared_completed" or c.validity.artifact_structure != "valid" for c in [baseline, candidate]):
        notices.append(Notice(code="capture_incomplete_or_unverified", message="At least one capture is partial or lacks verified finalization metadata."))
    if any(c.counts.failed or c.counts.no_graph_observed or c.counts.unknown_outcomes or c.counts.compiler_limit_events or c.counts.fallback_reports for c in [baseline, candidate]):
        notices.append(Notice(code="non_successful_compiler_behavior", message="Failure, skipped/no-graph, incomplete, limit, or fallback behavior requires inspection; fewer compilations do not establish a fix."))
    fingerprint = {"baseline": baseline_id, "candidate": candidate_id, "adapter": ADAPTER_VERSION,
                   "schema": SCHEMA_VERSION, "comparison_version": COMPARISON_VERSION, "source_map": source_map,
                   "options": {"source_analysis_bytes": store.limits.source_analysis_bytes,
                               "source_diff_line_pairs": store.limits.source_diff_line_pairs}}
    return Comparison(id=hashlib.sha256(canonical(fingerprint)).hexdigest(), baseline_id=baseline_id, candidate_id=candidate_id,
        capture_validity={"baseline": baseline.validity, "candidate": candidate.validity}, workload_comparability=status,
        comparability_differences=differences, baseline_counts=baseline.counts, candidate_counts=candidate.counts,
        functions=rows, notices=notices)
