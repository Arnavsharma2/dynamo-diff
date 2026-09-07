# Compatibility and resource bounds

## Tested toolchain

| Component | Tested version / role |
|---|---|
| CPython | 3.13.2 locally on macOS arm64; hosted 3.13.14/3.13.15 on macOS arm64 and 3.13.15 on Linux x64 |
| PyTorch | 2.14.0, source commit `08187d9e0fba026dc8217405802ab5381dc88d90` |
| Transformers | 5.10.1, full CPU `generate()` static-cache case study |
| tlparse | Published package 0.4.3; `raw.jsonl` export and linked payloads |
| Dynamo metrics | `log_format_version=3` |
| Pydantic | 2.13.5 |
| MCP Python SDK | 2.1.1, stdio server/client round trip |
| VS Code | 1.132.1, macOS arm64 and Linux x64 isolated development/installed-VSIX hosts |
| TypeScript | 7.0.2; extension uses VS Code 1.100 API types |

The extension's API floor is declared as VS Code 1.100. Runtime tests currently cover 1.132.1 only. The Python package declares 3.11+, but verified environments are Python 3.13. The [hosted CI checkpoint](../artifacts/HOSTED_CI.md) records passing wheel checks on macOS 26.5.2 and Ubuntu 24.04.4, plus Linux editor checks. Windows and additional Python/editor versions remain unverified. Compiler workload generation was performed on the original local toolchain; hosted CI inspects the retained captures without ML runtimes.

The converter is outside the analyzer. A report must contain a single string-table header, metadata records, and referenced payload files from the tested export. Import does not check an HTML report's appearance or run tlparse automatically. Producer/metrics versions outside the supported pair are rejected. Missing version metadata yields partial/unknown results, not a successful compatibility claim.

Only one process/rank is supported per capture. Mixed process IDs/ranks, repeated export headers, compiled-autograd and backward-compiler records are rejected. Missing process metadata limits what can be detected; this is not a general distributed-trace partitioner. Supply separately converted per-process bundles.

## Explicit limits

The Python `Limits` model supplies these defaults:

| Resource | Bound |
|---|---:|
| Total imported input | 512 MiB |
| One metadata record | 2 MiB |
| One payload or source snapshot | 16 MiB |
| One source snapshot analyzed for AST identity/diff | 1 MiB |
| Source diff work | At most 4,000,000 baseline-line × candidate-line pairs |
| JSON nesting | 64 levels |
| Metadata records | 1,000,000 |
| Compilation identities | 100,000 |
| MCP response | 12,000 JSON characters |
| Default evidence excerpt | 6,000 characters |
| MCP function page | Requested 1–20, default 5; reduced to fit output budget |

Aggregate input includes copied metadata, all referenced payloads (including uninterpreted artifacts), source/raw-trace context and the canonical manifest. Normalized stored output is also limited to 512 MiB. Only regular files can become artifacts; named pipes cannot make import wait for a writer. Paths colliding with the store's reserved manifest are rejected. JSON with duplicate object keys, non-finite numbers or invalid Unicode is not silently accepted. Bad metadata records remain visible as partial evidence; malformed manifests are rejected with a structured error.

The source-analysis limits retain readable, verified snapshots while leaving AST/diff correspondence unresolved when work would exceed the bounds. Explicit user mappings remain available. The library can configure resource limits; they are not yet exposed as CLI flags.

CLI full JSON is intended for file/tool consumption and can exceed the MCP response budget. The editor subprocess has a 32 MiB output cap and a 180-second timeout. A large report may require CLI use. These are operational limits; the separate [performance baseline](PERFORMANCE.md) records measured processing costs and their limitations.

MCP returns truncation flags and a next offset for function/evidence pages. It also limits groups, evidence IDs and source labels within a row, with explicit flags. One row that cannot fit produces `response_limit`. Use the CLI full report to inspect the complete group/evidence index.

## Versions and invalidation

Public schema version is `1`; the current adapter normalization revision is `tlparse-0.4.3-torch-2.14-log3-v4` and comparison rules are version `4`. Capture identity hashes imported artifacts, manifest, adapter, schema and source-analysis options. Comparison identity adds both capture IDs, the comparison-rule version, explicit source map and source-analysis/diff limits. Changing those inputs creates a different identity; do not reuse hard-coded demonstration IDs across adapter revisions. The normalized capture is cached; comparisons are currently recomputed and carry deterministic identities rather than a persisted result cache.

Stored artifacts and normalized metadata are hash-checked when read. This detects accidental local modification; it is not a cryptographic signature from an independent observer. Completion declarations are also declarations, not independent proof that all intended work ran.
