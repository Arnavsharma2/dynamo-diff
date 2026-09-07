"""Post-hoc format sensitivity analysis; never repairs primary trial results."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from score import same

HERE = Path(__file__).resolve().parent


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key")
        result[key] = value
    return result


def finite_constant(value):
    raise ValueError(f"Non-JSON constant: {value}")


DECODER = json.JSONDecoder(object_pairs_hook=unique_object, parse_constant=finite_constant)


def answer_prefix(text):
    """Decode only an untouched first answer member; do not repair any text."""
    if not isinstance(text, str):
        return None
    match = re.match(r'^\s*\{\s*"answer"\s*:\s*', text)
    if not match:
        return None
    try:
        answer, end = DECODER.raw_decode(text, match.end())
    except (ValueError, RecursionError):
        return None
    following = text[end:].lstrip()
    if not isinstance(answer, dict) or not following.startswith((",", "}")):
        return None
    return answer


def report(run: Path):
    receipt = json.loads((run / "receipt.json").read_text())
    key_path = HERE / "answer-key.json"
    expected_hash = receipt["configuration"]["input_hashes"]["benchmarks/agent_pilot/answer-key.json"]
    if hashlib.sha256(key_path.read_bytes()).hexdigest() != expected_hash:
        raise SystemExit("The frozen answer key changed")
    key = json.loads(key_path.read_text())["answers"]
    rows = []
    for spec in receipt["configuration"]["plan"]:
        path = run / f"{spec['id']}.json"
        if not path.exists():
            continue
        result = json.loads(path.read_text())
        answer = answer_prefix(result.get("final_text"))
        expected = key[spec["question_id"]]
        fields = {name: answer is not None and name in answer and same(answer[name], value)
                  for name, value in expected.items()}
        rows.append({"id": spec["id"], "condition": spec["condition"], "primary_status": result["status"],
            "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "answer_prefix_available": answer is not None,
            "answer_prefix": answer, "field_matches": fields, "correct_fields": sum(fields.values()),
            "total_fields": len(fields), "all_fields_correct": all(fields.values())})
    conditions = {}
    for condition in ("raw", "tlparse", "dynamo"):
        group = [r for r in rows if r["condition"] == condition]
        conditions[condition] = {"attempts": len(group),
            "primary_statuses": dict(Counter(r["primary_status"] for r in group)),
            "available_answer_prefixes": sum(r["answer_prefix_available"] for r in group),
            "all_fields_correct": sum(r["all_fields_correct"] for r in group),
            "correct_fields": sum(r["correct_fields"] for r in group),
            "total_fields": sum(r["total_fields"] for r in group)}
    output = {"generated_at": datetime.now(timezone.utc).isoformat(), "status": "post_hoc_format_sensitivity",
        "method_version": "1", "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "origin": "Authored after inspecting malformed JSON in q02-dynamo-r1 and a valid but incorrect q01-raw-r1 answer. This analysis was not preregistered.",
        "method": "For every planned condition, decode an unchanged first answer member at the start of the original final text. Reject malformed answer objects, duplicate keys and non-JSON constants. Do not extract later embedded objects, repair quotes, strip fences or change values. Missing prefixes/fields remain incorrect in the denominator.",
        "limitations": ["Primary strict-JSON scores and original results remain unchanged.",
            "An intact answer object does not make the entire response valid JSON.",
            "This checks structured fields only, not explanatory accuracy or citation support.",
            "The answer key still needs human review; this is exploratory evidence, not confirmed agent improvement."],
        "attempts": len(rows), "planned": 60, "conditions": conditions, "individual_results": rows}
    dest = run / "analysis"
    dest.mkdir(exist_ok=True)
    (dest / "format-sensitivity.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    result = report(args.run)
    print(json.dumps({"status": result["status"], "attempts": result["attempts"], "conditions": result["conditions"]}, indent=2))
