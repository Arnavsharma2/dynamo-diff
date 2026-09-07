# Hosted CI checkpoint

The private `Arnavsharma2/dynamo-diff` repository was created and the prepared `codex/dynamo-diff` branch uploaded with user approval on September 7, 2026. [Verify run 34145658752](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34145658752) passed on commit `0fd1053530792a979ec397a1b7f91154b9d4f0d1` without a workflow or implementation fix.

| Job | Environment observed in the log | Result |
|---|---|---|
| Core, macOS | macOS 26.5.2 arm64, CPython 3.13.14 | Installed wheel: 93 tests; both offline demonstrations; 12 evaluation-harness tests passed |
| Core, Linux | Ubuntu 24.04.4 x64, CPython 3.13.15 | Installed wheel: 93 tests; both offline demonstrations; 12 evaluation-harness tests passed |
| Editor, Linux | Ubuntu 24.04.4 x64, VS Code 1.132.1, Node 24 | 10 development-host checks, VSIX packaging and 11 isolated installed-VSIX checks passed |

The core release script required PyTorch and Transformers to be absent. The evaluation-harness checks made no model calls. CI inspected retained captures; it did not regenerate the ML workloads or rerun the diagnostic pilot.

The [GitHub status receipt](hosted-ci-34145658752.json) retains the tested commit, job results, timestamps and URLs. The [complete run log](hosted-ci-34145658752.log) retains the actual commands, environments and assertions. CI's VSIX has SHA-256 `380111de1d0df462e6ff60d7389d17463fd627c6c4757de8bcff11f81cba5a7f`; it was built on the runner and is distinct from the local VSIX identified by `final-local-checkpoint.json`.

This closes hosted execution for the recorded environments. Windows, other Python/VS Code versions, native visual acceptance and required human explanation/evaluation review remain outside this result. The repository is private; no PyPI or Marketplace release or external adoption is implied.
