# Input and evidence boundary audit

September 7, 2026. Codex reviewed the current CLI, adapter, manifest validation, comparison, store, MCP transport and extension code against the original scope's saved-input, conservative-matching and no-execution requirements. This is an AI code/evidence audit, not an independent human review or a guarantee against every possible attack.

## Finding corrected

A CLI source-map file could repeat a baseline function key with conflicting candidate IDs. Python's default JSON decoder kept the final value, allowing an explicitly labeled match from `compute` to the unrelated added `helper`. An empty array was also silently treated as an absent mapping by the core's truthiness default.

The CLI now uses the existing strict JSON decoder, rejects duplicate keys and excessive nesting with `invalid_source_map`, and requires an object. The core treats only `None` as an omitted mapping and retains its existing string-ID and one-to-one correspondence validation. Valid mappings and report identities are unchanged.

The [before-fix regression log](../artifacts/source-map-regression-before.log) retains two failures: conflicting duplicates and a non-object map incorrectly returned successful comparisons. The excessive-nesting case already returned a structured error at the tested depth. After the fix, all three cases and the other comparison checks pass: [18 focused tests](../artifacts/source-map-regression-after.xml). The [installed-wheel release check](../artifacts/wheel-source-map-check.log) passes 96 tests and both offline demonstrations with no ML runtimes; [12 evaluation-harness checks](../artifacts/pilot-source-map-tests.xml) pass without model calls.

## Boundaries inspected

| Requirement | Implementation and behavioral evidence |
|---|---|
| Embedded data is not executed | The adapter uses JSON decoding, text matching and `ast.parse`/`ast.dump`; source snapshots are never imported. `test_import_never_executes_guard_or_source_python` supplies actual Python side-effect expressions, retrieves their unchanged text, and verifies the marker file is absent. |
| Imported paths stay within declared roots | `within()` rejects absolute paths, parent traversal, NULs and resolved symlinks outside the root. MCP validates report and manifest paths against configured roots. Escape, symlink, invalid-ID and space-containing-path cases are retained in the store/MCP/input suites. |
| Imported artifacts survive original-file changes | Imports copy regular-file contents into a temporary bundle, check copied hashes, then rename it into the content-addressed store. Tests delete the original bundle and still retrieve identical evidence/source; changing stored evidence, source or normalized metadata is detected. |
| Special files and conflicting destinations are handled | File hashing/text reads require regular files. The FIFO payload test completes with a visible missing-payload notice. Reserved manifest paths cannot overwrite imported source; conflicting content for one imported path is rejected. |
| Resource limits cover the actual bundle | Metadata is read incrementally with byte/record limits. Payloads, untraced snapshots, original traces and manifests count toward aggregate import size. AST size and source-diff work are bounded; missing correspondence remains ambiguous. Tests exercise these boundaries and option-dependent identities. |
| Malformed content cannot silently establish supported success | Strict JSON rejects duplicate keys, non-finite values, invalid Unicode and excessive nesting. Invalid records remain partial evidence; malformed manifests are rejected. Graph-output, terminal, missing-payload, version and clean-truncation cases exercise the outcome/completeness distinction. |
| Matching is conservative | Exact unique structure or verified source-diff boundaries support automatic matches. Duplicate identities and unsupported source mappings stay ambiguous or fail explicitly. The corrected CLI regression covers conflicting explicit declarations. |
| Interfaces preserve data and execution boundaries | CLI failures use structured codes. MCP has bounded/paginated responses and labels retrieved prose as untrusted. The extension uses `execFile` arguments, checks workspace trust, limits subprocess output/time, propagates cancellation, and displays immutable virtual documents. Native Markdown table labels are escaped. |

## Practical limits

The caller controls its own local store and configured interpreter. This review does not claim protection against a concurrent malicious local process replacing files between filesystem checks and reads, nor authenticity of producer declarations. Hashes detect changes relative to the stored fingerprint; they are not a producer signature. Only the recorded producer/runtime combinations are tested. Operational size limits and retained processing benchmarks do not establish a universal memory or latency bound for every adversarial arrangement of records.

The source-map correction changes validation of malformed input; it does not change valid-capture normalization or the recorded pilot's evaluated code. The completed pilot and its negative primary result remain intact. The user subsequently made independent human fixture/case/evaluation review optional in the [approved scope revision](PROJECT_SCOPE.md#approved-review-policy-revision--september-7-2026). This audit remains AI-reviewed; human review has not occurred.
