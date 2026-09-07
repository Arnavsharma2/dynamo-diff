# Investigating a warm-request recompile in Transformers

Early initialization of a static KV cache removes one completed recompilation in this recorded CPU investigation of the real Transformers `generate()` path. The candidate still compiles separately for prefill and decoding. All three requests on both sides produce the same tokens and per-step logits as a separate eager model with identical weights. Application speed was not measured.

## Public origin and scope

[Transformers issue #46421](https://github.com/huggingface/transformers/issues/46421), opened June 4, 2026, reports a second-request recompilation when chunked prefill encounters lazy cache initialization. It suggests initializing the cache before entering the compiled region. The issue links the author's [generation investigation](https://github.com/dacorvo/transformers-generation-compile/blob/main/README.md). The issue is closed when checked September 6, 2026; this case does not claim to discover a new upstream bug or supply its upstream fix.

The workload here was authored for Dynamo Diff. It uses unmodified Transformers **5.10.1**, PyTorch **2.14.0**, tlparse **0.4.3**, and Python **3.13.2**. A small randomly initialized Llama model exercises the library's actual generation, chunked-prefill, attention and static-cache code. No pretrained model, tokenizer, network request, CUDA device or paid service is needed.

The CPU adaptation explicitly enables Transformers' `_compile_all_devices` test switch. Its backend records FX graph invocations and returns `graph.forward`; it does not run Inductor. These changes make the compiler behavior reproducible on the tested Apple M1 Pro / 32 GiB Mac. They do not reproduce the original report's GPU timings, workload size or production backend.

## Controlled change

The two subprocesses execute the same authored driver path. The only driver source change is this preparation before generation:

```python
cache.early_initialization(1, 2, 8, torch.float32, torch.device('cpu'))
```

The baseline allows lazy initialization. Both runs use a two-layer, 22,688-parameter Llama; 32 hidden dimensions; four query heads and two KV heads; CPU float32; greedy generation of three new tokens; the same eight input tokens; prefill chunk size eight; static cache capacity sixteen; and three identical requests. The cache is reset between requests. Each variant starts in a fresh process. Compilation uses `fullgraph=True`, `dynamic=False`, and the recording backend. No persistent Inductor cache is involved. Both manifests retain ordered inputs, settings, model configuration, parameter hashes, source snapshots and finalization hashes.

| Recorded observation | Lazy baseline | Early-init candidate |
|---|---:|---:|
| Backend totals after requests 1, 2, 3 | 2, 3, 3 | 2, 2, 2 |
| Completed compilation identities | 3 | 2 |
| Confirmed successful recompilations | 2 | 1 |
| Recorded guard-reason entries | 3 | 1 |
| Failed / no-graph / unknown outcomes | 0 / 0 / 0 | 0 / 0 / 0 |
| Graph-break records / limit events / fallback reports | 0 / 0 / 0 | 0 / 0 / 0 |
| Maximum logit error against eager, all requests | 0 | 0 |

The backend totals are an independent check for this full-graph workload. Backend invocations are not a general substitute for Dynamo event identities.

## Reading the evidence

The traced root is the decorator `can_return_tuple.wrapper` in the captured `transformers/utils/generic.py`, line 897. Its graph includes Llama forward execution. Dynamo Diff preserves this traced attribution and matches the unchanged wrapper by its unique source structure. The edited initialization is in the caller, outside that compiled wrapper; the tool does not claim that the wrapper's body changed.

In the baseline, terminal records **89, 188 and 288** in [raw.jsonl](captures/baseline/report/raw.jsonl) each report guarded code, a positive graph-op count and no failure. Recompile artifacts at records **90 and 189** explicitly belong to frame compilations `0/1` and `0/2`.

The first recompilation specializes from an eight-token prefill to a one-token decode. The next request rejects both cached specializations: the decode specialization has the wrong shape, and the earlier prefill specialization expects an uninitialized cache. These are **two guard reasons attached to one new compilation**, not two recompilations. The full [second recompile payload](captures/baseline/report/-_0_2_0/recompile_reasons_10.json) links the initialization check to `transformers/cache_utils.py:352`.

In the candidate, terminal records **101 and 200** in [raw.jsonl](captures/candidate/report/raw.jsonl) establish two completed compilations. Record **102** supplies the remaining prefill-to-decode shape reason. There is no new compiler invocation on the second or third request and no recorded initialization reason.

[comparison.json](comparison.json) preserves the complete machine-readable result. Baseline evidence `payload-189:reason-1` identifies the initialization reason; its artifact hash and record location survive import. `manifest_consistent` means the declared workloads and observed compiler configurations agree. It does not prove arbitrary runtime equivalence. In this case the separate output oracle adds specific numerical evidence.

## Inspect the retained case

From the repository root, an environment with the core package installed can run:

```sh
python case_studies/transformers_cache/verify.py
```

This requires neither PyTorch nor Transformers. It checks retained hashes, raw terminal evidence, reason associations, the independently recorded backend counts, eager-output results and Dynamo Diff's comparison. It uses a temporary store and leaves the original bundles unchanged. [expected.json](expected.json) contains the separately authored expected counts and evidence locations. **Human explanation review remains pending**; automated verification is not that review.

To retain a report or inspect evidence interactively:

```sh
python case_studies/transformers_cache/verify.py --output artifacts/transformers-case.json
dynamo-diff --store .cache/case-demo import case_studies/transformers_cache/captures/baseline/report --manifest case_studies/transformers_cache/captures/baseline/manifest.json
dynamo-diff --store .cache/case-demo import case_studies/transformers_cache/captures/candidate/report --manifest case_studies/transformers_cache/captures/candidate/manifest.json
```

Use the returned IDs with `compare` or `evidence`; IDs may change with adapter versions. The CLI, MCP server and editor consume the same comparison model.

## Regenerate the actual workload

The dependency lock targets the tested Python 3.13 environment. Create a separate environment, install the lock and package, then capture into a new directory:

```sh
python3.13 -m venv .case-venv
.case-venv/bin/python -m pip install --require-hashes -r requirements-case-study.lock
.case-venv/bin/python -m pip install --no-deps -e .
.case-venv/bin/python case_studies/transformers_cache/reproduce.py --output .cache/transformers-reproduction
.case-venv/bin/python case_studies/transformers_cache/verify.py --captures .cache/transformers-reproduction
```

Only dependency installation needs network access. The capture driver sets Hugging Face offline options, snapshots installed source and refuses to overwrite existing baseline/candidate bundles. The script checks numerical outputs before declaring each run complete. Different platforms or dependency versions can change compiler behavior; they need their own validation rather than an assumed match to these counts.

## What this case establishes

The retained pair demonstrates a real library investigation: one source preparation removes a warm-request compilation associated with cache initialization while retaining normal shape specialization and checked outputs. It also tests whether an analyzer mistakenly counts several rejected specializations as several recompilations.

It establishes no end-to-end latency, throughput, GPU-memory saving, general correctness guarantee, upstream novelty or adoption claim. The pilot evaluation must still determine whether this organization of evidence helps agents diagnose held-out cases.

Original drivers are under the repository MIT license. Captured upstream source retains its original headers; see [third-party notices](../../docs/THIRD_PARTY_NOTICES.md).
