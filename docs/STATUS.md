# Dynamo Diff delivery status

Implementation started September 6, 2026. The original scope remains the acceptance contract. This is an implementation checkpoint, **not a completed release**.

Current evidence: the [input-boundary audit](INPUT_AUDIT.md) found and corrected silent acceptance of conflicting/non-object source maps. The updated installed wheel passes 96 tests, both offline demonstrations and 12 evaluation-harness tests with PyTorch and Transformers absent. The preceding revision's [hosted CI](../artifacts/HOSTED_CI.md) passes 93 core tests on macOS/Linux and ten development/eleven installed-VSIX checks on Linux. Local macOS installed-VSIX checks also pass. The CLI displays both baseline and candidate guard categories. The earlier adapter-validation changes have a retained 10 MiB/100 MiB performance rerun. See [verification evidence](../artifacts/VERIFICATION.md).

## Milestones

| Milestone | State | Evidence / next requirement |
|---|---|---|
| Feasibility and differentiation | Initial gate verified | Python 3.13.2 / PyTorch 2.14.0 / tlparse 0.4.3 captures; edited-function demo and `FEASIBILITY.md`. Diagnostic value study still pending. |
| Parser and evidence model | Implemented; boundary audit recorded | Twelve recorded scenarios plus edit pair, malformed JSON/manifest checks, aggregate limits, bounded source analysis and no-execution checks. The [input audit](INPUT_AUDIT.md) records inspected boundaries, the corrected source-map issue and limits. The [fixture review guide](../fixtures/REVIEW.md) links expectations to direct records. Human review remains. |
| Comparison and CLI | Implemented; release audit open | Ordinary body edits, shifted IDs, duplicate-source ambiguity, manifest gates, capture/comparison schemas, text/Markdown/JSON. |
| MCP interface | Locally verified | Three tools, real stdio test, bounded retrieval, approved roots and CLI/core parity. Evidence discovery now exposes IDs hidden in compact rows. All 60 frozen pilot attempts finished; strict response-format failures prevented a demonstrated end-to-end improvement. |
| VS Code interface | Installed VSIX verified | Import/compare, native tree, table, captured source/evidence, error paths and actual cancellation pass against the installed package. Visual review remains. |
| Case studies and evaluation | Real-project case verified; pilot recorded | Full Transformers 5.10.1 generate() case, early-init intervention, raw/normalized evidence and independent eager-output checks. Ten fresh held-out questions, fourteen captures and all 60 individual attempts are retained. Provisional primary and explicitly post-hoc results are documented; human review remains. |
| Release and demonstration | Private repository and hosted CI verified; review gates open | Current wheel and VSIX pass local and hosted checks; source archive includes case corpus, upstream license texts and the recorded CLI demo. Native visual acceptance and required human review remain. |

## Acceptance ledger

- [x] Exact toolchain versions and reproducible dependency locks for the tested Python 3.13 setup.
- [x] Recorded original traces, converted bundles, manifests and source snapshots.
- [ ] Independent fixture expectations justified by compiler evidence.
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
- [x] Full Transformers generate() before/after investigation with pinned reproduction, raw compiler evidence, independent backend observations and eager-output oracle. Human explanation review remains separate.
- [x] Held-out agent pilot and all 60 individual results, including failures; human key and semantic review remain pending.
- [x] Local wheel/sdist and VSIX; installed-wheel suite and both demonstrations without ML runtimes; installed-VSIX integration checks. These are development artifacts, not a published release.
- [x] Hosted macOS/Linux core and Linux installed-editor CI; license/attribution, architecture/semantics/compatibility/capture/release docs. Human review remains separate.
- [x] Requirement-by-requirement audit recorded in `COMPLETION_AUDIT.md`; unresolved gates remain explicit.

Human review of expected fixture explanations and external user feedback must be recorded honestly. No human review, external usage, or benchmark outcome is implied by generated files or tests.

## Next work in the unchanged scope

1. Complete human key and semantic review of the [recorded 60-trial pilot](../benchmarks/agent_pilot/README.md). The strict result shows no demonstrated end-to-end improvement. An explicitly post-hoc answer-member analysis describes formatting sensitivity; it does not replace the primary result. No paid model usage was incurred.
2. Finish native editor visual verification once desktop automation provides consistent current state. The September 7 retry recovered the comparison tree and invoked table/source navigation, but accessibility content and screenshots remained stale and conflicting. The updated profile's final layout and source/evidence walkthrough remain open. The corrected [CLI demonstration](DEMO.md) is recorded and reproducible. The private repository is uploaded and [hosted CI passed](../artifacts/HOSTED_CI.md).
3. Obtain the required human review of fixture explanations, case study and pilot answer keys, then close the remaining items in the [requirement audit](COMPLETION_AUDIT.md). Human review has not occurred. Demand-validation targets remain unclaimed; no outreach has been sent.
