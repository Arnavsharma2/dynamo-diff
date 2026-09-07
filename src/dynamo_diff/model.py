"""Versioned public report contract. No compiler or editor dependency."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1"
ADAPTER_VERSION = "tlparse-0.4.3-torch-2.14-log3-v4"


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Limits(Model):
    input_bytes: int = Field(default=512 * 1024**2, gt=0)
    record_bytes: int = Field(default=2 * 1024**2, gt=0)
    payload_bytes: int = Field(default=16 * 1024**2, gt=0)
    source_analysis_bytes: int = Field(default=1024**2, gt=0)
    source_diff_line_pairs: int = Field(default=4_000_000, gt=0)
    records: int = Field(default=1_000_000, gt=0)
    events: int = Field(default=100_000, gt=0)
    response_chars: int = Field(default=12_000, ge=1000)


class Notice(Model):
    code: str
    message: str
    evidence_ids: list[str] = Field(default_factory=list)


class Evidence(Model):
    id: str
    artifact: str
    sha256: str
    byte_offset: int = 0
    byte_length: int
    record_line: int | None = None
    kind: str
    payload_index: int | None = None


class Source(Model):
    captured_path: str | None = None
    relative_path: str | None = None
    function: str | None = None
    qualified_name: str | None = None
    first_line: int | None = None
    snapshot: str | None = None
    snapshot_sha256: str | None = None
    function_sha256: str | None = None
    generated_resume: bool = False
    attribution: Literal["trace", "same_run_frame", "unknown"] = "unknown"


class GuardReason(Model):
    categories: list[str]
    summary: str
    evidence_id: str


class GraphBreak(Model):
    evidence_id: str
    site: str | None = None
    summary: str
    fallback_reported: bool = False


class Compilation(Model):
    id: str
    frame_id: int
    frame_compile_id: int
    rank: int | None = None
    attempts: list[int] = Field(default_factory=list)
    source: Source = Field(default_factory=Source)
    outcome: Literal["completed", "failed", "no_graph_observed", "unknown"] = "unknown"
    recompilation: Literal["confirmed", "not_reported", "unknown"] = "unknown"
    classification: Literal["confirmed_recompilation", "first_observed_compilation", "additional_frame_compilation", "unknown"] = "unknown"
    reasons: list[GuardReason] = Field(default_factory=list)
    graph_breaks: list[GraphBreak] = Field(default_factory=list)
    limit_reported: bool = False
    fallback_reported: bool = False
    error_type: str | None = None
    duration_us: int | None = None
    duration_metric: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    terminal_evidence_id: str | None = None
    notices: list[Notice] = Field(default_factory=list)


class Counts(Model):
    observed_compilation_identities: int = 0
    observed_attempts: int = 0
    completed: int = 0
    failed: int = 0
    no_graph_observed: int = 0
    unknown_outcomes: int = 0
    confirmed_recompilation_identities: int = 0
    confirmed_successful_recompilations: int = 0
    additional_frame_compilations: int = 0
    guard_reason_entries: int = 0
    graph_break_records: int = 0
    unique_graph_break_sites: int = 0
    compiler_limit_events: int = 0
    fallback_reports: int = 0


class CaptureValidity(Model):
    artifact_structure: Literal["valid", "partial"] = "valid"
    workload_completion: Literal["declared_completed", "declared_failed", "unknown"] = "unknown"
    provenance: Literal["hash_verified", "unverified", "absent"] = "absent"


class Capture(Model):
    schema_version: str = SCHEMA_VERSION
    adapter_version: str = ADAPTER_VERSION
    id: str
    producer: dict = Field(default_factory=dict)
    validity: CaptureValidity = Field(default_factory=CaptureValidity)
    counts: Counts = Field(default_factory=Counts)
    compilations: list[Compilation] = Field(default_factory=list)
    evidence: dict[str, Evidence] = Field(default_factory=dict)
    notices: list[Notice] = Field(default_factory=list)
    manifest: dict | None = None
    metadata_sha256: str
    records_read: int = 0
    unknown_record_types: list[str] = Field(default_factory=list)
    observed_configurations: dict[str, list[str]] = Field(default_factory=dict)
    performance_conclusion: Literal["not_measured"] = "not_measured"


def count_compilations(events: list[Compilation]) -> Counts:
    counts = Counts()
    sites: set[str] = set()
    for event in events:
        counts.observed_compilation_identities += 1
        counts.observed_attempts += len(event.attempts)
        if event.outcome == "unknown":
            counts.unknown_outcomes += 1
        else:
            setattr(counts, event.outcome, getattr(counts, event.outcome) + 1)
        if event.recompilation == "confirmed":
            counts.confirmed_recompilation_identities += 1
            counts.confirmed_successful_recompilations += event.outcome == "completed"
        counts.additional_frame_compilations += event.classification == "additional_frame_compilation"
        counts.guard_reason_entries += len(event.reasons)
        counts.graph_break_records += len(event.graph_breaks)
        counts.compiler_limit_events += event.limit_reported
        counts.fallback_reports += event.fallback_reported
        sites.update(item.site for item in event.graph_breaks if item.site is not None)
    counts.unique_graph_break_sites = len(sites)
    return counts
