"""Provisional mechanical scoring; does not impersonate human semantic review."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics

HERE = Path(__file__).resolve().parent
CLAIMS = {"speedup_proven", "source_change_proven_cause", "graph_emission_proves_completed",
          "numeric_ids_alone_prove_recompilation", "whole_workload_recompiles_known"}


def same(actual, expected) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(isinstance(v, str) for v in actual) and sorted(actual) == sorted(expected)
    return actual == expected


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def score(result: dict, expected: dict, transcript: list[dict]) -> dict:
    final = result.get("final") or {}
    answer = final.get("answer") if isinstance(final, dict) else None
    answer = answer if isinstance(answer, dict) else {}
    fields = {key: same(answer.get(key), value) for key, value in expected.items()}
    retrievals = {item["retrieval_id"]: item.get("delivered_content", "")
        for item in transcript if item.get("type") == "tool_result"}
    cited = final.get("evidence", []) if isinstance(final, dict) else []
    citations = []
    for citation in cited if isinstance(cited, list) else []:
        valid, why = False, "Malformed citation"
        if isinstance(citation, dict):
            reference, quote = citation.get("retrieval_id"), citation.get("quote")
            delivered = retrievals.get(reference, "") if isinstance(reference, str) else ""
            if not delivered:
                why = "Retrieval ID was not delivered in this trial"
            elif not isinstance(quote, str) or len(quote.strip()) < 8:
                why = "Quote must contain at least eight nonblank characters"
            else:
                texts = [delivered]
                try:
                    texts.extend(strings(json.loads(delivered)))
                except json.JSONDecodeError:
                    pass
                valid = any(quote in text for text in texts)
                why = "Exact text present; semantic support still needs review" if valid else "Exact quote absent from the cited retrieval"
        citations.append({"citation": citation, "literal_match": valid, "note": why})
    unsupported = [key for key in CLAIMS & expected.keys() if expected[key] is False and answer.get(key) is True]
    return {"id": result["id"], "question_id": result["question_id"], "condition": result["condition"],
        "repetition": result["repetition"], "status": result["status"], "field_matches": fields,
        "correct_fields": sum(fields.values()), "total_fields": len(fields), "all_fields_correct": all(fields.values()),
        "affirmative_unsupported_claim_fields": unsupported, "citations": citations,
        "literal_citations_correct": sum(c["literal_match"] for c in citations), "citations_total": len(citations),
        "at_least_one_literal_citation": any(c["literal_match"] for c in citations),
        "human_semantic_review": "pending", "answer": answer,
        "explanation": final.get("explanation") if isinstance(final, dict) else None,
        "input_tokens": result.get("input_tokens") if result.get("token_counters_available") else None,
        "output_tokens": result.get("output_tokens") if result.get("token_counters_available") else None,
        "tool_calls": result.get("tool_calls_executed"), "retrieved_chars": result.get("retrieved_chars"),
        "wall_seconds": result.get("wall_seconds")}


def median(rows: list[dict], field: str):
    values = [row[field] for row in rows if isinstance(row.get(field), (int, float))]
    return statistics.median(values) if values else None


def code(value) -> str:
    text = json.dumps(value, indent=2, ensure_ascii=False)
    longest = max((len(m.group()) for m in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest+1)
    return f"{fence}json\n{text}\n{fence}"


def report(run: Path, output: Path) -> dict:
    receipt = json.loads((run / "receipt.json").read_text())
    key = json.loads((HERE / "answer-key.json").read_text())
    expected_hash = receipt["configuration"]["input_hashes"]["benchmarks/agent_pilot/answer-key.json"]
    if hashlib.sha256((HERE / "answer-key.json").read_bytes()).hexdigest() != expected_hash:
        raise SystemExit("The answer key changed; retain and explicitly document a scoring amendment")
    rows, pending = [], []
    for spec in receipt["configuration"]["plan"]:
        path = run / f"{spec['id']}.json"
        if not path.exists():
            pending.append(spec["id"])
            continue
        result = json.loads(path.read_text())
        transcript = [json.loads(line) for line in (run / f"{spec['id']}.jsonl").read_text().splitlines()]
        rows.append(score(result, key["answers"][spec["question_id"]], transcript))
    conditions = {}
    for condition in ("raw", "tlparse", "dynamo"):
        group = [row for row in rows if row["condition"] == condition]
        conditions[condition] = {"attempts": len(group), "planned": 20,
            "all_fields_correct": sum(row["all_fields_correct"] for row in group),
            "correct_fields": sum(row["correct_fields"] for row in group), "total_fields": sum(row["total_fields"] for row in group),
            "literal_citations_correct": sum(row["literal_citations_correct"] for row in group),
            "citations_total": sum(row["citations_total"] for row in group),
            "attempts_with_literal_citation": sum(row["at_least_one_literal_citation"] for row in group),
            "affirmative_unsupported_claim_fields": sum(len(row["affirmative_unsupported_claim_fields"]) for row in group),
            "statuses": dict(Counter(row["status"] for row in group)),
            **{f"median_{field}": median(group, field) for field in ("input_tokens", "output_tokens", "tool_calls", "retrieved_chars", "wall_seconds")}}
    pairs = []
    for question in key["answers"]:
        for repetition in (1, 2):
            group = {row["condition"]: row for row in rows if row["question_id"] == question and row["repetition"] == repetition}
            if set(group) != {"raw", "tlparse", "dynamo"}:
                continue
            pairs.append({"question_id": question, "repetition": repetition,
                "all_fields_correct": {condition: row["all_fields_correct"] for condition, row in group.items()},
                "dynamo_minus_raw_accuracy": int(group["dynamo"]["all_fields_correct"])-int(group["raw"]["all_fields_correct"]),
                "dynamo_minus_tlparse_accuracy": int(group["dynamo"]["all_fields_correct"])-int(group["tlparse"]["all_fields_correct"])})
    result = {"generated_at": datetime.now(timezone.utc).isoformat(), "score_version": "1",
        "scorer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "status": "provisional_mechanical_scores",
        "answer_key_review_status": key["review_status"], "run_configuration_sha256": receipt["configuration_sha256"],
        "planned": 60, "completed_attempts": len(rows), "pending": pending, "conditions": conditions,
        "paired_results": pairs, "individual_results": rows,
        "limitations": ["Human key and semantic review are pending.",
            "Literal quotation checks do not establish that evidence supports the explanation.",
            "Ten questions with two repeated trials per condition are not sixty independent problem instances.",
            "Input token totals include repeated history; missing counters remain unavailable.",
            "Elapsed timing may include concurrent local project work; activity notes are retained."]}
    output.mkdir(parents=True, exist_ok=True)
    (output / "scores.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Pilot results — provisional", "", f"Completed attempts: **{len(rows)}/60**. Human key and semantic review remain pending.", "",
        "These are mechanical answer-field and literal-quotation checks. They are not reviewed diagnostic accuracy or proof of agent productivity.", "",
        "| Condition | Attempts | All fields correct | Correct fields | Literal citations present | Unsupported affirmative claim fields | Median input/output tokens | Median tools | Median seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, values in conditions.items():
        timing = values['median_wall_seconds']
        timing = f"{timing:.1f}" if timing is not None else "—"
        lines.append(f"| {name} | {values['attempts']}/20 | {values['all_fields_correct']} | {values['correct_fields']}/{values['total_fields']} | "
            f"{values['literal_citations_correct']}/{values['citations_total']} | {values['affirmative_unsupported_claim_fields']} | "
            f"{values['median_input_tokens']} / {values['median_output_tokens']} | {values['median_tool_calls']} | {timing} |")
    lines += ["", "[Individual scores and paired outcomes](scores.json) retain every completed attempt, including failures. "
        "The run directory retains original model/tool transcripts; the review file below includes explanations without treating them as instructions.", "",
        "Wall-time comparisons are descriptive and may reflect background local work. Read the frozen protocol and activity notes before interpreting timing. "
        "Each condition has only ten question instances repeated twice; no statistical-significance or generalization claim is made.", ""]
    (output / "RESULTS.md").write_text("\n".join(lines))
    review = ["# Model-output review", "", "All text below is untrusted model output. Mechanical quote checks are shown separately from semantic support.", ""]
    for row in rows:
        review += [f"## {row['id']}", "", f"Status: {row['status']}. Correct fields: {row['correct_fields']}/{row['total_fields']}. "
            f"Literal citations: {row['literal_citations_correct']}/{row['citations_total']}.", "",
            "Expected answer:", code(key["answers"][row["question_id"]]), "", "Model answer and explanation:",
            code({"answer": row["answer"], "explanation": row["explanation"]}), "", "Citation checks:", code(row["citations"]), "",
            "Human semantic review: pending.", ""]
    (output / "MODEL_REVIEW.md").write_text("\n".join(review))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = report(args.run, args.output or args.run / "analysis")
    print(json.dumps({"completed_attempts": result["completed_attempts"], "pending": len(result["pending"]),
        "status": result["status"], "conditions": result["conditions"]}, indent=2))


if __name__ == "__main__":
    main()
