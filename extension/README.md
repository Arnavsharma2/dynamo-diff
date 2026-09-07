# Dynamo Diff for VS Code

Compare two saved PyTorch Dynamo runs, inspect which functions recompiled, and open the captured source and original guard evidence behind each change.

## Set up the Python analyzer

The extension uses the local Dynamo Diff Python CLI. Install it from [PyPI](https://pypi.org/project/dynamo-diff/):

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install dynamo-diff
.venv/bin/dynamo-diff --version
```

In VS Code settings, set **Dynamo Diff: Python Path** (`dynamoDiff.pythonPath`) to the full path of that virtual environment's Python executable, such as `/your/project/.venv/bin/python`. Keep the virtual-environment path intact rather than resolving its symlink to the base interpreter.

Python 3.13 and VS Code 1.132.1 are tested on macOS and Linux. Other Python/editor versions and Windows have not been verified. PyTorch and a GPU are not needed to inspect saved captures. The tested adapter accepts PyTorch 2.14.0 / tlparse 0.4.3 report bundles.

## Compare captures

Use **Dynamo Diff: Import Capture** twice, choosing each report directory and its optional manifest. Run **Compare Captures**, select baseline and candidate, then expand **Dynamo Diff** in Explorer. **Show Comparison Table** displays counts, guard categories and source-match status; **Show Comparison Report** opens the full JSON.

Source and evidence entries open captured virtual documents. Baseline links retain baseline source, even after your working tree changes. The progress notification supports cancellation. A trusted workspace and an installed Python package are required.

The [installation guide](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/INSTALL.md#try-the-included-captures) explains how to try the included before/after captures. [Capture instructions](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/CAPTURING.md) explain how to record your own supported reports.

## Interpretation and data handling

Counts describe observed compiler behavior. Failed attempts, compiler limits, missing evidence and ambiguous matches constrain conclusions. This extension does not prove an application is fixed, correct, or faster.

The extension invokes the configured Python executable directly without a shell. It has no telemetry or automatic uploads. Traces can contain private source code and local paths; enabling an agent integration can send requested excerpts to that agent's model provider.

Build locally with `npm ci` followed by `npm run package`, then use **Extensions: Install from VSIX...**. [Integration instructions](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/INTEGRATIONS.md) include MCP configuration and troubleshooting. Report reproducible problems in the [issue tracker](https://github.com/Arnavsharma2/dynamo-diff/issues).
