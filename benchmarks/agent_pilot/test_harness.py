"""Harness controls, using only synthetic data rather than held-out answers."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("pilot_runner", Path(__file__).with_name("run.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "q00"
    for part in ("sources", "raw", "report"):
        (root / "a" / part).mkdir(parents=True, exist_ok=True)
    (root / "a/manifest.json").write_text('{"workload":{"calls":[]}}')
    (root / "a/sources/model.py").write_text('print("not executed")')
    (root / "a/raw/trace.log").write_text("needle one\n" * 33)
    (root / "a/report/summary.html").write_text('<style>hidden-style</style><script>hidden-script</script><h1>visible</h1><a href="part.txt">link</a>')
    (root / "a/report/part.txt").write_text("needle two\n" * 33)
    (root / "a/workload-result.json").write_text('{"answer":999}')
    (root / "answer-key.json").write_text('{"answer":999}')
    return root


@pytest.mark.parametrize("condition", ["raw", "tlparse", "dynamo"])
def test_agent_cannot_read_outcomes_curator_or_other_representation(corpus, condition):
    files = runner.Files(corpus, condition)
    assert set(files.paths) >= {"a/manifest.json", "a/sources/model.py"}
    for name in ("../answer-key.json", "answer-key.json", "a/workload-result.json", "/etc/passwd"):
        with pytest.raises(ValueError, match="allowed file"):
            files.call("read_file", {"path": name})
    assert ("a/trace.log" in files.paths) == (condition == "raw")
    assert ("a/report/part.txt" in files.paths) == (condition == "tlparse")


def test_search_pagination_neither_skips_nor_duplicates_evidence(corpus):
    files = runner.Files(corpus, "raw")
    offset, positions = 0, []
    while True:
        page = files.call("search_files", {"query": "needle", "offset": offset, "max_matches": 4})
        assert page["total_matches"] == 33
        positions.extend(item["match_offset"] for item in page["matches"])
        if page["next_offset"] is None:
            break
        assert page["next_offset"] > offset
        offset = page["next_offset"]
    assert len(positions) == len(set(positions)) == 33
    for position in positions:
        assert files.call("read_file", {"path": "a/trace.log", "offset": position, "max_chars": 6})["text"] == "needle"


def test_html_baseline_preserves_visible_text_and_link_destination(corpus):
    text = runner.Files(corpus, "tlparse").text("a/report/summary.html")
    assert "visible" in text and "link (part.txt)" in text
    assert "hidden-style" not in text and "hidden-script" not in text


def test_order_contains_paired_repeats_of_every_condition():
    schedule = runner.plan()
    assert len(schedule) == len({item["id"] for item in schedule}) == 60
    assert schedule == runner.plan()
    for q in {item["question_id"] for item in schedule}:
        group = [item for item in schedule if item["question_id"] == q]
        assert {(item["condition"], item["repetition"]) for item in group} == {
            (condition, repeat) for condition in ("raw", "tlparse", "dynamo") for repeat in (1, 2)}
        assert {item["seed"] for item in group if item["repetition"] == 1} == {731}
