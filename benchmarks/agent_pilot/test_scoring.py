import importlib.util
from pathlib import Path
import json

spec = importlib.util.spec_from_file_location("pilot_scoring", Path(__file__).with_name("score.py"))
scoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scoring)


def test_types_unknowns_and_unordered_category_sets():
    assert not scoring.same(False, 0)
    assert not scoring.same("2", 2)
    assert not scoring.same(None, 2)
    assert scoring.same(["grad_mode", "dtype_device"], ["dtype_device", "grad_mode"])
    assert not scoring.same(["grad_mode", "grad_mode"], ["grad_mode", "dtype_device"])


def test_citation_must_match_the_specific_delivered_retrieval():
    expected = {"completed": 2, "speedup_proven": False}
    transcript = [{"type": "tool_result", "retrieval_id": "r1", "delivered_content": json.dumps({"text": "The original retained text"})}]
    result = {"id": "synthetic", "question_id": "q00", "condition": "raw", "repetition": 1,
        "status": "completed", "final": {"answer": {"completed": 2, "speedup_proven": True}, "evidence": [
            {"retrieval_id": "r1", "quote": "original retained text"},
            {"retrieval_id": "r2", "quote": "original retained text"},
            {"retrieval_id": "r1", "quote": "a quote that was not seen"}]}}
    score = scoring.score(result, expected, transcript)
    assert score["correct_fields"] == 1 and not score["all_fields_correct"]
    assert score["literal_citations_correct"] == 1
    assert score["affirmative_unsupported_claim_fields"] == ["speedup_proven"]
    assert score["input_tokens"] is None
    assert score["human_semantic_review"] == "pending"


def test_invalid_or_failed_answers_remain_in_the_denominator():
    result = {"id": "synthetic", "question_id": "q00", "condition": "dynamo", "repetition": 2,
        "status": "trial_error", "final": None}
    score = scoring.score(result, {"completed": 2}, [])
    assert score["total_fields"] == 1 and score["correct_fields"] == 0
    assert score["citations_total"] == 0
