# Dynamo Diff for VS Code

Compare saved PyTorch Dynamo captures and navigate to source-linked compiler evidence. Version 0.1.0 is distributed as a VSIX through [GitHub Releases](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0).

Follow the [installation guide](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/INSTALL.md) to install the Python wheel and VSIX, then set `dynamoDiff.pythonPath` to that environment's full Python executable path. PyTorch and a GPU are not needed to inspect saved captures. The tested adapter accepts PyTorch 2.14.0 / tlparse 0.4.3 report bundles.

Use **Dynamo Diff: Import Capture** twice, choosing each report directory and its optional manifest. Run **Compare Captures**, select baseline and candidate, then expand **Dynamo Diff** in Explorer. **Show Comparison Table** displays counts, guard categories and source-match status; **Show Comparison Report** opens the full JSON.

Source and evidence entries open captured virtual documents. Baseline links retain baseline source, even after your working tree changes. The progress notification supports cancellation. A trusted workspace and an installed Python package are required.

Counts describe observed compiler behavior. Failed attempts, compiler limits, missing evidence and ambiguous matches constrain conclusions. This extension does not prove an application is fixed, correct, or faster.

The extension invokes the configured Python executable directly without a shell. It has no telemetry or automatic uploads. Traces can contain private source code and local paths; enabling an agent integration can send requested excerpts to that agent's model provider.

Build locally with `npm ci` followed by `npm run package`, then use **Extensions: Install from VSIX...**. [Integration instructions](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/INTEGRATIONS.md) include MCP configuration and troubleshooting. There is no VS Code Marketplace publication for this version.
