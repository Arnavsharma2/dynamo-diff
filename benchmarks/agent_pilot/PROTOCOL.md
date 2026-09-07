# Diagnostic agent pilot protocol

This is a small local pilot, not a claim about all agents, real-world developer productivity or application performance. It uses ten fresh held-out questions, three representations and two repetitions: **60 trials** in randomized order. Evaluation model outputs have not informed the questions or answer key. Human review of the answer key and semantic scoring is pending.

## Model and fixed resources

- Ollama **0.33.2**, installed `qwen3:8b`, Q4_K_M, 8.2B parameters.
- Model manifest digest: `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Local HTTP endpoint only: `127.0.0.1:11434`. No hosted API, paid calls or model downloads.
- `think=false`, temperature 0.2, top_k 20, top_p 0.95, repeat_penalty 1; context 40,960 tokens. Seeds 731 and 732 are paired across conditions for repetitions 1 and 2.
- Each trial: at most 12 tool calls, 4,096 generated tokens across model requests, 60,000 characters of tool results, and 600 seconds elapsed. Each model request generates at most 1,024 tokens, and one tool result can be at most 12,000 characters. Limits and exhausted-budget failures are retained.
- A separate generic lookup preflight tests native tool calling and warms the model; no held-out question is used. Trial order is shuffled with Python random seed 917029 and retained before execution. No conversations are shared across trials.

## Held-out corpus and access

`generate.py` authored fourteen new process captures after the implementation was recorded in `corpus/implementation-freeze.json`. Questions cover new numerical/string inputs and combinations of the supported semantics. These are held-out instances of the tool's intended cases, not a claim of generalization to unseen compiler versions or arbitrary production workloads. Question q07 is an explicitly curated clean truncation of a fresh process trace; the raw prefix is reconverted by tlparse. Original recordings remain available to reviewers.

Every condition receives the same question, output fields, general event semantics, workload manifests and captured source. Filenames exposed to the agent use neutral question/capture labels. Answer keys, curator files, independent backend-count observations, other questions, repository implementation, internet and shell execution are inaccessible to the evaluation agent.

The shared tools list files, read bounded ranges and search literal text in the allowed files. They support pagination, offsets and explicit truncation. A tool result carries a retrieval ID so citations can be checked against exactly what the agent saw.

| Condition | Additional accessible evidence |
|---|---|
| Raw | Original structured process trace, including metadata prefixes and multiline payloads. |
| tlparse text | Output of tlparse 0.4.3 `--plain-text`: metadata JSONL, payload text/JSON, artifact directory and readable text extracted from its HTML tables. The generic HTML-to-text renderer removes style/script content and preserves link destinations; it does not infer compiler events or counts. Original raw.log is also present in the converter output. |
| Dynamo Diff | The actual local MCP server's `import_trace`, `compare_runs` and `get_evidence` tools. Evidence index mode exposes records omitted from compact comparisons. Original payload excerpts are available through the MCP tool. |

The representation and its navigation interface are the intervention. Raw/tlparse agents get direct file/search access rather than receiving a preselected excerpt; Dynamo Diff gets its real analysis tools. Invocation, output and generation budgets are identical. Native tool schemas necessarily differ between a file corpus and the analyzer; results cannot isolate formatting from the analysis/navigation interface.

## Measurements and scoring

Retain every model response, tool call, returned excerpt, refusal, error, budget stop and final answer. Record wall-clock elapsed time, inference timing reported by Ollama, input/output token counters, cached-input counters when available, retrieved characters and tool calls. Sum the reported prompt-token counts across requests, including repeated conversation context; do not present that as the count of unique source tokens. Timings use a warm local model and unflushed OS/model caches with randomized order. They include tool overhead; model load timing is separately retained.

The requested final JSON contains an answer object, short explanation and citations to retrieved evidence. Score structured fields against the separately authored key; report both all-fields-correct question accuracy and field accuracy. Count affirmative unsupported performance/source-causality assertions among the explicit claim fields. Verbatim citation checks verify the retrieval ID and quoted text; they do not by themselves establish that a quote supports the associated interpretation.

Human review is required for the key, explanatory correctness, semantic evidence support and unsupported prose claims. Until that review exists, any automatic scores are **provisional** and the study does not satisfy the final reviewed-evaluation gate. Publish individual results and failures, condition aggregates, paired question/repetition differences and small-sample limitations. If there is no measured improvement, report that outcome and revise the product without rewriting this run.

Freeze the protocol, questions, key, harness, exposed corpus hashes, exact model identity and core source hashes in the run receipt before the first trial. A changed run uses a new output directory; resume only missing trials under an identical receipt. Interrupted/failed attempts are retained rather than silently replaced with successful reruns.

The API fields and native tool-message format follow the official [Ollama chat endpoint](https://docs.ollama.com/api/chat) and [tool-calling guide](https://docs.ollama.com/capabilities/tool-calling). This uses the local server's actual returned counters; it does not estimate token savings from character ratios.
