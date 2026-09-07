# Changelog

## 0.1.0 — September 7, 2026

Initial public release of the saved-capture analyzer, local MCP server and VS Code extension. The tested adapter reads PyTorch 2.14.0 / tlparse 0.4.3 bundles without requiring ML runtimes for analysis.

- Reconstruct compilation identities, attempts, outcomes and explicit recompilation evidence; preserve unknowns, failures, graph breaks and compiler limits.
- Compare conservatively across source edits, show workload-manifest differences, and retain immutable baseline/candidate source and original evidence.
- Share versioned reports across CLI, three MCP tools and editor import/comparison/navigation commands; bound untrusted inputs and evidence retrieval.
- Include twelve controlled scenarios, an authored edit pair, a Transformers `generate()` case, tool-processing benchmarks, a 60-attempt agent pilot and a recorded demo.
- Correct malformed source-map acceptance, display guard categories on both sides, and keep source/evidence/table views in the active editor group.
- Distribute a wheel, source archive and VSIX through GitHub Releases, with installation instructions, checksums and build evidence.

The visual walkthrough was removed from the repository and release downloads in a documentation-only revision. Analyzer and editor runtime behavior are unchanged.

The pilot shows no demonstrated end-to-end agent improvement. CPU compiler evidence does not establish an application-speed benefit. Reviews are AI-reviewed; the approved scope makes independent human review optional. This version is delivered through the public repository and [GitHub release](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0), with no PyPI or Marketplace publication or external-adoption claim.
