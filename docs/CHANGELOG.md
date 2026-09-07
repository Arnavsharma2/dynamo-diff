# Changelog

## Python analyzer 0.1.1 — September 7, 2026

- Add a PyPI-specific package description with absolute documentation links and installation instructions for the base analyzer and optional MCP extra.
- Add a manually dispatched build, verification and Trusted Publishing workflow, followed by installation checks against the public index.
- Keep the analyzer implementation unchanged apart from its reported version. Published on [PyPI](https://pypi.org/project/dynamo-diff/0.1.1/) through Trusted Publishing. Public wheel/source downloads match the verified build, and fresh macOS/Linux installations pass; see the [publication receipt](../artifacts/pypi-publication-0.1.1.json).

## VS Code extension 0.1.1 — September 7, 2026

Published to [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=dynamo-diff.dynamo-diff) under `dynamo-diff.dynamo-diff`. This editor package adds Python setup instructions, compatibility details, search keywords and support links. It uses the same verified runtime behavior and requires Python analyzer 0.1.0. Marketplace validation and a byte-for-byte public download check passed; see the [publication receipt](../artifacts/marketplace-publication.json).

## 0.1.0 — September 7, 2026

Initial public release of the saved-capture analyzer, local MCP server and VS Code extension. The tested adapter reads PyTorch 2.14.0 / tlparse 0.4.3 bundles without requiring ML runtimes for analysis.

- Reconstruct compilation identities, attempts, outcomes and explicit recompilation evidence; preserve unknowns, failures, graph breaks and compiler limits.
- Compare conservatively across source edits, show workload-manifest differences, and retain immutable baseline/candidate source and original evidence.
- Share versioned reports across CLI, three MCP tools and editor import/comparison/navigation commands; bound untrusted inputs and evidence retrieval.
- Include twelve controlled scenarios, an authored edit pair, a Transformers `generate()` case, tool-processing benchmarks, a 60-attempt agent pilot and a recorded demo.
- Correct malformed source-map acceptance, display guard categories on both sides, and keep source/evidence/table views in the active editor group.
- Distribute a wheel, source archive and VSIX through GitHub Releases, with installation instructions, checksums and build evidence.

The visual walkthrough was removed from the repository and release downloads in a documentation-only revision. Analyzer and editor runtime behavior are unchanged.

The pilot shows no demonstrated end-to-end agent improvement. CPU compiler evidence does not establish an application-speed benefit. Reviews are AI-reviewed; the approved scope makes independent human review optional. The initial 0.1.0 distribution used the public repository and [GitHub release](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0). Later Python and editor publications are described above. External adoption remains unclaimed.
