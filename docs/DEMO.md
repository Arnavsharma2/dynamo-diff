# Recorded CLI walkthrough

The [26-second recording](../artifacts/demo/cli-002/walkthrough.cast) runs five real commands against the retained authored-edit captures. The [plain-text transcript](../artifacts/demo/cli-002/transcript.txt) is readable without a player. The [receipt](../artifacts/demo/cli-002/receipt.json) retains each argument list, stdout, stderr, exit code, command duration, recorder hash and recording hash. All five commands exited 0.

1. Import the baseline report and its manifest.
2. Import the candidate report and its manifest.
3. Compare their workload declarations, matched functions and compiler counts.
4. Retrieve an original guard reason, including its artifact path and SHA-256.
5. Verify the edited function and the newly added, unmatched helper.

The comparison matches `compute` across the source edit: three completed compilations, including two confirmed recompilations, become one completed compilation with no confirmed recompilation. The candidate's new helper contributes another completed compilation to candidate totals. The manifest comparison is consistent, but declarations alone do not prove equivalent execution. Application performance remains explicitly unmeasured.

This is actual CLI subprocess output with narrated command labels and five intentional five-second presentation pauses. Its total duration is not a processing benchmark. The recording used the separate installed-wheel environment without PyTorch or Transformers. It predates the post-pilot MCP import-navigation change; the CLI behavior is unchanged. It is not a native VS Code screen recording.

The file uses the documented [asciicast v2 format](https://docs.asciinema.org/manual/asciicast/v2/). A compatible player can replay it locally; no upload is required. The earlier `artifacts/demo/cli-001/failure.json` records a recorder setup assertion failure and is not a successful demo.

## Reproduce

From the checkout, using an installed Dynamo Diff package:

```sh
python tools/demo.py
python tools/record_demo.py --output artifacts/demo/my-new-recording
```

Choose a new output directory each time. The recorder refuses to overwrite an existing recording, uses a temporary capture store, and inspects saved captures without executing the recorded workloads. `--pause 0` removes presentation pauses for a quick local check.

## VS Code review

The tested VSIX is installed in the user-approved `Dynamo Diff Demo` profile. Both authored captures were imported through the native UI. The demo workspace's Python setting points to the virtual environment executable, preserving its path rather than resolving its symlink to the base Python interpreter.

The installed-VSIX integration suite passed ten checks, including comparison, captured source/evidence navigation, error recovery and cancellation. Native visual acceptance is still pending: macOS screen capture and accessibility control failed before a verified comparison-table walkthrough. These automation errors do not establish another editor crash. The CLI recording does not substitute for that visual check.
