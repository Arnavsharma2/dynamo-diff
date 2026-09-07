# PyPI publication

Python analyzer 0.1.1 is [published on PyPI](https://pypi.org/project/dynamo-diff/0.1.1/) through [this successful workflow](https://github.com/Arnavsharma2/dynamo-diff/actions/runs/34166470273). The [publication receipt](../artifacts/pypi-publication-0.1.1.json) records matching public downloads and fresh macOS/Linux installations. The earlier GitHub analyzer release remains available.

## Publisher configuration

The owning PyPI account is `Arnavsharma2`. The initial GitHub pending publisher used this configuration and became an active publisher after the first release:

| Field | Value |
|---|---|
| PyPI project name | `dynamo-diff` |
| GitHub owner | `Arnavsharma2` |
| Repository | `dynamo-diff` |
| Workflow filename | `publish-pypi.yml` |
| Environment | `pypi` |

The [PyPI documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) explains pending publishers. The first successful workflow publication creates the project. This configuration uses GitHub OIDC and does not require a persistent PyPI API token in the repository.

## Release workflow

The manually dispatched [publishing workflow](../.github/workflows/publish-pypi.yml) accepts only the `codex/dynamo-diff` branch. The GitHub `pypi` environment is configured to allow only that branch. The workflow:

1. Checks that package metadata and CLI versions agree.
2. Builds a source archive and builds the wheel from that archive with the pinned build dependencies.
3. Tests the installed wheel, schemas, recorded demonstrations and evaluation harness without ML runtimes.
4. Transfers the verified distributions to a separate publishing job. Only that job has `id-token: write`; it publishes using PyPA's pinned action and its default attestations.
5. Installs the exact published version and MCP extra from the public PyPI index in a new environment, checks dependencies, and reruns the installed-package checks.

After the publisher is configured and source CI passes, dispatch with:

```sh
gh workflow run publish-pypi.yml --ref codex/dynamo-diff
```

Wait for all jobs, verify the public wheel/source archive hashes against the workflow's `python-distributions` artifact, and record a versioned publication receipt. Also verify the base installation from PyPI locally without PyTorch, then the optional MCP extra. Update the user-facing installation instructions and Marketplace README only after public installation succeeds. Keep historical release receipts intact.
