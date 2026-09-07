# Dynamo Diff delivery status

**Portfolio v1 completed September 7, 2026**, against the [approved scope](PROJECT_SCOPE.md), including the user's revision making independent human review optional. Reviews remain labeled **AI-reviewed**, and the [original proposal](PROJECT_SCOPE_ORIGINAL.md) is archived. The public repository and [v0.1.0 GitHub release](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0) provide the source, wheel, source archive and VSIX. VS Code extension 0.1.2 is [published on Marketplace](https://marketplace.visualstudio.com/items?itemName=dynamo-diff.dynamo-diff), with validation and public-download checks recorded in its [publication receipt](../artifacts/marketplace-publication-0.1.2.json). PyPI publication and external adoption are unclaimed.

Current evidence: the [input-boundary audit](INPUT_AUDIT.md) found and corrected silent acceptance of conflicting/non-object source maps. The updated installed wheel passes 96 tests, both offline demonstrations and 12 evaluation-harness tests with PyTorch and Transformers absent, locally and in [hosted CI](../artifacts/HOSTED_CI.md) on macOS/Linux. The updated revision also passes ten development/eleven installed-VSIX checks on Linux. Local macOS installed-VSIX checks pass. The CLI displays both baseline and candidate guard categories. The earlier adapter-validation changes have a retained 10 MiB/100 MiB performance rerun. See [verification evidence](../artifacts/VERIFICATION.md).

## Milestones

| Milestone | State | Evidence / next requirement |
|---|---|---|
| Feasibility and differentiation | Verified; pilot completed | Python 3.13.2 / PyTorch 2.14.0 / tlparse 0.4.3 captures; edited-function demo and `FEASIBILITY.md`. The diagnostic pilot found no demonstrated end-to-end agent improvement. |
| Parser and evidence model | Implemented; AI boundary audit recorded | Twelve recorded scenarios plus edit pair, malformed JSON/manifest checks, aggregate limits, bounded source analysis and no-execution checks. The [input audit](INPUT_AUDIT.md) records inspected boundaries, the corrected source-map issue and limits. The [fixture review guide](../fixtures/REVIEW.md) links expectations to direct records. |
| Comparison and CLI | Implemented and verified | Ordinary body edits, shifted IDs, duplicate-source ambiguity, manifest gates, capture/comparison schemas, text/Markdown/JSON. |
| MCP interface | Locally verified | Three tools, real stdio test, bounded retrieval, approved roots and CLI/core parity. Evidence discovery now exposes IDs hidden in compact rows. All 60 frozen pilot attempts finished; strict response-format failures prevented a demonstrated end-to-end improvement. |
| VS Code interface | Installed VSIX and native walkthrough verified | Import/compare, native tree, table, captured source/evidence, error paths and actual cancellation pass against the installed package. Baseline/candidate source, comparison table and original guard evidence are visually verified in one editor group. |
| Case studies and evaluation | Real-project case verified; pilot recorded and AI-reviewed | Full Transformers 5.10.1 generate() case, early-init intervention, raw/normalized evidence and independent eager-output checks. Ten fresh held-out questions, fourteen captures and all 60 individual attempts are retained. Provisional primary and explicitly post-hoc results are documented. Human review is optional and unclaimed. |
| Release and demonstration | Portfolio v1 delivered | Current wheel and VSIX pass local and hosted checks; source archive includes case corpus, upstream license texts, revised scope, archived proposal, release notes and the recorded CLI demo. Native visual inspection is complete. |

## Acceptance ledger

- [x] Exact toolchain versions and reproducible dependency locks for the tested Python 3.13 setup.
- [x] Recorded original traces, converted bundles, manifests and source snapshots.
- [x] Fixture expectations justified by original compiler evidence and independent backend observations; explanations are AI-reviewed, with optional human review.
- [x] Stable repeated inputs and A→B→A specialization/reuse.
- [x] Dynamic-shape generalization and Python scalar specialization.
- [x] Grad/type/identity cases and multiple guard reasons per event; additional modes remain outside the recorded examples.
- [x] Graph breaks/resume regions and internal attempts.
- [x] Backend failures, no-graph outcomes and limits; missing explicit fallback records stay unclaimed.
- [x] Multiple module instances sharing a code object.
- [x] Line shifts, changed frame IDs, ordinary body edits and ambiguous source matches; duplicate-source ambiguity has a labeled synthetic robustness case.
- [x] Truncated/malformed/missing/unsupported examples, including clean truncation; input-boundary audit and its limitations recorded.
- [x] Duplicate imports and rejection of mixed-process identities.
- [x] Space-containing paths and escaped-root/symlink rejection.
- [x] Unsupported compiled-autograd/multi-rank examples visibly rejected.
- [x] Separate capture structure, workload completion, comparability and performance conclusions.
- [x] Source snapshots and immutable, content-addressed evidence.
- [x] Explicit input/record/payload/output limits, aggregate context accounting, strict JSON bounds and bounded source analysis/diff.
- [x] Capture/comparison identities include content, adapter/schema, comparison rules and relevant options; invalidation tests pass. Comparisons are recomputed rather than persistently cached.
- [x] CLI import/analyze/compare/evidence/serve-mcp commands, plus source and schema export.
- [x] Versioned capture/comparison JSON schemas, terminal and Markdown output.
- [x] MCP import_trace/compare_runs/get_evidence tools and bounded retrieval.
- [x] CLI/MCP/editor model parity and actual subprocess integration checks on the tested platform.
- [x] VS Code import/compare/results/navigation/cancellation/error handling in the development host.
- [x] Guard/source no-execution code path, explicit side-effect regression and recorded input-boundary code audit.
- [x] Local processing, no telemetry, documented agent source-sharing boundary.
- [x] 10 MiB/100 MiB synthetic scale import benchmarks, peak RSS, warm real-pair comparison latency, output size and separate small-trace conversion costs; individual trials and limitations in `PERFORMANCE.md`.
- [x] Full Transformers generate() before/after investigation with pinned reproduction, raw compiler evidence, independent backend observations and eager-output oracle; explanation is AI-reviewed.
- [x] Held-out agent pilot and all 60 individual results, including failures; AI answer/evidence review and mechanical scoring limits are documented. Optional human review has not occurred.
- [x] Local wheel/sdist and VSIX; installed-wheel suite and both demonstrations without ML runtimes; installed-VSIX integration checks. The original development receipt is retained separately from the public-release build receipt.
- [x] Hosted macOS/Linux core and Linux installed-editor CI; license/attribution, architecture/semantics/compatibility/capture/release docs.
- [x] Native visual inspection of imports, comparison table, both captured source snapshots and original evidence in the approved demo profile.
- [x] Requirement-by-requirement audit completed in `COMPLETION_AUDIT.md`; remaining limitations and optional follow-ups are explicit.

Human review and external user feedback must be recorded honestly. No human review or external usage is claimed. The negative pilot result and frozen historical protocol remain unchanged by the delivery-policy revision.

## Delivery and optional follow-ups

No required portfolio-v1 implementation or review gate remains open under the approved scope. The [requirement audit](COMPLETION_AUDIT.md) maps requirements to evidence. The [portfolio delivery receipt](../artifacts/portfolio-v1-delivery.json) identifies the earlier development artifacts and validation. The [public release](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0) supplies a separate build receipt and checksums for its rebuilt packages. Both source snapshots, the rendered comparison table and original guard evidence are visually verified. The [recorded example](DEMO.md) can be inspected locally. [Installation instructions](INSTALL.md) cover the release downloads. The [public-release review](PUBLIC_RELEASE.md) describes publication checks; [hosted CI evidence](../artifacts/HOSTED_CI.md) preserves the development checkpoints.

Independent human review is an optional follow-up. The [60-trial pilot](../benchmarks/agent_pilot/README.md) shows no demonstrated end-to-end improvement. Post-hoc formatting sensitivity does not replace the primary result. No paid model usage was incurred. Demand-validation targets remain unclaimed; no outreach has been sent.
