# CLI, MCP and VS Code

## One installed Python package

Install from PyPI with `python -m pip install 'dynamo-diff[mcp]'` in your chosen virtual environment. All interfaces use the same capture/comparison model. The core has no model API dependency. Keep the chosen environment available: the editor does not bundle Python or download packages automatically.

Use absolute executable/store/capture paths in integrations. On Windows the environment's Python executable is normally under `Scripts`; on macOS/Linux it is under `bin`. Windows integration is not yet verified.

## MCP over stdio

Configure the client with the Python executable and these separate arguments:

```json
{
  "servers": {
    "dynamo-diff": {
      "type": "stdio",
      "command": "/absolute/path/to/.venv/bin/python",
      "args": [
        "-m", "dynamo_diff.cli",
        "--store", "/absolute/path/to/dynamo-store",
        "serve-mcp",
        "--allow-root", "/absolute/path/to/capture-bundles"
      ]
    }
  }
}
```

This is the VS Code `.vscode/mcp.json` format; replace the example paths. For other clients, use their equivalent stdio server configuration. VS Code also supports portable Agent Host configuration with a different file format; see its [MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration). The example above needs no credentials or input variables.

`--allow-root` is repeatable. Report and manifest must be inside allowed roots, and linked payload/source paths must remain inside their bundle roots. Use a dedicated capture directory, not a broad home-directory allowlist. The server writes only its configured local store; it cannot launch a workload or edit model code.

Expected tools:

| Tool | Arguments | Result |
|---|---|---|
| `import_trace` | `report_directory`, optional `manifest_path` | Capture ID, validity, counts, notices |
| `compare_runs` | `baseline_id`, `candidate_id`, optional `offset`, `page_size`, `source_map` | Shared comparison model with bounded function rows |
| `get_evidence` | `capture_id`, optional `evidence_id`, `offset`, `max_chars`, `kind` | Paginated evidence index or hash-linked original excerpt |

Omit `evidence_id` to discover evidence, optionally filtering `kind` (for example, `recompile_reasons` or `dynamo_error`). The index returns IDs, artifact names and record locations; its `offset` counts entries. Supply an indexed `evidence_id` to retrieve its original text; excerpt offsets count characters. Do not supply `kind` with an evidence ID. Both modes honor a bounded response budget.

Import responses include `next_steps`: an executable evidence-index tool call and the arguments required for comparison. When diagnosing a change, call `compare_runs` with explicitly chosen baseline/candidate IDs before attributing it to source or workload differences. This navigation aid was added after the first pilot; its effect on model behavior has not been measured. Agent clients should validate their own final response format and retain validation failures and any retry costs.

Always follow `next_offset` until it is null when the complete result is needed. Within-row truncation has separate flags. Comparison rows include only a short list of evidence IDs; use the index to discover later evidence, including guard failures. The CLI full JSON also exposes the complete index. Tool error results set MCP `isError` and contain `error.code`/`error.message`. The Python SDK stdio integration test lists and calls all three tools; client-specific chat diagnosis remains part of the evaluation work.

Default reports do not include raw source text. Requested evidence can include private source, paths and values. The client's model may receive that content, even though the server itself runs locally. Raw excerpts are labeled untrusted data.

## VS Code extension

Install [Dynamo Diff from VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=dynamo-diff.dynamo-diff). For local development, build a VSIX from the `extension` directory:

```sh
npm ci
npm run package
```

For that local build, run **Extensions: Install from VSIX...** in VS Code and select the generated VSIX.

Set `dynamoDiff.pythonPath` to the full path of the Python executable where the package is installed. Optionally set `dynamoDiff.storePath`; otherwise the extension uses its workspace storage. Trust the workspace before invoking Python.

1. Run **Dynamo Diff: Import Capture**. Choose the converted report directory and its manifest, or explicitly import without a manifest.
2. Import the other capture, then run **Dynamo Diff: Compare Captures**. Select baseline first and candidate second.
3. Expand **Dynamo Diff** in Explorer. Capture validity, workload comparability and performance limitations are visible independently of counts.
4. Use **Show Comparison Table** for baseline/candidate counts and guard categories. **Show Comparison Report** opens the full JSON model.
5. Under each source function, open the baseline/candidate captured source or an evidence entry. These are separate virtual documents; source navigation uses the captured line rather than current working-tree text. Large evidence excerpts offer **Open next excerpt**.

The progress notification supports cancellation. Missing snapshots produce `missing_source`; the extension does not silently substitute another file. Failures leave the previous successful comparison visible. The interpreter is executed without a shell, including paths containing spaces.

## Editor test isolation

`npm test` runs the compiled integration suite in a temporary workspace/profile, with separate extension storage and user settings. It downloads its pinned editor if an executable is not supplied. To reuse a known installation on macOS:

```sh
VSCODE_EXECUTABLE_PATH='/Applications/Visual Studio Code.app/Contents/MacOS/Code' npm test
```

`DYNAMO_DIFF_PYTHON` overrides the test interpreter. `DYNAMO_DIFF_TEST_RESULT` writes a machine-readable receipt. Ordinary tests should not install into your normal editor profile.

On this macOS host, launching the GUI from a restricted shell sandbox aborted during application registration before extension activation. Launching the isolated test with normal desktop process permissions worked. Do not repeatedly retry a sandboxed GUI startup. A failed test also closes its own development-host window by design; inspect the test result to distinguish that exit from an application crash.
