# Dynamo Diff for VS Code

Compare saved PyTorch Dynamo captures and navigate to source-linked compiler evidence. This is a development preview, not a published Marketplace release.

Install the Dynamo Diff Python package from its source checkout, then set `dynamoDiff.pythonPath` to that environment's full Python executable path. PyTorch and a GPU are not needed to inspect saved captures. The tested adapter accepts PyTorch 2.14.0 / tlparse 0.4.3 report bundles.

Use **Dynamo Diff: Import Capture** twice, choosing each report directory and its optional manifest. Run **Compare Captures**, select baseline and candidate, then expand **Dynamo Diff** in Explorer. **Show Comparison Table** displays counts, guard categories and source-match status; **Show Comparison Report** opens the full JSON.

Source and evidence entries open captured virtual documents. Baseline links retain baseline source, even after your working tree changes. The progress notification supports cancellation. A trusted workspace and an installed Python package are required.

Counts describe observed compiler behavior. Failed attempts, compiler limits, missing evidence and ambiguous matches constrain conclusions. This extension does not prove an application is fixed, correct, or faster.

The extension invokes the configured Python executable directly without a shell. It has no telemetry or automatic uploads. Traces can contain private source code and local paths; enabling an agent integration can send requested excerpts to that agent's model provider.

Build locally with `npm ci` followed by `npm run package`, then use **Extensions: Install from VSIX...**. Integration instructions and the full project status are included in the source repository's `docs` directory.
