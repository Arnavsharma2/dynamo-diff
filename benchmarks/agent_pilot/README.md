# Diagnostic pilot: no demonstrated end-to-end improvement

All **60 planned attempts** finished under the [frozen protocol](PROTOCOL.md), using local Ollama 0.33.2 and the recorded qwen3:8b Q4_K_M digest. The runner's final configuration check passed. No trial was silently retried or removed. The answer key is **AI-reviewed**; independent human answer-key and semantic review have not occurred, so the results below remain provisional mechanical measurements. The user made that outside review optional for project delivery in the September 7 [scope revision](../../docs/PROJECT_SCOPE.md). The frozen protocol and original reports retain their historical review requirements; no trial, score or scientific validation claim was changed by this delivery decision.

## Primary result

| Representation | Valid final JSON | All requested fields correct | Correct fields | Median input tokens | Median tool calls | Median seconds |
|---|---:|---:|---:|---:|---:|---:|
| Raw trace | 14/20 | 0/20 | 21/86 | 8,704 | 4 | 49.4 |
| tlparse text | 17/20 | 1/20 | 21/86 | 12,588.5 | 7.5 | 48.7 |
| Dynamo Diff | 0/20 | 0/20 | 0/86 | 2,781.5 | 1 | 29.0 |

The predefined final-response contract required a complete valid JSON object. Every Dynamo Diff attempt failed that contract; all remain failures. Lower tokens and elapsed time for failed or incomplete answers are **not established productivity gains**. Timings also include concurrent local project work. The ten questions, repeated twice per representation, are not sixty independent problem instances.

The [primary report](runs/run-001/analysis/RESULTS.md) includes token/output counters, literal citation checks and explicit unsupported-claim fields. [Individual scores](runs/run-001/analysis/scores.json), [original transcripts](runs/run-001/) and the [model review packet](runs/run-001/analysis/MODEL_REVIEW.md) retain failures. Literal quotes appearing in retrieved text do not establish semantic support. Zero scored unsupported claims from malformed responses does not imply safe or correct reasoning.

## What failed

Inspection of `q02-dynamo-r1` found an intact answer object followed by an invalid citation: the model copied JSON fields into a quoted string without escaping the inner quotes. Its answer also left the last event's reason count unknown rather than retrieving the relevant evidence. A valid raw-condition response, `q01-raw-r1`, incorrectly counted four workload calls as four completed compilations and misidentified the guard category.

Across all Dynamo Diff trials, the agent made 28 `import_trace` calls, two `get_evidence` calls and **zero `compare_runs` calls**. The normalized summaries exposed useful counts, but this model frequently stopped before navigating the comparison and evidence interfaces. Transport success alone is not effective agent diagnosis.

## Exploratory format sensitivity

After observing the formatting failure, a separate [post-hoc analysis](diagnose_formatting.py) was authored. It decodes only an unchanged first `answer` member when that member is valid JSON. It does not repair quotes, search later objects, strip fences, change values, or replace the primary results. Every planned attempt remains in the denominator.

| Representation | All fields correct in isolated answer member | Correct fields in isolated answer member |
|---|---:|---:|
| Raw trace | 0/20 | 31/86 |
| tlparse text | 1/20 | 26/86 |
| Dynamo Diff | 10/20 | 65/86 |

These [exploratory results](runs/run-001/analysis/format-sensitivity.json) help distinguish response-format failure from incorrect fields. They were not preregistered, do not validate explanations or evidence, and do not demonstrate an end-to-end improvement. The full JSON response is still invalid. [Scoring history](runs/run-001/analysis/SCORING_NOTES.md) records when this analysis was introduced and the presentation-only scorer update.

## Product consequence and next experiment

The CLI and editor remain evidence viewers whose output must be interpreted alongside validity and comparability. The MCP integration is an **experimental agent interface**, with no established diagnosis-quality or productivity benefit from this pilot.

A next iteration should make the available follow-up actions easier to discover after import and keep output-format validation in the agent client. A future experiment should predeclare structured-response handling, bounded validation retries, semantic scoring and all resource costs, then use fresh held-out questions. It must retain this run and report its failures rather than overwrite them or retrofit a winning metric.

The post-pilot implementation now returns `next_steps` after import, including an executable evidence-index call and the required comparison arguments. The MCP transport test follows the returned evidence action. This is an unmeasured navigation change, not an improved evaluation result. The exact evaluated source and protocol were saved first in [frozen-code.tar.gz](runs/run-001/frozen-code.tar.gz), with a [hash receipt](runs/run-001/frozen-code-receipt.json); the frozen corpus remains separately available. Use those versions in an isolated checkout to reproduce the original implementation. The runner intentionally rejects changed core files; do not overwrite this run to test the revision.

Recreate the mechanical reports without any model call:

```sh
.venv/bin/python benchmarks/agent_pilot/score.py benchmarks/agent_pilot/runs/run-001
.venv/bin/python benchmarks/agent_pilot/diagnose_formatting.py benchmarks/agent_pilot/runs/run-001
```

The original run receipt records source and exposed-input hashes. The answer key in [ANSWER_REVIEW.md](ANSWER_REVIEW.md) is AI-reviewed, with optional human review unclaimed; expected counts were authored from direct compiler evidence and independent backend observations, not accepted from the analyzer's answers.
