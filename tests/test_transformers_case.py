"""The retained full generate() investigation is inspectable without ML dependencies."""

import importlib.util
from pathlib import Path

from dynamo_diff.store import Store

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case_studies/transformers_cache"


def test_real_transformers_case_has_independent_output_and_event_evidence(tmp_path):
    spec = importlib.util.spec_from_file_location("transformers_case_verify", CASE / "verify.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify(CASE / "captures", Store(tmp_path))
    assert len(result["checks"]) == 3
    # Automated checks cannot satisfy the separate human explanation-review gate.
    assert result["review_status"] == "human_review_pending"
