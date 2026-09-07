# Public release review: 0.1.0

The first public release distributes the saved-capture analyzer and VS Code extension through [GitHub Releases](https://github.com/Arnavsharma2/dynamo-diff/releases/tag/v0.1.0). It includes the Python wheel, source archive, VSIX, release receipt and SHA-256 checksums. [Installation instructions](INSTALL.md) explain how to use them. The release tag identifies the source commit; the attached receipt identifies the build files and validation run.

## Repository and capture review

Before publication, the seven existing history commits, 751 unique Git blobs, nested archived source and all six existing hosted CI logs were reviewed with a bounded credential-pattern scan and manual provenance checks. The initial scan covered 21,068,430 bytes and 16 nested archived files and found no credential-pattern matches. The release receipt records the final scan after adding release files and packages.

The scan checks common private-key headers, token formats, credentials in URLs and quoted secret assignments. It is a targeted check, not an exhaustive secret-detection guarantee. The corpus contains authored workloads and attributed upstream PyTorch/Transformers source. Original local capture paths are preserved so raw evidence and frozen hashes remain unchanged. Commit authors use a GitHub noreply address. Upstream contact information and license texts remain attributed in [third-party notices](THIRD_PARTY_NOTICES.md).

## Build and validation

The public packages rebuild version 0.1.0 with release documentation and repository metadata. Analyzer and editor runtime code are unchanged from the verified portfolio implementation. The earlier [portfolio delivery receipt](../artifacts/portfolio-v1-delivery.json) remains a historical record; its package hashes must not be substituted for the new release downloads.

Validation includes the installed-wheel core suite, both offline demonstrations, evaluation-harness checks, hosted macOS/Linux core jobs and the Linux development/installed-VSIX checks. The release receipt records exact results, source commit, CI URL and final asset hashes. The visual presentation and its public download assets were removed in a documentation-only revision; the recorded compiler inputs remain available for local inspection.

## Claim boundaries

This is a public software release with measured compiler evidence. There is no PyPI or Marketplace publication, external adoption claim, CUDA/Inductor speedup claim or demonstrated end-to-end agent improvement. The 60-attempt pilot's negative primary result remains unchanged. Reviews are AI-reviewed under the approved scope; independent human review remains optional and unclaimed.
