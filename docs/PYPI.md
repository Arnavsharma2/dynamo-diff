# Dynamo Diff

Compare saved PyTorch Dynamo captures, inspect which source functions compiled differently, and retrieve the original guard failures and captured source behind each result.

The Python package provides the analyzer, command-line interface and optional MCP server. The [VS Code extension](https://marketplace.visualstudio.com/items?itemName=dynamo-diff.dynamo-diff) uses the same local analyzer.

## Install

Python 3.13 is the tested setup on macOS and Linux. The package declares Python 3.11 or newer; other Python versions and Windows have not been verified. Analyzing saved captures requires neither PyTorch nor a GPU.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install dynamo-diff
.venv/bin/dynamo-diff --version
.venv/bin/dynamo-diff --help
```

For the optional agent interface, install the MCP extra:

```sh
.venv/bin/python -m pip install 'dynamo-diff[mcp]'
```

In VS Code, set **Dynamo Diff: Python Path** (`dynamoDiff.pythonPath`) to the full path of this environment's Python executable, such as `/your/project/.venv/bin/python`. Keep the virtual-environment path intact instead of resolving its symlink to the base interpreter.

## Use

Import two supported report bundles, compare the captures, then inspect source and original evidence. The [installation guide](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/INSTALL.md) includes a complete example using recorded before/after captures. The [capture guide](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/CAPTURING.md) explains how to record new inputs. [MCP configuration](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/INTEGRATIONS.md) covers the three tools: `import_trace`, `compare_runs`, and `get_evidence`.

The tested adapter accepts PyTorch 2.14.0 / tlparse 0.4.3 bundles. Arbitrary producer versions are not supported. Capture generation is separate from analysis and requires the supported compiler toolchain; see [compatibility](https://github.com/Arnavsharma2/dynamo-diff/blob/codex/dynamo-diff/docs/COMPATIBILITY.md).

## Interpretation and data handling

Reports distinguish compilation attempts, outcomes, explicit recompilation evidence, ambiguous source matches and missing records. Compiler-event counts do not establish application speed or correctness. The experimental agent pilot found no demonstrated end-to-end improvement.

Captures and comparisons are processed locally, with no telemetry or automatic uploads. Traces can contain private source code and local paths. When an agent calls the MCP server, requested evidence may be sent to that agent's model provider.

[Source and documentation](https://github.com/Arnavsharma2/dynamo-diff) · [Report a reproducible issue](https://github.com/Arnavsharma2/dynamo-diff/issues)
