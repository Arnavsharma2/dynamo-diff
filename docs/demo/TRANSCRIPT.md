# Dynamo Diff release walkthrough

This 72-second presentation uses actual CLI output from the retained authored captures. It is paced for reading, not a native editor recording or a runtime benchmark. `receipt.json` retains commands, original stdout, exit codes and hashes.

1. **0–8 seconds:** the baseline has three completed compilations; the candidate has two.
2. **8–20 seconds:** the candidate removes a redundant scalar branch and adds a helper. The source excerpts omit only the explanatory comment.
3. **20–34 seconds:** `compute` matches across changed source hashes/frame IDs, moving from three to one completed compilations and two to zero confirmed recompiles. The unmatched helper remains in totals.
4. **34–50 seconds:** baseline evidence contains `step == 1`, the original `if step > 0` context, artifact path, record number and SHA-256. The displayed hash is shortened; the complete value is in the receipt.
5. **50–62 seconds:** source correspondence, workload declarations and application performance are separate. Manifest consistency is not runtime-equivalence proof; application speed is not measured.
6. **62–72 seconds:** use the recorded CLI example or the VS Code import/compare flow. The local MCP interface is experimental; the existing pilot found no end-to-end agent improvement.
