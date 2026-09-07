import hashlib
import json
from pathlib import Path
import shutil

import pytest

from dynamo_diff.errors import DynamoDiffError
from dynamo_diff.store import Store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/captures"


def test_import_is_idempotent_and_immutable(tmp_path):
    root = tmp_path / "source"
    shutil.copytree(FIXTURES / "multiple_guards", root)
    store = Store(tmp_path / "store")
    first = store.import_trace(root / "report", manifest_path=root / "manifest.json")
    second = store.import_trace(root / "report", manifest_path=root / "manifest.json")
    assert first.id == second.id
    assert first.validity.workload_completion == "declared_completed"
    evidence_id = first.compilations[-1].reasons[-1].evidence_id
    before = store.get_evidence(first.id, evidence_id)
    shutil.rmtree(root)
    assert store.get_evidence(first.id, evidence_id) == before
    store.load(first.id, verify_artifacts=True)


def test_modified_imported_evidence_is_detected(tmp_path):
    store = Store(tmp_path / "store")
    capture = store.import_trace(FIXTURES / "shape/report")
    evidence = capture.evidence[capture.compilations[-1].reasons[0].evidence_id]
    (store.capture_dir(capture.id) / "report" / evidence.artifact).write_text("changed")
    with pytest.raises(DynamoDiffError) as error:
        store.get_evidence(capture.id, evidence.id)
    assert error.value.code == "corrupt_store"


def test_manifest_finalization_is_bound_to_export_bytes(tmp_path):
    root = tmp_path / "source"
    shutil.copytree(FIXTURES / "multiple_guards", root)
    metadata = root / "report/raw.jsonl"
    metadata.write_text("\n".join(metadata.read_text().splitlines()[:9]) + "\n")
    with pytest.raises(DynamoDiffError) as error:
        Store(tmp_path / "store").import_trace(root / "report", manifest_path=root / "manifest.json")
    assert error.value.code == "inconsistent_metadata"


def test_unfinalized_export_never_claims_completed(tmp_path):
    root = tmp_path / "source"
    shutil.copytree(FIXTURES / "stable", root)
    manifest = json.loads((root / "manifest.json").read_text())
    del manifest["capture"]["report_sha256"]
    (root / "manifest.json").write_text(json.dumps(manifest))
    capture = Store(tmp_path / "store").import_trace(root / "report", manifest_path=root / "manifest.json")
    assert capture.validity.workload_completion == "unknown"


def test_changed_manifest_creates_new_capture(tmp_path):
    root = tmp_path / "source"
    shutil.copytree(FIXTURES / "stable", root)
    store = Store(tmp_path / "store")
    first = store.import_trace(root / "report", manifest_path=root / "manifest.json")
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["workload"]["seed"] += 1
    (root / "manifest.json").write_text(json.dumps(manifest))
    second = store.import_trace(root / "report", manifest_path=root / "manifest.json")
    assert first.id != second.id


def test_evidence_pagination_reconstructs_exact_payload(tmp_path):
    store = Store(tmp_path / "store")
    capture = store.import_trace(FIXTURES / "multiple_guards/report")
    evidence_id = capture.compilations[-1].reasons[0].evidence_id
    expected = store.get_evidence(capture.id, evidence_id)["text"]
    offset, pieces = 0, []
    while True:
        page = store.get_evidence(capture.id, evidence_id, offset=offset, max_chars=73)
        assert len(page["text"]) <= 73
        pieces.append(page["text"])
        if page["next_offset"] is None:
            break
        offset = page["next_offset"]
    assert "".join(pieces) == expected


def test_normalized_capture_tampering_is_detected(tmp_path):
    store = Store(tmp_path / "store")
    capture = store.import_trace(FIXTURES / "stable/report")
    path = store.capture_dir(capture.id) / "capture.json"
    data = json.loads(path.read_text())
    data["counts"]["completed"] = 99
    path.write_text(json.dumps(data))
    with pytest.raises(DynamoDiffError) as error:
        store.load(capture.id)
    assert error.value.code == "corrupt_store"


def test_captured_sources_survive_working_tree_changes_and_removal(tmp_path):
    root = tmp_path / "source with spaces"
    shutil.copytree(FIXTURES / "edit_before", root)
    store = Store(tmp_path / "store with spaces")
    capture = store.import_trace(root / "report", manifest_path=root / "manifest.json")
    event = capture.compilations[0]
    function_id = event.id.rsplit("/", 1)[0]
    source = store.get_source(capture.id, function_id)
    expected = (root / "sources/model.py").read_text()
    assert source["text"] == expected
    assert source["sha256"] == hashlib.sha256(expected.encode()).hexdigest()
    assert source["first_line"] == event.source.first_line
    shutil.rmtree(root)
    assert store.get_source(capture.id, function_id) == source
    (store.capture_dir(capture.id) / "context" / event.source.snapshot).write_text("changed")
    with pytest.raises(DynamoDiffError) as error:
        store.get_source(capture.id, function_id)
    assert error.value.code == "corrupt_store"


def test_source_errors_are_explicit_without_working_tree_fallback(tmp_path):
    store = Store(tmp_path)
    capture = store.import_trace(FIXTURES / "edit_before/report")
    with pytest.raises(DynamoDiffError) as error:
        store.get_source(capture.id, "rank-unspecified:0")
    assert error.value.code == "missing_source"
    with pytest.raises(DynamoDiffError) as error:
        store.get_source(capture.id, "../arbitrary-file")
    assert error.value.code == "unknown_function"


def test_import_never_executes_guard_or_source_python(tmp_path):
    root = tmp_path / "adversarial-bundle"
    shutil.copytree(FIXTURES / "multiple_guards", root)
    marker = tmp_path / "must-not-be-created"
    expression = f"__import__('pathlib').Path({str(marker)!r}).write_text('executed')"
    records = [json.loads(line) for line in (root / "report/raw.jsonl").read_text().splitlines()]
    payloads = [record["payload_filename"] for record in records if record.get("artifact", {}).get("name") == "recompile_reasons"]
    assert payloads
    for name in payloads:
        (root / "report" / name).write_text(json.dumps([expression]))
    manifest = json.loads((root / "manifest.json").read_text())
    source = root / manifest["source"]["files"][0]["snapshot"]
    source.write_text(source.read_text() + "\n" + expression + "\n")
    manifest["source"]["files"][0]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    (root / "manifest.json").write_text(json.dumps(manifest))
    store = Store(tmp_path / "store")
    capture = store.import_trace(root / "report", manifest_path=root / "manifest.json")
    reasons = [reason for event in capture.compilations for reason in event.reasons]
    assert any(expression in reason.summary for reason in reasons)
    assert any(expression in store.get_evidence(capture.id, reason.evidence_id)["text"] for reason in reasons)
    assert expression in store.get_source(capture.id, "rank-unspecified:0")["text"]
    assert not marker.exists()
