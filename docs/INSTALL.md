# Install Dynamo Diff

Install the VS Code extension **0.1.2** from [Marketplace](https://marketplace.visualstudio.com/items?itemName=dynamo-diff.dynamo-diff), and install the Python analyzer **0.1.1** from [PyPI](https://pypi.org/project/dynamo-diff/). The extension requires the separately installed Python analyzer. The earlier **0.1.0** [GitHub release](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0) remains available with its source archive, build evidence and `SHA256SUMS`.

Python 3.13 is the tested setup on macOS and Linux. The package declares Python 3.11 or newer, but other versions and Windows have not been verified. Inspecting saved captures needs neither PyTorch nor a GPU.

## Python CLI

Create a virtual environment and install from PyPI:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install 'dynamo-diff[mcp]'
.venv/bin/dynamo-diff --version
```

The `mcp` extra enables the local agent server. Omit `[mcp]` if you only need the CLI and editor. Installation downloads ordinary Python dependencies; analyzing a saved capture does not upload it.

## VS Code extension

1. Install **Dynamo Diff**, published by **Dynamo Diff**, from [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=dynamo-diff.dynamo-diff). Its exact identifier is `dynamo-diff.dynamo-diff`. From a terminal with the VS Code CLI configured, you can use `code --install-extension dynamo-diff.dynamo-diff`.
2. Set **Dynamo Diff: Python Path** (`dynamoDiff.pythonPath`) to the absolute path of the virtual environment's Python, such as `/your/project/.venv/bin/python`. Preserve the virtual-environment path instead of resolving its symlink to the base interpreter.
3. In a trusted workspace, run **Dynamo Diff: Import Capture** for each saved report directory and its manifest, then **Dynamo Diff: Compare Captures**.
4. Expand **Dynamo Diff** in Explorer to open the comparison table, captured source or original guard evidence.

The earlier 0.1.0 VSIX remains available in the GitHub release for that version. Use Marketplace for the current editor package.

The extension is tested with VS Code 1.132.1 on macOS and Linux. Its manifest permits 1.100 or newer; that entire version range has not been tested. It invokes the configured local Python package, so installing the VSIX alone is insufficient.

## Try the included captures

The wheel contains the analyzer. The source archive and Git checkout additionally contain the demo scripts and recorded captures. After installing the package, download and extract the source distribution from [PyPI's files page](https://pypi.org/project/dynamo-diff/0.1.1/#files), or clone the repository, then run from that source directory using your installed environment:

```sh
/absolute/path/to/.venv/bin/python tools/demo.py
/absolute/path/to/.venv/bin/python case_studies/transformers_cache/verify.py
```

For the editor example, import `fixtures/captures/edit_before/report` with its adjacent `manifest.json`, then `fixtures/captures/edit_after/report` with its manifest. Choose the before capture as baseline and after capture as candidate.

These commands inspect retained outputs without executing their workloads. [Capture instructions](CAPTURING.md) cover recording your own supported reports. [Integration instructions](INTEGRATIONS.md) cover MCP configuration and troubleshooting; [compatibility](COMPATIBILITY.md) defines the accepted format.

## Verify downloads

The [PyPI publication receipt](../artifacts/pypi-publication-0.1.1.json) records the wheel/source archive hashes and fresh-install verification. PyPI also lists file hashes and publishing attestations on its files page.

For the historical GitHub release, keep the downloaded files and `SHA256SUMS` together. On macOS, use `shasum -a 256 -c SHA256SUMS`; on Linux, use `sha256sum -c SHA256SUMS`. Download all listed files for a complete check. That checksum file checks byte integrity; it is not a separate signed attestation.
