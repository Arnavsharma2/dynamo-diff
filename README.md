# Dynamo Diff

Compare two recorded PyTorch Dynamo runs and inspect the compiler evidence behind the difference. A local Python analyzer powers a CLI, three MCP tools, and a small VS Code extension.

**Development status:** [hosted CI](artifacts/HOSTED_CI.md) passes core and MCP checks on macOS/Linux and development/installed-extension checks on Linux; local macOS editor checks also pass. The [import benchmark](docs/PERFORMANCE.md) has a measured baseline, and a [real Transformers investigation](case_studies/transformers_cache/README.md) retains before/after traces and eager-output checks. The [60-trial diagnostic pilot](benchmarks/agent_pilot/README.md) finished without demonstrating end-to-end agent improvement. Audits are **AI-reviewed**; the user made independent human review optional in the [scope revision](docs/PROJECT_SCOPE.md). See [delivery status](docs/STATUS.md) for the remaining acceptance checks. This project is not yet published to PyPI or the VS Code Marketplace.

## What a comparison tells you

- Completed compilations, explicit recompilations, failures, no-graph outcomes, graph breaks, limits, and unknowns stay separate.
- Recorded guard reasons link to immutable artifacts, with hashes and bounded excerpts.
- Source snapshots support conservative matching across ordinary function-body edits and shifted frame IDs. Ambiguous matches stay unresolved.
- Workload declarations and recorded compiler settings are compared before interpreting event deltas.

The tool does not prove an optimization is correct or faster. Several failed guards can belong to one recompilation; fewer compilations can accompany a failure or a compiler limit. These distinctions are part of its [correctness contract](docs/SEMANTICS.md).

## Install from this checkout

Use Python 3.13 for the tested setup. The package declares Python 3.11 or newer; other Python versions have not yet been verified.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install '.[mcp]'
.venv/bin/dynamo-diff --version
```

Inspecting saved captures requires neither PyTorch nor a GPU. `.[fixtures]` adds the pinned compiler and converter for generating new captures. [Compatibility](docs/COMPATIBILITY.md) lists the supported trace format; arbitrary PyTorch/tlparse versions are not supported.

## Try the recorded edit

```sh
.venv/bin/python tools/demo.py
```

This imports the bundled before/after captures into a temporary store, checks their expected comparison, and prints a Markdown table. `compute` changes from three completed compilations, including two confirmed recompilations, to one completed compilation with no confirmed recompilation. A new helper remains in candidate totals as an unmatched function. These are captured compiler observations, not a runtime-speed result.

The [recorded walkthrough](docs/DEMO.md) shows the five-command import, comparison and original-evidence flow, with a plain-text transcript and reproducible recording script.

For the retained full Transformers `generate()` case, run `python case_studies/transformers_cache/verify.py`. Early static-cache initialization removes one warm-request recompile while retaining prefill/decode specialization. This inspection also works without PyTorch or Transformers; the case guide separately explains workload regeneration.

To inspect your own converted reports:

```sh
.venv/bin/dynamo-diff import ./baseline-report --manifest ./baseline.json
.venv/bin/dynamo-diff import ./candidate-report --manifest ./candidate.json
.venv/bin/dynamo-diff compare BASELINE_CAPTURE_ID CANDIDATE_CAPTURE_ID --format markdown
.venv/bin/dynamo-diff compare BASELINE_CAPTURE_ID CANDIDATE_CAPTURE_ID --format json
.venv/bin/dynamo-diff evidence CAPTURE_ID EVIDENCE_ID --max-chars 1000
```

Use the IDs returned by import and comparison. `--store /path/to/store` is a global option placed **before** the subcommand; the default is `.dynamo-diff` in the current directory. `analyze CAPTURE_ID`, `source CAPTURE_ID FUNCTION_ID`, and `schema --kind comparison` expose the single-run report, captured source, and public report schema. [Capture instructions](docs/CAPTURING.md) explain manifests and finalization.

## Use from an agent or editor

The MCP server runs locally over stdio:

```sh
.venv/bin/dynamo-diff --store /absolute/path/to/store serve-mcp --allow-root /absolute/path/to/capture-bundles
```

The experimental agent interface exposes `import_trace`, `compare_runs`, and `get_evidence`. The current pilot does not establish improved diagnosis quality or productivity. Imports are restricted to explicitly configured directories. Comparisons and evidence discovery are paginated; original evidence text is fetched only when requested. An agent may send returned data to its configured model provider. Local MCP does not imply local model inference.

The VS Code extension invokes the same CLI using a configured Python executable. Import captures, choose a baseline and candidate, open the comparison table, then navigate to captured source and original evidence through the results tree. [Integration instructions](docs/INTEGRATIONS.md) include MCP configuration, extension installation, and troubleshooting.

## Development

```sh
.venv/bin/python -m pip install --require-hashes -r requirements-test.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m pytest -q
cd extension
npm ci
npm run compile
```

`requirements-test.lock` pins core, MCP, tests and packaging without PyTorch. `requirements-dev.lock` additionally pins fixture generation. `requirements-case-study.lock` adds the pinned Transformers reproduction. All target Python 3.13. Actual artifact regeneration is separate from ordinary tests and refuses to overwrite retained captures.

See [architecture](docs/ARCHITECTURE.md), [semantics](docs/SEMANTICS.md), [release instructions](docs/RELEASING.md), and the original [project scope](docs/PROJECT_SCOPE.md).

## Local data handling

Import reads saved metadata, source snapshots, and payloads. It does not execute source, guard expressions, shell text, or a workload. Imported data is bounded and content-addressed; evidence hashes detect later changes. No telemetry or automatic uploads are implemented. Traces can still contain private code, paths, and values—choose agent import roots and requested excerpts accordingly.

Original project code is MIT licensed. Captured upstream source retains its original terms; see [third-party notices](docs/THIRD_PARTY_NOTICES.md).
