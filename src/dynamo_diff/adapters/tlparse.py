"""tlparse 0.4.3 raw.jsonl export with PyTorch 2.14/log-format 3.

The format is implementation-defined. See docs/SEMANTICS.md for the evidence
behind these rules and the distinction between processing and compilation.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re

from ..errors import DynamoDiffError
from ..io import hash_file, json_value, read_text, records, within
from ..manifest import validate_manifest
from ..model import Capture, Compilation, Evidence, GraphBreak, GuardReason, Limits, Notice, Source, count_compilations

COMMON = {"attempt", "frame_id", "frame_compile_id", "compiled_autograd_id", "rank", "pid", "process_id",
          "thread", "timestamp", "pathname", "lineno", "has_payload", "payload_filename"}
KNOWN = {"string_table", "artifact", "dynamo_start", "dynamo_output_graph", "compilation_metrics",
         "dynamo_cpp_guards_str", "dynamo_guards", "describe_storage", "describe_tensor", "describe_source",
         "create_symbol", "guard_added", "symbolic_shape_specialization", "expression_created"}
RESUME = re.compile(r"torch_dynamo_resume_in_(.+)_at_(\d+)")


def guard_summary(raw: str) -> str:
    """Do not include source snippets/stack traces in a default diagnostic."""
    return raw.splitlines()[0].split("#", 1)[0].strip()[:1000] if raw else "Unspecified guard failure"


def categories(summary: str) -> list[str]:
    text = summary.lower()
    found = []
    if any(term in text for term in ["size mismatch", ".size(", "shape", "stride mismatch", ".stride(", "storage_offset"]):
        found.append("tensor_shape_stride")
    if any(term in text for term in ["dtype mismatch", "dtype=", "device mismatch", "device index", "device type"]):
        found.append("dtype_device")
    if any(term in text for term in ["requires_grad", "grad_mode", "grad mode", "is_grad_enabled", "training ==", "inference_mode"]):
        found.append("grad_mode")
    if any(term in text for term in ["check_obj_id", "check_type_id", "type mismatch", "dispatchkey", "dispatch key", "dispatch-key", "id_match"]):
        found.append("type_identity_dispatch")
    if not found and re.search(r"(?:==|!=)\s*(?:-?\d+(?:\.\d+)?|true|false|none|'[^']*'|\"[^\"]*\")(?:\s|$)", text):
        found.append("python_scalar")
    return found or ["unknown"]


def reason_strings(text: str) -> list[str]:
    """0.4.3 renders strings without JSON quotes; lists remain JSON arrays."""
    try:
        value = json_value(text)
    except (ValueError, RecursionError, UnicodeError):
        if text.lstrip().startswith(("[", "{", '"')):
            raise DynamoDiffError("malformed_payload", "Malformed structured recompile-reasons payload")
        return [text] if text.strip() else []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise DynamoDiffError("malformed_payload", "Expected a reason string or list of strings")


def _source_from_stack(stack: object, strings: list[str]) -> Source:
    if isinstance(stack, list) and stack and isinstance(stack[-1], dict):
        frame = stack[-1]
        filename = frame.get("filename")
        if isinstance(filename, int) and not isinstance(filename, bool) and 0 <= filename < len(strings):
            filename = strings[filename]
        if not isinstance(filename, str):
            filename = None
        return Source(captured_path=filename, function=frame.get("name") if isinstance(frame.get("name"), str) else None,
                      first_line=frame.get("line") if type(frame.get("line")) is int else None, attribution="trace")
    return Source()


def _enrich_source(source: Source, manifest: dict | None, manifest_root: Path | None, limits: Limits) -> None:
    source.generated_resume = bool(source.function and RESUME.fullmatch(source.function))
    if not manifest or not manifest_root or not source.captured_path:
        return
    entries = manifest.get("source", {}).get("files", [])
    if not isinstance(entries, list):
        raise DynamoDiffError("malformed_manifest", "source.files must be a list")
    matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("captured_path") == source.captured_path]
    if len(matches) != 1:
        return
    entry = matches[0]
    relative = entry.get("relative_path")
    snapshot = entry.get("snapshot")
    if not isinstance(relative, str) or not isinstance(snapshot, str):
        raise DynamoDiffError("malformed_manifest", "Source entries require relative_path and snapshot")
    within(manifest_root, relative)  # Validate lexical paths even if the working file is absent.
    path = within(manifest_root, snapshot)
    digest = hash_file(path, limits.payload_bytes)
    if digest != entry.get("sha256"):
        raise DynamoDiffError("inconsistent_metadata", f"Source snapshot hash does not match: {snapshot}")
    source.relative_path, source.snapshot, source.snapshot_sha256 = relative, snapshot, digest
    if source.generated_resume:
        return
    text = read_text(path, limits.payload_bytes)
    if len(text.encode("utf-8")) > limits.source_analysis_bytes:
        return  # Keep the verified snapshot, but do not build an unbounded source AST.
    try:
        tree = ast.parse(text)
    except (SyntaxError, RecursionError):
        return
    matches_ast = []

    pending = [(tree, ())]
    while pending:
        node, parents = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            parents = (*parents, node.name)
            first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == source.function and first <= (source.first_line or 0) <= node.lineno:
                matches_ast.append((node, ".".join(parents)))
        pending.extend((child, parents) for child in ast.iter_child_nodes(node))
    if len(matches_ast) == 1:
        node, source.qualified_name = matches_ast[0]
        # Hash code structure, not line numbers; this is identity evidence, never equivalence proof.
        try:
            source.function_sha256 = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
        except RecursionError:
            source.qualified_name = None


def analyze_report(report: Path, *, capture_id: str | None = None, manifest: dict | None = None,
                   manifest_root: Path | None = None, limits: Limits | None = None) -> Capture:
    limits = limits or Limits()
    validate_manifest(manifest)
    report = report.resolve()
    metadata_path = within(report, "raw.jsonl")
    metadata_hash = hash_file(metadata_path, limits.input_bytes)
    capture = Capture(id=capture_id or metadata_hash, metadata_sha256=metadata_hash, manifest=manifest)
    strings: list[str] = []
    events: dict[tuple[int | None, int, int], Compilation] = {}
    states: dict[str, dict] = {}
    versions: set[str] = set()
    ranks: set[int] = set()
    processes: set[str] = set()
    unknown = set()
    saw_header = False
    payload_hashes: dict[str, str] = {}
    configuration_hashes: dict[str, set[str]] = {}
    payload_total = metadata_path.stat().st_size

    def notice(code: str, message: str, evidence_id: str | None = None) -> None:
        capture.notices.append(Notice(code=code, message=message, evidence_ids=[evidence_id] if evidence_id else []))
        capture.validity.artifact_structure = "partial"

    for number, offset, length, data in records(metadata_path, limits):
        capture.records_read = number
        record_id = f"record-{number}"
        record_evidence = Evidence(id=record_id, artifact="raw.jsonl", sha256=metadata_hash, byte_offset=offset,
                                   byte_length=length, record_line=number, kind="metadata")
        if data is None:
            capture.evidence[record_id] = record_evidence
            notice("malformed_record", f"Record {number} is not a JSON object", record_id)
            continue
        if "string_table" in data:
            if saw_header:
                raise DynamoDiffError("unsupported_scope", "Multiple string tables may combine captures; import each separately")
            table = data["string_table"]
            if not isinstance(table, list) or not all(isinstance(value, str) for value in table):
                raise DynamoDiffError("unsupported_format", "Expected a tlparse string-table header")
            strings, saw_header = table, True
            continue
        if not saw_header:
            raise DynamoDiffError("unsupported_format", "Expected tlparse raw.jsonl with a string-table header")
        if data.get("compiled_autograd_id") is not None or "bwd_compilation_metrics" in data:
            raise DynamoDiffError("unsupported_scope", "Compiled-autograd/backward analysis is not supported by this adapter")
        rank = data.get("rank")
        if rank is not None:
            if type(rank) is not int:
                raise DynamoDiffError("malformed_input", "Rank must be an integer")
            ranks.add(rank)
        for field in ["pid", "process_id"]:
            if data.get(field) is not None:
                processes.add(str(data[field]))
        if len(ranks) > 1 or len(processes) > 1:
            raise DynamoDiffError("unsupported_scope", "Import one process/rank at a time")
        unknown.update(set(data) - COMMON - KNOWN)
        artifact = data.get("artifact", {})
        if not isinstance(artifact, dict):
            notice("malformed_record", f"Record {number} has invalid artifact metadata", record_id)
            capture.evidence[record_id] = record_evidence
            continue
        artifact_name = artifact.get("name")
        if artifact_name is not None and not isinstance(artifact_name, str):
            notice("malformed_record", f"Record {number} has an invalid artifact name", record_id)
            capture.evidence[record_id] = record_evidence
            continue
        relevant = bool(set(data) & {"dynamo_start", "dynamo_output_graph", "dynamo_cpp_guards_str", "compilation_metrics"}) or artifact_name in {"torch_version", "recompile_reasons", "dynamo_error", "dynamo_graph_break_reason"}
        if not relevant:
            continue
        capture.evidence[record_id] = record_evidence
        payload_id, payload_text = None, None
        payload = data.get("payload_filename")
        if payload is not None:
            if not isinstance(payload, str):
                notice("malformed_payload", f"Invalid payload reference at record {number}", record_id)
            else:
                path = within(report, payload)
                try:
                    if payload not in payload_hashes and path.is_file():
                        payload_total += path.stat().st_size
                        if payload_total > limits.input_bytes:
                            raise DynamoDiffError("resource_limit", "Metadata and evidence exceed the input-byte budget")
                    payload_hash = payload_hashes.get(payload) or hash_file(path, limits.payload_bytes)
                    payload_hashes[payload] = payload_hash
                    payload_id = f"payload-{number}"
                    capture.evidence[payload_id] = Evidence(id=payload_id, artifact=payload, sha256=payload_hash,
                        byte_length=path.stat().st_size, kind=str(artifact_name or "graph_or_guards"), record_line=number)
                    if artifact_name in {"torch_version", "recompile_reasons", "dynamo_error", "dynamo_graph_break_reason"}:
                        payload_text = read_text(path, limits.payload_bytes)
                except DynamoDiffError as error:
                    if error.code != "missing_artifact":
                        raise
                    notice("missing_payload", f"Missing payload referenced at record {number}", record_id)
        elif data.get("has_payload"):
            notice("missing_payload", f"No payload file recorded at record {number}", record_id)
        if artifact_name == "torch_version" and payload_text is not None:
            try:
                version_info = json_value(payload_text)
                version = version_info.get("pytorch_version")
                if isinstance(version, str):
                    versions.add(version)
                capture.producer.update(version_info)
            except (ValueError, UnicodeError, RecursionError, AttributeError):
                notice("malformed_payload", "Invalid torch_version payload", payload_id)
            continue
        frame_id, compile_id = data.get("frame_id"), data.get("frame_compile_id")
        if type(frame_id) is not int or type(compile_id) is not int or min(frame_id, compile_id) < 0:
            notice("unscoped_record", f"Cannot associate compiler record {number} with a compilation", record_id)
            continue
        key = (rank, frame_id, compile_id)
        if key not in events:
            if len(events) >= limits.events:
                raise DynamoDiffError("resource_limit", "Compilation identity limit exceeded")
            identifier = f"rank-{rank if rank is not None else 'unspecified'}:{frame_id}/{compile_id}"
            events[key] = Compilation(id=identifier, frame_id=frame_id, frame_compile_id=compile_id, rank=rank)
            states[identifier] = {"graph": False, "metrics": None, "recompile_artifact": False}
        event = events[key]
        state = states[event.id]
        event.evidence_ids.append(record_id)
        if payload_id:
            event.evidence_ids.append(payload_id)
        attempt = data.get("attempt", 0)
        if type(attempt) is not int or attempt < 0:
            notice("invalid_attempt", f"Invalid attempt for {event.id}", record_id)
        elif attempt not in event.attempts:
            event.attempts.append(attempt)
        if "dynamo_start" in data:
            start = data["dynamo_start"]
            event.source = _source_from_stack(start.get("stack") if isinstance(start, dict) else None, strings)
        if "dynamo_output_graph" in data:
            if isinstance(data["dynamo_output_graph"], dict):
                state["graph"] = True
            else:
                state["malformed_graph"] = True
                notice("malformed_graph", f"Invalid graph-output record for {event.id}", record_id)
        if artifact_name == "recompile_reasons":
            state["recompile_artifact"] = True
            event.recompilation = "confirmed"
            if payload_text is not None:
                try:
                    for index, reason in enumerate(reason_strings(payload_text)):
                        identifier = f"{payload_id}:reason-{index}"
                        capture.evidence[identifier] = capture.evidence[payload_id].model_copy(update={"id": identifier, "payload_index": index})
                        summary = guard_summary(reason)
                        event.reasons.append(GuardReason(categories=categories(summary), summary=summary, evidence_id=identifier))
                except DynamoDiffError as error:
                    notice(error.code, str(error), payload_id)
        if artifact_name == "dynamo_graph_break_reason" and payload_text is not None:
            match = re.search(r"Graph break in user code at (.+):(\d+)", payload_text)
            fallback = "fall back to eager" in payload_text or "fallback to eager" in payload_text
            event.graph_breaks.append(GraphBreak(evidence_id=payload_id, site=match.group(0).removeprefix("Graph break in user code at ") if match else None,
                summary=guard_summary(payload_text), fallback_reported=fallback))
            event.fallback_reported |= fallback
        if artifact_name == "dynamo_error":
            event.outcome = "failed"
        if "compilation_metrics" in data:
            metrics = data["compilation_metrics"]
            if not isinstance(metrics, dict):
                notice("malformed_metrics", f"Invalid metrics for {event.id}", record_id)
                continue
            if state["metrics"] is not None:
                notice("duplicate_terminal", f"Multiple terminal metrics for {event.id}; outcome is unresolved", record_id)
                state["duplicate_terminal"] = True
            state["metrics"] = metrics
            event.terminal_evidence_id = record_id
            if type(metrics.get("log_format_version")) is not int or metrics["log_format_version"] != 3:
                raise DynamoDiffError("unsupported_format", "This adapter requires PyTorch log_format_version 3")
            if isinstance(metrics.get("pytorch_version"), str):
                versions.add(metrics["pytorch_version"])
            for config_name in ["dynamo_config", "compiler_config", "functorch_config", "inductor_config"]:
                if isinstance(metrics.get(config_name), str):
                    try:
                        config = json_value(metrics[config_name])
                        serialized = json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)
                        configuration_hashes.setdefault(config_name, set()).add(hashlib.sha256(serialized.encode()).hexdigest())
                    except (ValueError, UnicodeError, RecursionError):
                        notice("malformed_configuration", f"Invalid {config_name} at record {number}", record_id)
            for field, target in [("co_filename", "captured_path"), ("co_name", "function"), ("co_firstlineno", "first_line")]:
                value = metrics.get(field)
                if (target == "first_line" and type(value) is int) or (target != "first_line" and isinstance(value, str)):
                    setattr(event.source, target, value)
                    event.source.attribution = "trace"

    if not saw_header:
        raise DynamoDiffError("unsupported_format", "Empty or unrecognized tlparse export")
    if not versions:
        notice("unverified_producer", "No PyTorch version evidence; compilation outcomes cannot be verified")
    elif versions != {"2.14.0"}:
        raise DynamoDiffError("unsupported_version", f"Supported PyTorch version is 2.14.0; observed {sorted(versions)}")
    capture.producer["pytorch_version"] = next(iter(versions)) if len(versions) == 1 else None
    # Fill source only within the same run-local frame; no cross-run numeric matching.
    frame_sources = {}
    for event in events.values():
        if event.source.captured_path and event.source.function:
            frame_sources.setdefault((event.rank, event.frame_id), event.source)
    seen_frames = set()
    for event in events.values():
        state = states[event.id]
        metrics = state["metrics"]
        frame = (event.rank, event.frame_id)
        if not event.source.captured_path and frame in frame_sources:
            event.source = frame_sources[frame].model_copy(deep=True, update={"attribution": "same_run_frame"})
        _enrich_source(event.source, manifest, manifest_root, limits)
        if isinstance(metrics, dict):
            reason = metrics.get("recompile_reason")
            if isinstance(reason, str) and reason.strip():
                event.recompilation = "confirmed"
                if not event.reasons:
                    summary = guard_summary(reason)
                    event.reasons.append(GuardReason(categories=categories(summary), summary=summary, evidence_id=event.terminal_evidence_id))
            elif "recompile_reason" in metrics and not state["recompile_artifact"]:
                event.recompilation = "not_reported" if reason is None else "unknown"
            if metrics.get("fail_type") or metrics.get("fail_reason"):
                event.outcome = "failed"
                event.error_type = str(metrics.get("fail_type") or "CompilerFailure")
                reason_text = str(metrics.get("fail_reason") or "")
                event.limit_reported = "recompile limit exceeded" in reason_text.lower()
            elif event.outcome != "failed":
                if metrics.get("has_guarded_code") is True and state["graph"] and type(metrics.get("graph_op_count")) is int and metrics["graph_op_count"] > 0:
                    event.outcome = "completed"
                elif (not state["graph"] and metrics.get("has_guarded_code") is True and "graph_op_count" in metrics
                      and (metrics["graph_op_count"] is None or (type(metrics["graph_op_count"]) is int and metrics["graph_op_count"] == 0))):
                    event.outcome = "no_graph_observed"
            if type(metrics.get("dynamo_cumulative_compile_time_us")) is int:
                event.duration_us = metrics["dynamo_cumulative_compile_time_us"]
                event.duration_metric = "dynamo_cumulative_compile_time_us"
        else:
            event.notices.append(Notice(code="missing_terminal", message="No terminal metrics; outcome is incomplete", evidence_ids=event.evidence_ids[:1]))
        if state.get("duplicate_terminal") or state.get("malformed_graph") or not versions:
            event.outcome = "unknown"
        event.classification = "confirmed_recompilation" if event.recompilation == "confirmed" else (
            "first_observed_compilation" if frame not in seen_frames else "additional_frame_compilation")
        seen_frames.add(frame)
        event.attempts.sort()
    if manifest:
        producer = manifest.get("producer", {})
        if not isinstance(producer, dict):
            raise DynamoDiffError("malformed_manifest", "producer must be an object")
        if producer.get("torch") and producer["torch"] not in versions:
            raise DynamoDiffError("inconsistent_metadata", "Manifest PyTorch version disagrees with trace evidence")
        if producer.get("tlparse") not in [None, "0.4.3"]:
            raise DynamoDiffError("unsupported_version", "This adapter is tested with tlparse 0.4.3")
        capture.producer["tlparse"] = producer.get("tlparse")
    capture.compilations = list(events.values())
    capture.counts = count_compilations(capture.compilations)
    capture.unknown_record_types = sorted(unknown)
    capture.observed_configurations = {name: sorted(values) for name, values in configuration_hashes.items()}
    if unknown:
        capture.notices.append(Notice(code="unknown_record_types", message="Uninterpreted record types are retained as raw evidence: " + ", ".join(sorted(unknown))))
    return capture
