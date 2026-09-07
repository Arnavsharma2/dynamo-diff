"""Human-readable views over the same report objects used by agents."""

from __future__ import annotations

import re

from .compare import Comparison
from .model import Capture


def clean(text: str) -> str:
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", lambda match: repr(match.group())[1:-1], text)


def capture_summary(capture: Capture) -> dict:
    return {"schema_version": capture.schema_version, "adapter_version": capture.adapter_version,
            "capture_id": capture.id, "producer": capture.producer, "capture_validity": capture.validity.model_dump(),
            "counts": capture.counts.model_dump(), "notices": [item.model_dump() for item in capture.notices],
            "unknown_record_types": capture.unknown_record_types, "performance_conclusion": capture.performance_conclusion}


def render_capture(capture: Capture, *, markdown: bool = False) -> str:
    title = "# Dynamo capture" if markdown else "Dynamo capture"
    lines = [title, "", f"Capture: {capture.id}", f"Artifacts: {capture.validity.artifact_structure}; workload completion: {capture.validity.workload_completion}",
             f"Completed compilations: {capture.counts.completed}; confirmed successful recompilations: {capture.counts.confirmed_successful_recompilations}",
             f"Failed: {capture.counts.failed}; no graph observed: {capture.counts.no_graph_observed}; unknown outcomes: {capture.counts.unknown_outcomes}", ""]
    for event in capture.compilations:
        source = event.source
        lines.append(f"{event.id}  {source.relative_path or source.captured_path or '?'}:{source.first_line or '?'}  {source.qualified_name or source.function or '?'}")
        lines.append(f"  {event.outcome}; {event.classification}; attempts={event.attempts}")
        for reason in event.reasons:
            lines.append(f"  [{', '.join(reason.categories)}] {reason.summary} (evidence: {reason.evidence_id})")
        if event.limit_reported:
            lines.append("  Compiler limit reported. Inspect failure evidence.")
    for notice in capture.notices:
        lines.append(f"Notice [{notice.code}]: {notice.message}")
    lines.extend(["", "Application performance: not measured."])
    return clean("\n".join(lines)) + "\n"


def render_comparison(comparison: Comparison, *, markdown: bool = False) -> str:
    lines = ["# Dynamo comparison" if markdown else "Dynamo comparison", "", f"Baseline: {comparison.baseline_id}",
             f"Candidate: {comparison.candidate_id}", f"Workload comparability: {comparison.workload_comparability}", ""]
    if markdown:
        lines.extend(["| Function | Match | Completed before → after | Confirmed recompiles before → after | Guard categories before → after |",
                      "|---|---|---:|---:|---|"])
    for row in comparison.functions:
        group = (row.candidate or row.baseline)[0]
        source = group.source
        name = f"{source.relative_path or source.captured_path or '?'}:{source.qualified_name or source.function or '?'}"
        guards = " → ".join(
            ", ".join(sorted({category for item in groups for category in item.guard_categories}))
            or ("none recorded" if groups else "function absent")
            for groups in (row.baseline, row.candidate)
        )
        completed = f"{row.baseline_counts.completed} → {row.candidate_counts.completed}"
        recompiles = f"{row.baseline_counts.confirmed_successful_recompilations} → {row.candidate_counts.confirmed_successful_recompilations}"
        if markdown:
            escaped_name = name.replace("|", "\\|")
            lines.append(f"| {escaped_name} | {row.match_status} | {completed} | {recompiles} | {guards} |")
        else:
            lines.append(f"{name}: {row.match_status} ({row.match_method})")
            lines.append(f"  Completed: {completed}; confirmed recompiles: {recompiles}; guards before → after: {guards}")
    lines.append("")
    for difference in comparison.comparability_differences:
        lines.append(f"Workload metadata: {difference['field']} is {difference['status']}.")
    for notice in comparison.notices:
        lines.append(f"Notice [{notice.code}]: {notice.message}")
    lines.append("Application performance: not measured. Counts describe captured compiler behavior.")
    return clean("\n".join(lines)) + "\n"
