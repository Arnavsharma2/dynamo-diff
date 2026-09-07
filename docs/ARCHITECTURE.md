# Architecture

Saved raw trace → external pinned tlparse conversion → local report import → typed capture → conservative comparison → CLI, MCP and editor.

## Boundaries

`adapters/tlparse.py` incrementally reads the tested metadata export and associates payload evidence with compilation identities. It derives outcomes only from supported records, preserves notices/unknowns, and uses AST parsing for captured source identities. It never imports captured Python or evaluates a guard expression.

`store.py` validates relative paths and hashes, copies reports and manifest context into staging, and atomically installs a content-addressed capture directory. A normalized capture and an integrity manifest index the imported bytes. Evidence is fetched lazily by hash-checked artifact plus record offset or payload index. Snapshot retrieval never substitutes the user's current working tree.

`compare.py` groups run-local identities into source functions, checks workload declarations and observed configurations, then aligns only well-supported source counterparts. Exact structure and source-boundary diff mappings are conservative correspondence methods. Explicit one-to-one mappings are labeled. Ambiguous and unmatched rows remain in totals.

`cli.py` exposes the core model as full JSON and human-readable reports. Capture/comparison schemas come from the same Pydantic definitions. `mcp_server.py` adds approved import roots, bounded pages and protocol error envelopes over that core; it has no workload execution tool or model client.

The VS Code extension uses `execFile` with structured arguments to call the CLI. It displays the returned model in a native tree and an escaped Markdown table. Captured source/evidence use a read-only virtual document scheme; the extension implements no write-back path. The installed editor's ordinary virtual-document API is used, as described in [VS Code's documentation](https://code.visualstudio.com/api/extension-guides/virtual-documents). Other trusted extensions can manipulate editor buffers; the immutable store remains the evidence authority.

## Trust and persistence

Traces, manifests and source text are untrusted data. Path traversal and escaped symlinks are rejected. The analyzer has explicit file/record/event limits and no telemetry or network client. MCP clients may send returned content to their chosen model service; operators choose allowed roots and whether to request excerpts.

The configured Python interpreter is executable software chosen by the user, not trace data. The editor requires a trusted workspace before invoking it. Its capture store can be configured separately from the source tree. Import is idempotent; interrupted imports can leave staging data while committed capture identities remain immutable. Review cleanup and storage growth before large repeated experiments.

## Validation layers

Controlled PyTorch captures retain the raw trace, conversion, manifest, source and independent backend observations. Tests cover event interpretation, malformed input, immutable evidence, source changes, comparability, CLI parity and an actual MCP stdio process. The editor integration launches a separate temporary VS Code profile and checks import/comparison/navigation, table data, visible typing restrictions, errors and actual child-process cancellation.

These checks do not replace human review of fixture explanations or the separate held-out diagnostic study. Those remain explicit release work in `STATUS.md`.
