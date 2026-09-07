# Local build and release checklist

These instructions create installable local artifacts. Public package publication is a separate action requiring a chosen distribution channel.

## Build

Use Python 3.13 and install the hashed test/build lock, then the checkout:

```sh
python -m pip install --require-hashes -r requirements-test.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest -q
python tools/demo.py
python -m build --no-isolation
```

The wheel and source archive appear under `dist`. Build the extension with `npm ci` and `npm run package` from `extension`. Do not infer Marketplace availability from a successful VSIX build.

## Fresh installation

Create a separate Python 3.13 environment. Install the test lock and the built wheel with `--no-deps`, then run `python tools/check_release.py --require-wheel --junit artifacts/wheel-tests.xml`. This verifies the actual import comes from `site-packages`, requires both PyTorch and Transformers to be absent, checks committed schemas, runs the suite with pytest's source-path override disabled, and runs the authored-edit and real-project demonstrations. The suite includes CLI and actual MCP stdio subprocesses. An editable checkout import is not a clean-wheel proof.

For the extension, run the isolated editor suite and install the VSIX into a separate test profile. Validate import, comparison table, source/evidence navigation, missing-data errors and cancellation. Record the exact editor/platform used; green TypeScript compilation alone is insufficient.

## Portfolio v1 delivery checklist

- Evidence-backed, AI-reviewed fixture expectations and explanations, including negative controls. Independent human review is optional under the [approved scope revision](PROJECT_SCOPE.md#approved-review-policy-revision--september-7-2026) and has not occurred.
- Review the completed [input and evidence boundary audit](INPUT_AUDIT.md), its source-map correction and documented limits.
- Review the retained [Transformers investigation](../case_studies/transformers_cache/README.md), its independent output evidence and reproduction recipe.
- AI review of the completed ten-question, 60-attempt diagnostic pilot across raw logs, tlparse text and Dynamo Diff. Individual results and failures are retained; the primary result shows no demonstrated end-to-end improvement. Mechanical scores retain their limitations, and frozen protocols and trial records must not be rewritten to imply human validation.
- Review [upstream notices](THIRD_PARTY_NOTICES.md) and the included license texts for redistributed artifacts.
- Native editor visual acceptance. Fresh-wheel and installed-VSIX checks pass locally and in [hosted CI](../artifacts/HOSTED_CI.md); the [short CLI demo](DEMO.md) is recorded.
- Requirement-by-requirement comparison against the current approved project scope; preserve the [original proposal](PROJECT_SCOPE_ORIGINAL.md) alongside the review-policy revision.

Record evidence in `STATUS.md`; never replace an unverified gate with a broader claim based on unit tests. External feedback/adoption remains unclaimed unless actually obtained. Once the gates pass, finalize the version/changelog and hash the artifacts. The approved private repository provides project delivery; PyPI, Marketplace and public repository publication remain separate decisions.

The initial 10 MiB/100 MiB processing baseline and separate conversion timings are already recorded in [PERFORMANCE.md](PERFORMANCE.md). Repeat them when implementation changes or unresolved regression concerns warrant it.

## CI

`.github/workflows/ci.yml` defines wheel-based core checks on macOS/Linux and an actual VS Code extension-host run under Xvfb on Linux. Official checkout/Python/Node actions are pinned to verified release commits, and the workflow grants read-only repository access. It does not execute recorded workloads or require ML runtimes for normal checks.

The first [hosted run](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34145658752) passed on September 7, 2026 at commit `0fd1053530792a979ec397a1b7f91154b9d4f0d1`. Both macOS/Linux wheel jobs passed 93 core tests, both offline demonstrations and 12 evaluation-harness tests. The Linux editor job passed ten development-host checks, built the VSIX and passed eleven checks against its isolated installation. [The retained checkpoint](../artifacts/HOSTED_CI.md) records exact environments and links the complete log. CI does not establish human review or native visual inspection.

The [source-map validation revision](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34147070929), commit `813b7f8407175c14ffb666eb4c0af1aa541a03d5`, subsequently passed **96 core tests** on both hosted platforms, both demonstrations, twelve evaluation-harness tests and the same ten/eleven development/installed-VSIX checks. Its status and complete log are retained alongside the initial run.
