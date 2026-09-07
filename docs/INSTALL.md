# Install Dynamo Diff 0.1.0

Download the Python wheel and VS Code extension from the [v0.1.0 release](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0). The release also includes a source archive, a 72-second demo, build evidence and `SHA256SUMS`. GitHub is the distribution channel for this version.

Python 3.13 is the tested setup on macOS and Linux. The package declares Python 3.11 or newer, but other versions and Windows have not been verified. Inspecting saved captures needs neither PyTorch nor a GPU.

## Python CLI

From the directory containing the downloaded wheel:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install './dynamo_diff-0.1.0-py3-none-any.whl[mcp]'
.venv/bin/dynamo-diff --version
```

The `mcp` extra enables the local agent server. Omit `[mcp]` if you only need the CLI and editor. Installation downloads ordinary Python dependencies; analyzing a saved capture does not upload it.

## VS Code extension

1. Download `dynamo-diff-0.1.0.vsix` from the same release.
2. In VS Code, run **Extensions: Install from VSIX...** and select that file.
3. Set **Dynamo Diff: Python Path** (`dynamoDiff.pythonPath`) to the absolute path of the virtual environment's Python, such as `/your/project/.venv/bin/python`. Preserve the virtual-environment path instead of resolving its symlink to the base interpreter.
4. In a trusted workspace, run **Dynamo Diff: Import Capture** for each saved report directory and its manifest, then **Dynamo Diff: Compare Captures**.
5. Expand **Dynamo Diff** in Explorer to open the comparison table, captured source or original guard evidence.

The extension is tested with VS Code 1.132.1 on macOS and Linux. Its manifest permits 1.100 or newer; that entire version range has not been tested. It invokes the configured local Python package, so installing the VSIX alone is insufficient.

## Try the included captures

The wheel contains the analyzer. The source archive and Git checkout additionally contain the demo scripts and recorded captures. After installing the wheel, extract `dynamo_diff-0.1.0.tar.gz` or clone the repository, then run from that source directory using your installed environment:

```sh
/absolute/path/to/.venv/bin/python tools/demo.py
/absolute/path/to/.venv/bin/python case_studies/transformers_cache/verify.py
```

For the editor example, import `fixtures/captures/edit_before/report` with its adjacent `manifest.json`, then `fixtures/captures/edit_after/report` with its manifest. Choose the before capture as baseline and after capture as candidate.

These commands inspect retained outputs without executing their workloads. [Capture instructions](CAPTURING.md) cover recording your own supported reports. [Integration instructions](INTEGRATIONS.md) cover MCP configuration and troubleshooting; [compatibility](COMPATIBILITY.md) defines the accepted format.

## Verify downloads

Keep the files and `SHA256SUMS` together. On macOS, use `shasum -a 256 -c SHA256SUMS`; on Linux, use `sha256sum -c SHA256SUMS`. Download all listed files for a complete check. The checksum file checks byte integrity; it is not a separate signed attestation.
