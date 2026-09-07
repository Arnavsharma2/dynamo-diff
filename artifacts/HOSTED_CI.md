# Hosted CI checkpoint

The approved review-policy documentation revision `e20b29163b1f0b658e26037bba54f618e12ea1da` also passed all three jobs in [run 34149211212](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34149211212): macOS/Linux installed-wheel checks and Linux development/installed-extension checks. The implementation-specific retained logs below continue to document the unchanged runtime and its regression coverage.

## Current implementation: source-map validation

[Verify run 34147070929](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34147070929) passed at commit `813b7f8407175c14ffb666eb4c0af1aa541a03d5` on September 7, 2026. Both macOS arm64 and Ubuntu x64 used CPython 3.13.15 and passed **96 installed-wheel tests**, both offline demonstrations and **12 evaluation-harness tests**. The Linux editor job passed **10 development-host checks**, packaged the extension, and passed **11 isolated installed-VSIX checks** in VS Code 1.132.1.

The [status receipt](hosted-ci-34147070929.json) and [complete log](hosted-ci-34147070929.log) retain exact jobs, environments, commands and results. This runner's VSIX SHA-256 is `1717312c8f2d1c5f24298bc3c1ebdcd96ad89ef03fb8b581e599e6992e97e669`. These results include the [source-map regressions](../docs/INPUT_AUDIT.md); they required no additional CI fix or model calls. The [local source-map checkpoint](source-map-checkpoint.json) identifies the separately built local packages.

## Initial upload

The private `Arnavsharma2/dynamo-diff` repository was created and the prepared `codex/dynamo-diff` branch uploaded with user approval on September 7, 2026. [Verify run 34145658752](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34145658752) passed on commit `0fd1053530792a979ec397a1b7f91154b9d4f0d1` without a workflow or implementation fix.

| Job | Environment observed in the log | Result |
|---|---|---|
| Core, macOS | macOS 26.5.2 arm64, CPython 3.13.14 | Installed wheel: 93 tests; both offline demonstrations; 12 evaluation-harness tests passed |
| Core, Linux | Ubuntu 24.04.4 x64, CPython 3.13.15 | Installed wheel: 93 tests; both offline demonstrations; 12 evaluation-harness tests passed |
| Editor, Linux | Ubuntu 24.04.4 x64, VS Code 1.132.1, Node 24 | 10 development-host checks, VSIX packaging and 11 isolated installed-VSIX checks passed |

The core release script required PyTorch and Transformers to be absent. The evaluation-harness checks made no model calls. CI inspected retained captures; it did not regenerate the ML workloads or rerun the diagnostic pilot.

The [GitHub status receipt](hosted-ci-34145658752.json) retains the tested commit, job results, timestamps and URLs. The [complete run log](hosted-ci-34145658752.log) retains the actual commands, environments and assertions. CI's VSIX has SHA-256 `380111de1d0df462e6ff60d7389d17463fd627c6c4757de8bcff11f81cba5a7f`; it was built on the runner and is distinct from the local VSIX identified by `final-local-checkpoint.json`.

This closes hosted execution for the recorded environments. Windows, other Python/VS Code versions and native visual inspection remain outside the CI result. Independent human explanation/evaluation review is optional under the [approved scope revision](../docs/PROJECT_SCOPE.md#approved-review-policy-revision--september-7-2026) and has not occurred. The repository is private; no PyPI or Marketplace release or external adoption is implied.
