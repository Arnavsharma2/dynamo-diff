# Verification checkpoint

This records local and hosted evidence, not a release-completion claim. Raw compiler fixtures and their expected counts are separate from these test receipts.

## Latest input-audit revision

The [input-boundary audit](../docs/INPUT_AUDIT.md) found that duplicate source-map keys could silently select the wrong function and an empty array could silently become an omitted mapping. Both regressions failed before the correction. The updated CLI/core reject malformed maps with `invalid_source_map`; 18 focused comparison checks pass. The rebuilt installed wheel passes **96 tests in 5.25 seconds** and both offline demonstrations with PyTorch/Transformers absent, recorded in `wheel-source-map-check.log` and `wheel-source-map-tests.xml`. Twelve evaluation-harness checks also pass. [The source-map checkpoint](source-map-checkpoint.json) records the current package hashes and verified installed/source-archive payloads. This supersedes the earlier wheel's source identity and test count below; the extension code and VSIX are unchanged.

The [hosted source-map run](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34147070929) also passed: 96 installed-wheel tests and twelve evaluation-harness tests on macOS/Linux, both offline demonstrations, and ten/eleven Linux development/installed-VSIX checks. [HOSTED_CI.md](HOSTED_CI.md) links the retained log and status receipt for exact commit `813b7f8407175c14ffb666eb4c0af1aa541a03d5`.

Native automation briefly recovered a current screenshot of the updated profile's baseline source: `compute` at line 9, its original scalar-dependent branch and `VARIANT = "before"`, in one editor group. This verifies baseline source navigation and its layout. Subsequent stream errors and stale tree updates still prevent final acceptance of the candidate/evidence/table walkthrough; no complete native visual sign-off is claimed.

The next follow-up visually verified the rendered comparison table in that same group: valid/declared-completed captures, completed totals 3 → 2, confirmed recompiles 2 → 0, `compute` matched with `python_scalar` only on the baseline, the unmatched helper, and the explicit unmeasured-performance limitation. Table layout is accepted for the observed window size. A subsequent evidence action changed the title to `payload-10-0.txt`, but AX content and screenshots stayed on the previous table. Candidate source and original-evidence visual acceptance remain open; automated installed-extension navigation checks pass.

## Python wheel

The wheel was built with `python -m build --no-isolation` and reinstalled with `--no-deps --force-reinstall` into the separate environment under `.cache/clean-env`, which was created from the hashed `requirements-test.lock`. The release-check script confirms the package comes from that environment's site-packages and that neither PyTorch nor Transformers is installed.

```sh
.cache/clean-env/bin/python tools/check_release.py --require-wheel --junit artifacts/wheel-tests.xml
```

**93 passed in 4.15 seconds.** The September 7 wheel refresh includes paginated MCP evidence discovery, post-pilot import navigation hints and the baseline/candidate guard-display correction. The MCP test follows the returned evidence action. Two CLI regressions failed before the display fix; text and Markdown now show guard categories in both comparison directions, including `python_scalar → none recorded`, and distinguish an absent function. The empty pytest `pythonpath` override prevents the repository setting from substituting editable source for the installed wheel. Tests include real CLI and MCP stdio subprocesses, controlled and real-project captures, immutable evidence, source matching, malformed JSON/nested manifests, resource limits, invalidation and explicit no-execution input. Committed capture/comparison schemas match the installed package. All installed Python source files match the wheel and the current checkout.

Both `tools/demo.py` and `case_studies/transformers_cache/verify.py` passed against that wheel without ML runtimes or a network connection. `wheel-demo.json` retains the authored-edit report.

The separate evaluation-harness command, `python -m pytest -q -o pythonpath= --import-mode=importlib benchmarks/agent_pilot`, passed **12 tests in 1.06 seconds**. This validates runner boundaries and scoring behavior without making model calls. Its JUnit result is `pilot-harness-tests.xml`.

## New compiler reproduction

`python tools/generate_edit_pair.py --output .cache/regenerated-edit-pair` executed the authored before/after workloads again under the pinned fixture environment and converted both new logs. Backend invocations were 3 and 2 respectively. `tools/demo.py --captures .cache/regenerated-edit-pair` verified the expected function match, completed/recompile counts and retained unmatched helper. Original fixture output was not overwritten.

## VS Code

`editor-integration.json` records ten passed integration checks on VS Code **1.132.1**, macOS. The suite used a temporary workspace with spaces in its path, separate user data/extensions/store, and the installed Python interpreter. It checked full CLI/editor report equality, native tree contents, separate captured source views, line navigation, read-only user typing, evidence provenance, escaped table labels, active-editor-group reuse, rendered-preview activation, error recovery and actual child-process termination on cancellation.

The first restricted GUI launch aborted in macOS application registration before extension activation. A normal desktop-permission launch succeeded. Two test assertions were corrected to match the actual API: virtual documents restrict user typing while extension API buffer edits are separate; the missing report error is `missing_artifact`. The final run exited 0. The user's normal VS Code process was not terminated.

`installed-editor-integration.json` records **eleven passed checks against the rebuilt VSIX**, using the clean-wheel Python interpreter. The VS Code CLI installed the package into a temporary extensions directory. A separate test-driver extension launches the suite; no development copy of Dynamo Diff can shadow the installed package. The suite verifies the actual loaded extension path and JavaScript digest before running the same report/source/evidence/error/cancellation checks. The final host exits 0. The six-entry VSIX excludes tests, caches and node_modules.

The native walkthrough exposed repeated editor splitting. `editor-view-regression-before.log` retains the actual failed assertion: the initial one-column workspace became six columns. Captured views now reuse the active editor group, and the table uses an in-place Markdown preview. The test waits for actual preview-tab activation because the installed built-in Markdown command returns before that asynchronous UI event. The corrected development and installed-extension runs both preserve the original group count and activate a rendered webview. An initial test launch used the obsolete `MacOS/Electron` path and failed before starting; the verified app executable is `MacOS/Code`.

The user approved installation in a persistent `Dynamo Diff Demo` profile. The CLI confirms `dynamo-diff.dynamo-diff@0.1.0`, and the rebuilt tested VSIX was subsequently installed successfully in that profile. Both authored captures imported successfully through the native UI: baseline three completed/two confirmed recompilations; candidate two completed/zero confirmed recompilations in total. A demo setup mistake initially resolved the virtual environment executable's symlink to base Python, producing `ModuleNotFoundError`. Correcting the workspace setting to preserve the virtual environment path fixed import; that setup issue required no extension change.

Native control initially returned stale states, `noWindowsAvailable`, `elementHasNoFrame` and a ScreenCaptureKit stream error. It later recovered enough to select the captures, inspect the expected comparison totals, and inspect the rendered table's validity, event counts, source match and baseline/candidate guard fields through the native accessibility tree. Generated views were closed and the demo window was reloaded after the tested VSIX update. macOS then reported a locked desktop, so visual acceptance of the updated layout and the native source/evidence walkthrough remain pending. The demo workspace uses VS Code's built-in file picker; this is a local demo setting. These automation failures are not evidence of another VS Code crash.

The September 7 follow-up recovered the updated profile's comparison tree with expected totals and one empty editor group. Table and baseline-source actions changed the outer window title to `Preview comparison.md` and then `model.py`, but accessibility content lagged behind those titles and screenshots remained on the earlier empty editor. The native visual gate remains open because those conflicting observations cannot establish the final source/evidence layout. No normal VS Code process was terminated during this retry.

## Hosted CI

After the user approved the private repository upload, [Verify run 34145658752](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34145658752) passed at commit `0fd1053530792a979ec397a1b7f91154b9d4f0d1`. Both macOS and Linux passed 93 installed-wheel tests, both offline demonstrations and 12 evaluation-harness tests. Linux VS Code 1.132.1 passed ten development checks, packaged the VSIX and passed eleven isolated installed-package checks. No CI fixes or model calls were needed. [HOSTED_CI.md](HOSTED_CI.md) links the exact environments, complete log and GitHub status receipt.

## Real-project investigation

`case_studies/transformers_cache` retains an authored CPU reproduction through unmodified Transformers 5.10.1 `generate()`. Backend totals after three identical requests are **2 → 3 → 3** with lazy initialization and **2 → 2 → 2** with early initialization. Raw terminal records support three versus two completed compilations; explicit recompile artifacts support two versus one successful recompilations. The removed event has both a cached shape rejection and a cache-initialization guard reason.

Each request passes exact token and per-step logit checks against a separate uncompiled model with identical weights. The before/after weights, tokens and logits also agree. `transformers-case.json` records offline evidence verification and the current comparison. The guide explains the CPU compile test switch, recording backend, preserved prefill/decode specialization and absence of any application-speed claim. Expected explanations have not received human review.

## Diagnostic pilot and demonstration

All 60 planned local-model attempts finished. [Primary results](../benchmarks/agent_pilot/README.md) show no demonstrated end-to-end improvement: every Dynamo Diff final response failed the required complete-JSON format. Lower tokens or time for those failures are not productivity evidence. All original outputs, individual scores, frozen evaluated code and explicitly post-hoc format-sensitivity results are retained. Human answer-key and semantic review remain pending. The later MCP navigation hints have transport coverage but no measured model-performance result.

The [CLI walkthrough](../docs/DEMO.md) records five successful actual commands, including original evidence retrieval. `demo/cli-003/receipt.json` retains the corrected guard display, output and hashes; the recording includes intentional presentation pauses. The earlier `cli-002` remains a historical recording of candidate-only guard labels. The in-conversation preview's controls and narrow-width wrapping were checked in the browser; the updated data shows the baseline scalar category and opens the original guard excerpt. This is not native editor visual acceptance.

## Packaging and open gates

Wheel, source archive and VSIX exist locally. The source archive includes the offline demonstrations, controlled fixtures, real-project captures, exact upstream license texts, completed pilot and recorded CLI demo. Hosted CI passed for the uploaded private repository. The artifacts remain development previews pending native visual acceptance and human fixture/case/answer-key/semantic review. The requirement audit records these open gates.

`final-local-checkpoint.json` identifies the unchanged local build artifacts and local test receipts; its pre-upload open-gate notes are superseded by the hosted CI checkpoint above. Earlier `build-receipt.json` and `wheel-profile-checkpoint.json` are historical checkpoints; their hashes describe earlier implementations. No package has been published, no external user validation is claimed, and the original scope remains unchanged.

## Processing benchmark

The separate retained baseline measured 10 MiB/100 MiB synthetic inputs in three fresh import processes each, and the real edit pair in 20 warm comparisons. All generated-input count checks passed. `docs/PERFORMANCE.md` documents measured time, process peak RSS, output size, cache assumptions, separate tlparse conversion costs and investigation thresholds. Hardware was verified as an Apple M1 Pro, 32 GiB RAM, MacBookPro18,3. This provides tool-processing evidence; it does not measure agent diagnosis quality or application speed.

After the revision-4 validation changes, the same procedure measured **1.349 s / 13.466 s** median imports for 10 MiB / 100 MiB, about 42% above the original baseline. Peak RSS was **58.8 / 254.7 MiB**. `benchmarks/check_regression.py` reports `within_thresholds` against the unchanged earlier thresholds. Both sets of individual measurements are retained.
