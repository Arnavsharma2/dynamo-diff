import asyncio
import json
from pathlib import Path
import sys

import pytest

from dynamo_diff.compare import compare_runs
from dynamo_diff.errors import DynamoDiffError
from dynamo_diff.mcp_server import AnalysisTools
from dynamo_diff.store import Store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/captures"


def test_tool_pagination_preserves_counts_and_source_rows(tmp_path):
    store = Store(tmp_path)
    tools = AnalysisTools(store, [FIXTURES])
    captures = [tools.import_trace(str(FIXTURES / case / "report"), str(FIXTURES / case / "manifest.json")) for case in ["edit_before", "edit_after"]]
    ids = [c["capture_id"] for c in captures]
    first = tools.compare_runs(*ids, page_size=1)
    assert first["truncated"]
    second = tools.compare_runs(*ids, offset=first["next_offset"], page_size=1)
    assert not second["truncated"]
    full = compare_runs(store, *ids)
    assert first["baseline_counts"] == full.baseline_counts.model_dump()
    assert first["candidate_counts"] == full.candidate_counts.model_dump()
    assert len(first["functions"]) + len(second["functions"]) == len(full.functions)
    assert all(len(json.dumps(page, ensure_ascii=False)) <= store.limits.response_chars for page in [first, second])


def test_tool_import_roots_and_symlinks(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    (allowed / "escape").symlink_to(FIXTURES, target_is_directory=True)
    tools = AnalysisTools(Store(tmp_path / "store"), [allowed])
    for path in [FIXTURES / "stable/report", allowed / "escape/stable/report"]:
        with pytest.raises(DynamoDiffError) as error:
            tools.import_trace(str(path))
        assert error.value.code == "path_not_allowed"


def test_evidence_index_discovers_every_hidden_reason_and_paginates(tmp_path):
    store = Store(tmp_path)
    tools = AnalysisTools(store, [FIXTURES])
    capture = store.import_trace(FIXTURES / "multiple_guards/report")
    compact = tools.compare_runs(capture.id, capture.id)
    shown = set(compact["functions"][0]["baseline"][0]["evidence_ids"])
    reasons = {r.evidence_id for event in capture.compilations for r in event.reasons}
    assert reasons - shown  # The original compact report alone cannot expose them all.
    offset, indexed = 0, []
    while True:
        page = tools.get_evidence(capture.id, offset=offset, max_chars=1000)
        assert len(json.dumps(page, ensure_ascii=False)) <= 1000
        indexed.extend(entry["evidence_id"] for entry in page["entries"])
        if page["next_offset"] is None:
            break
        assert page["next_offset"] > offset
        offset = page["next_offset"]
    assert len(indexed) == len(set(indexed)) == len(capture.evidence)
    assert set(indexed) == set(capture.evidence)
    filtered = tools.get_evidence(capture.id, kind="recompile_reasons")
    assert reasons <= {entry["evidence_id"] for entry in filtered["entries"]}
    for entry in filtered["entries"]:
        assert tools.get_evidence(capture.id, entry["evidence_id"])["text"]
    assert tools.get_evidence(capture.id, kind="unrecorded-kind")["entries"] == []
    with pytest.raises(DynamoDiffError):
        tools.get_evidence(capture.id, next(iter(reasons)), kind="recompile_reasons")


def test_real_mcp_stdio_roundtrip(tmp_path):
    pytest.importorskip("mcp")
    from mcp import Client, StdioServerParameters

    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "dynamo_diff.cli", "--store", str(tmp_path),
            "serve-mcp", "--allow-root", str(FIXTURES)])
        async with Client(params, read_timeout_seconds=30) as client:
            listed = await client.list_tools()
            tools = listed.tools if hasattr(listed, "tools") else listed
            assert {tool.name for tool in tools} == {"import_trace", "compare_runs", "get_evidence"}
            ids = []
            discovery = []
            for case in ["edit_before", "edit_after"]:
                result = await client.call_tool("import_trace", {"report_directory": str(FIXTURES / case / "report"),
                    "manifest_path": str(FIXTURES / case / "manifest.json")})
                assert not result.is_error
                ids.append(result.structured_content["capture_id"])
                discovery.append(result.structured_content["next_steps"]["evidence_index"])
            report = await client.call_tool("compare_runs", {"baseline_id": ids[0], "candidate_id": ids[1]})
            assert not report.is_error
            assert report.structured_content["workload_comparability"] == "manifest_consistent"
            assert report.structured_content["baseline_counts"]["completed"] == 3
            assert report.structured_content["candidate_counts"]["completed"] == 2
            evidence_id = report.structured_content["functions"][0]["baseline"][0]["evidence_ids"][0]
            evidence = await client.call_tool("get_evidence", {"capture_id": ids[0], "evidence_id": evidence_id, "max_chars": 100})
            assert not evidence.is_error
            assert len(evidence.structured_content["text"]) <= 100
            # A client can follow the returned action without knowing an evidence ID.
            action = discovery[0]
            index = await client.call_tool(action["tool"], {**action["arguments"], "kind": "recompile_reasons"})
            assert not index.is_error
            assert index.structured_content["mode"] == "index"
            assert any(entry["payload_index"] is not None for entry in index.structured_content["entries"])
            denied = await client.call_tool("import_trace", {"report_directory": str(tmp_path.parent)})
            assert denied.is_error
            assert denied.structured_content["error"]["code"] == "path_not_allowed"
    asyncio.run(run())
