# Supported compiler-event semantics

Verified against PyTorch **2.14.0**, source commit `08187d9e0fba026dc8217405802ab5381dc88d90`, and tlparse **0.4.3**. The recorded cases use Python 3.13.2 on macOS arm64 and a CPU backend returning the FX graph's forward function. These are Dynamo tests, not CUDA/Inductor performance tests.

## Adapter boundary

The adapter reads tlparse's `raw.jsonl`, beginning with a string table, followed by metadata records with optional `payload_filename` references. tlparse 0.4.3 has this export; building the newer development revision was unnecessary. It retains the `create_symbol` record even though its renderer calls that record unknown.

The `recompile_reasons` artifact is marked JSON upstream. In the tested export, one reason is written as unquoted text; multiple reasons are a JSON list. The adapter recognizes exactly those representations. It never evaluates guard expressions.

## Counting rules and evidence

Compilation identities are local to a capture, rank, frame ID, and frame-compile ID. Attempts are nested beneath that identity. The `graph_break` fixture has two compilation identities and three attempts. Counting attempts would overstate compiled regions.

Terminal `compilation_metrics.recompile_reason` and the supported `recompile_reasons` artifact provide explicit recompile evidence. The `multiple_guards` fixture has three successful compilation identities, two confirmed successful recompilations, and three recorded reason entries. Its last compilation rejects two earlier variants; those are not two additional compilations.

`identity_partitioned` sets the module's supported internal static-specialization override for this controlled test. It produces frame-compile IDs 0, 1, and 2, with accumulated cache sizes 0, 1, and 2, while each identity-specific cache size remains 0 and `recompile_reason` remains null. There are three compiled variants and no confirmed recompilations. In contrast, `identity` exercises an ordinary object-identity guard and records two recompilations. This demonstrates why the classifier must follow explicit compiler evidence rather than numeric IDs or the presence of an identity guard alone.

`has_guarded_code` is insufficient for successful graph compilation. In this PyTorch version the local variable can hold a `ConvertFrameReturn` describing a skipped frame. The `no_graph` fixture records `has_guarded_code=true`, no graph operations, and zero backend invocations. The analyzer reports **no graph observed**, without claiming to recover an absent skip reason.

A completed outcome requires supported terminal success evidence, positive graph-operation count, and a graph-output record. Backend failures remain failures even if a graph was emitted. Incomplete outcomes remain unknown. Duplicate terminal records make an outcome unresolved.

The limit fixture records two successful compiled variants followed by an unsuccessful attempt with a recompilation-limit error. A subsequent workload call executes without another backend invocation. The analyzer reports the explicit limit and failure; it does not invent a separate fallback log record where the export did not contain one.

Durations retain the original `dynamo_cumulative_compile_time_us` metric name. No subphase durations are added to it and it is never presented as application runtime saved.

## Source correspondence

Source snapshots are parsed with Python's AST parser, never imported. Qualified names distinguish methods in different classes. An exact function-structure hash supports unique unchanged matches; otherwise a source diff must map the function boundary between verified snapshots. This establishes source correspondence, not semantic equivalence.

`edit_before` and `edit_after` contain actual different source files executed at the same captured path. The candidate removes a redundant branch and adds a separately compiled helper, changing the target's run-local frame ID. The comparator matches `compute` by its source boundary and reports the helper as unmatched. The ordered tensor/step inputs to `compute` stay identical; the helper is a deliberate source addition, not a hidden workload-input change.

Without sufficient snapshot evidence, source-location matches remain ambiguous. Explicit mappings are permitted and labeled. Generated resume regions with changed snapshots remain unresolved because splitting/merging them is outside v1's matching contract.

Explicit source-map files must be JSON objects with unique baseline keys and one-to-one existing function IDs. Conflicting duplicate keys are rejected rather than silently accepting the last candidate. Invalid shapes and excessive nesting return a structured `invalid_source_map` error.

## Completeness and comparability

Parsing a valid file does not prove a complete workload. Imported finalization metadata must identify the source trace hashes, successful process/converter exit codes, and the exact converted report hash. The result is labeled **declared completed**, not independently observed completion. Missing metadata stays unknown; a changed report with a stale finalization hash is rejected.

Manifest consistency is a comparison of declarations, not proof of identical execution. Ordered calls, relevant compiler settings, versions, and cache policy are checked. Hashes of actual compiler configurations in the metrics are also compared, so equal manifests cannot silently hide an observed setting change.

## Review status

Expected fixture counts in `fixtures/expected.json` were written from direct inspection of compiler records and the independent instrumented backend, then checked against the adapter. They have been reviewed by Codex. **Human review is pending.** The held-out agent evaluation must not reuse these fixture names as diagnostic answers.

Upstream references: [cache-size semantics](https://github.com/pytorch/pytorch/blob/v2.14.0/torch/_dynamo/cache_size.py), [frame conversion and metrics](https://github.com/pytorch/pytorch/blob/v2.14.0/torch/_dynamo/convert_frame.py), [guard emitter](https://github.com/pytorch/pytorch/blob/v2.14.0/torch/_dynamo/guards.py), [tlparse](https://github.com/meta-pytorch/tlparse).
