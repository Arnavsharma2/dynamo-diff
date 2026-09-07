# Recorded CLI walkthrough

The [26-second recording](../artifacts/demo/cli-003/walkthrough.cast) runs five real commands against the retained authored-edit captures. The [plain-text transcript](../artifacts/demo/cli-003/transcript.txt) is readable without a player. The [receipt](../artifacts/demo/cli-003/receipt.json) retains each argument list, stdout, stderr, exit code, command duration, recorder hash and recording hash. All five commands exited 0.

1. Import the baseline report and its manifest.
2. Import the candidate report and its manifest.
3. Compare their workload declarations, matched functions and compiler counts.
4. Retrieve an original guard reason, including its artifact path and SHA-256.
5. Verify the edited function and the newly added, unmatched helper.

The comparison matches `compute` across the source edit: three completed compilations, including two confirmed recompilations, become one completed compilation with no confirmed recompilation. Guard categories are shown on both sides: `python_scalar → none recorded`. The candidate's new helper contributes another completed compilation to candidate totals, and its absent baseline counterpart is labeled `function absent`. The manifest comparison is consistent, but declarations alone do not prove equivalent execution. Application performance remains explicitly unmeasured.

This is actual CLI subprocess output with narrated command labels and five intentional five-second presentation pauses. Its total duration is not a processing benchmark. The recording used the separate installed-wheel environment without PyTorch or Transformers, after the baseline-guard display correction. It is not a native VS Code screen recording.

The file uses the documented [asciicast v2 format](https://docs.asciinema.org/manual/asciicast/v2/). A compatible player can replay it locally; no upload is required. The earlier `artifacts/demo/cli-001/failure.json` records a recorder setup assertion failure and is not a successful demo. `cli-002` retains the earlier successful recording, whose comparison displayed only candidate guard categories; use `cli-003` for the corrected current behavior.

## Reproduce

From the checkout, using an installed Dynamo Diff package:

```sh
python tools/demo.py
python tools/record_demo.py --output artifacts/demo/my-new-recording
```

Choose a new output directory each time. The recorder refuses to overwrite an existing recording, uses a temporary capture store, and inspects saved captures without executing the recorded workloads. `--pause 0` removes presentation pauses for a quick local check.

## VS Code review

The tested VSIX is installed in the user-approved `Dynamo Diff Demo` profile. Both authored captures were imported through the native UI. The demo workspace's Python setting points to the virtual environment executable, preserving its path rather than resolving its symlink to the base Python interpreter.

The installed-VSIX integration suite passed eleven checks, including comparison, captured source/evidence navigation, error recovery, cancellation, active-editor-group reuse and activation of the rendered table. The original navigation code expanded a one-column test workspace to six columns; the retained regression fails on that behavior, and the fix preserves one column. Source snapshots remain distinct and read-only.

Native import and comparison produced three → two total completed compilations and two → zero confirmed recompilations. The table's baseline/candidate categories and validity fields were inspected through the native accessibility tree. The rebuilt VSIX was then installed in the approved profile, and the demo window was reloaded. The desktop locked before the updated layout and native source/evidence walkthrough could be visually verified. The CLI recording does not substitute for that remaining visual check. Earlier stale capture/accessibility errors are retained in the verification notes; they do not establish another editor crash.

The September 7 retry recovered the updated comparison tree and invoked table/source navigation, but the outer window title, accessibility content and screenshots disagreed about the active view. Final visual acceptance remains pending consistent native state. Hosted Linux and local macOS installed-VSIX tests independently passed source/evidence navigation and editor-group preservation; those checks are recorded in the [verification notes](../artifacts/VERIFICATION.md).

A later follow-up visually verified the baseline's original `compute` branch at line 9 and the rendered table with counts, separate baseline/candidate guards, the unmatched helper and performance limitation in one editor group. The evidence action changed the outer title to `payload-10-0.txt`, but its content could not yet be verified because the UI tool continued showing the old table. The remaining visual check is candidate source and original evidence; baseline/table inspection is complete.

The next native screenshot verified the original evidence view: `payload-10-0.txt` displays `step == 1`, the captured `if step > 0` source context, artifact `-_0_1_0/recompile_reasons_4.json`, record 10 and SHA-256 `832c22b265eea6007916338024fa9ad308f931e2ca6ecf4bbc57ce205b43dc6a`. The full excerpt fits in one editor group. This closes original-evidence visual inspection; candidate source remains.
