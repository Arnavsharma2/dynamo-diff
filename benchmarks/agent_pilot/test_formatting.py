import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("format_sensitivity", HERE / "diagnose_formatting.py")
formatting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formatting)


def test_exact_answer_prefix_can_survive_a_broken_later_quote():
    text = '{"answer": {"completed": 2, "speedup_proven": false}, "evidence": [{"quote": "completed": 2}]}'
    assert formatting.answer_prefix(text) == {"completed": 2, "speedup_proven": False}


def test_no_repairs_or_later_object_search():
    for text in ('```json\n{"answer": {"x": 2}}\n```',
                 'Explanation: {"answer": {"x": 2}}',
                 '{"answer": {"x": 2,}}',
                 '{"answer": {"x": 1, "x": 2}}',
                 '{"answer": {"x": NaN}}',
                 '{"answer": {"x": 2}garbage',
                 '{"answer": [2]}', None):
        assert formatting.answer_prefix(text) is None


def test_nested_quoted_braces_and_arrays_preserve_values():
    text = ' { "answer": {"text": "a } brace", "nested": {"x": 2}, "categories": ["a", "b"]}, "explanation": "ok"}'
    assert formatting.answer_prefix(text) == {"text": "a } brace", "nested": {"x": 2}, "categories": ["a", "b"]}
