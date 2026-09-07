# Verification checkpoint

This records local evidence, not a release-completion claim. Raw compiler fixtures and their expected counts are separate from these test receipts.

## Python wheel

The wheel was built with `python -m build --no-isolation` and reinstalled with `--no-deps --force-reinstall` into the separate environment under `.cache/clean-env`, which was created from the hashed `requirements-test.lock`. The release-check script confirms the package comes from that environment's site-packages and that neither PyTorch nor Transformers is installed.

```sh
.cache/clean-env/bin/python tools/check_release.py --require-wheel --junit artifacts/wheel-tests.xml
```

**91 passed in 3.53 seconds.** The final September 7 wheel refresh includes paginated MCP evidence discovery and the post-pilot import navigation hints. The MCP test follows the returned evidence action. The empty pytest `pythonpath` override prevents the repository setting from substituting editable source for the installed wheel. Tests include real CLI and MCP stdio subprocesses, controlled and real-project captures, immutable evidence, source matching, malformed JSON/nested manifests, resource limits, invalidation and explicit no-execution input. Committed capture/comparison schemas match the installed package. All installed Python source files match the wheel and the current checkout.

Both `tools/demo.py` and `case_studies/transformers_cache/verify.py` passed against that wheel without ML runtimes or a network connection. `wheel-demo.json` retains the authored-edit report.

The separate evaluation-harness command, `python -m pytest -q -o pythonpath= --import-mode=importlib benchmarks/agent_pilot`, passed **12 tests in 1.06 seconds**. This validates runner boundaries and scoring behavior without making model calls. Its JUnit result is `pilot-harness-tests.xml`.

## New compiler reproduction

`python tools/generate_edit_pair.py --output .cache/regenerated-edit-pair` executed the authored before/after workloads again under the pinned fixture environment and converted both new logs. Backend invocations were 3 and 2 respectively. `tools/demo.py --captures .cache/regenerated-edit-pair` verified the expected function match, completed/recompile counts and retained unmatched helper. Original fixture output was not overwritten.

## VS Code

`editor-integration.json` records nine passed integration checks on VS Code **1.132.1**, macOS. The suite used a temporary workspace with spaces in its path, separate user data/extensions/store, and the installed Python interpreter. It checked full CLI/editor report equality, native tree contents, separate captured source views, line navigation, read-only user typing, evidence provenance, escaped table labels, error recovery and actual child-process termination on cancellation.

The first restricted GUI launch aborted in macOS application registration before extension activation. A normal desktop-permission launch succeeded. Two test assertions were corrected to match the actual API: virtual documents restrict user typing while extension API buffer edits are separate; the missing report error is `missing_artifact`. The final run exited 0. The user's normal VS Code process was not terminated.

`installed-editor-integration.json` records **ten passed checks against the installed VSIX**, using the clean-wheel Python interpreter. The VS Code CLI installed the package into a temporary extensions directory. A separate test-driver extension launches the suite; no development copy of Dynamo Diff can shadow the installed package. The suite verifies the actual loaded extension path and JavaScript digest before running the same report/source/evidence/error/cancellation checks. The final host exits 0. The six-entry VSIX excludes tests, caches and node_modules. The subsequent MCP-only changes do not alter the extension or its CLI path; the tested VSIX hash is unchanged.

The user approved installation of the same VSIX in a persistent `Dynamo Diff Demo` profile. The CLI confirms `dynamo-diff.dynamo-diff@0.1.0`. Both authored captures imported successfully through the native UI: baseline three completed/two confirmed recompilations; candidate two completed/zero confirmed recompilations in total. A demo setup mistake initially resolved the virtual environment executable's symlink to base Python, producing `ModuleNotFoundError`. Correcting the workspace setting to preserve the virtual environment path fixed import. No extension code change was needed.

Visual acceptance remains pending. Native control returned stale states, `noWindowsAvailable`, `elementHasNoFrame` and a ScreenCaptureKit stream error before a verified comparison-table walkthrough. A later read-only inspection again failed to start the screen-capture stream. The demo workspace uses VS Code's built-in file picker; this is a local demo setting. These automation failures are not evidence of another VS Code crash.

## Real-project investigation

`case_studies/transformers_cache` retains an authored CPU reproduction through unmodified Transformers 5.10.1 `generate()`. Backend totals after three identical requests are **2 → 3 → 3** with lazy initialization and **2 → 2 → 2** with early initialization. Raw terminal records support three versus two completed compilations; explicit recompile artifacts support two versus one successful recompilations. The removed event has both a cached shape rejection and a cache-initialization guard reason.

Each request passes exact token and per-step logit checks against a separate uncompiled model with identical weights. The before/after weights, tokens and logits also agree. `transformers-case.json` records offline evidence verification and the current comparison. The guide explains the CPU compile test switch, recording backend, preserved prefill/decode specialization and absence of any application-speed claim. Expected explanations have not received human review.

## Diagnostic pilot and demonstration

All 60 planned local-model attempts finished. [Primary results](../benchmarks/agent_pilot/README.md) show no demonstrated end-to-end improvement: every Dynamo Diff final response failed the required complete-JSON format. Lower tokens or time for those failures are not productivity evidence. All original outputs, individual scores, frozen evaluated code and explicitly post-hoc format-sensitivity results are retained. Human answer-key and semantic review remain pending. The later MCP navigation hints have transport coverage but no measured model-performance result.

The [CLI walkthrough](../docs/DEMO.md) records five successful actual commands, including original evidence retrieval. `demo/cli-002/receipt.json` retains output and hashes; the recording includes intentional presentation pauses. The in-conversation preview's Next/Previous controls, final-step boundary, command disclosure and narrow-width wrapping were checked in the browser. This is not native editor visual acceptance.

## Packaging and open gates

Wheel, source archive and VSIX exist locally. The source archive includes the offline demonstrations, controlled fixtures, real-project captures, exact upstream license texts, completed pilot and recorded CLI demo. The CI workflow is written, action commits verified, and YAML structure checked; it has not executed on GitHub. The artifacts remain development previews pending hosted CI, native visual acceptance and human fixture/case/answer-key/semantic review. The requirement audit records these open gates.

`final-local-checkpoint.json` identifies the current artifacts and test receipts. Earlier `build-receipt.json` and `wheel-profile-checkpoint.json` are historical checkpoints; their hashes describe earlier implementations. No package has been published, no external user validation is claimed, and the original scope remains unchanged.

## Processing benchmark

The separate retained baseline measured 10 MiB/100 MiB synthetic inputs in three fresh import processes each, and the real edit pair in 20 warm comparisons. All generated-input count checks passed. `docs/PERFORMANCE.md` documents measured time, process peak RSS, output size, cache assumptions, separate tlparse conversion costs and investigation thresholds. Hardware was verified as an Apple M1 Pro, 32 GiB RAM, MacBookPro18,3. This provides tool-processing evidence; it does not measure agent diagnosis quality or application speed.

After the revision-4 validation changes, the same procedure measured **1.349 s / 13.466 s** median imports for 10 MiB / 100 MiB, about 42% above the original baseline. Peak RSS was **58.8 / 254.7 MiB**. `benchmarks/check_regression.py` reports `within_thresholds` against the unchanged earlier thresholds. Both sets of individual measurements are retained.
