# First feasibility gate

**Result: proceed with the scoped implementation.**

The pinned PyTorch 2.14.0 / tlparse 0.4.3 pair exposes enough evidence to identify completed and failed compilation outcomes, explicit recompilation reasons, internal attempts, graph breaks, source locations, and relevant compiler configurations. Twelve controlled compiler scenarios and an actual before/after source-edit pair have been captured successfully.

The before/after pair is an early demonstration of differentiation:

- The baseline `compute` function produces three completed compilations, including two confirmed recompilations.
- The candidate `compute` function produces one completed compilation, with no confirmed recompilation.
- Adding a helper shifts `compute` from frame ID 0 to frame ID 1. The comparator matches its source boundary rather than joining on the numeric ID.
- The new helper is retained as an unmatched function and counted in candidate totals.
- Changed workload inputs in the separate shape fixture are labeled confounded.

Plain tlparse output exposes the component artifacts but does not itself supply this semantic correspondence and workload gate. The comparator consolidates that evidence into one report. This demonstrates useful functionality; it does **not** establish measured developer productivity, adoption, performance improvement, or product demand. Those remain later requirements.

Current upstream interfaces were checked against the scope: tlparse supports text intended for diffing; TritonParse already supplies kernel/whole-trace comparison. Dynamo Diff remains narrowly about Dynamo compilation identities, guard evidence, and conservative source correspondence.

## Reproduce the current demonstration

From an environment with the package installed:

```sh
dynamo-diff import fixtures/captures/edit_before/report --manifest fixtures/captures/edit_before/manifest.json
dynamo-diff import fixtures/captures/edit_after/report --manifest fixtures/captures/edit_after/manifest.json
dynamo-diff compare BASELINE_CAPTURE_ID CANDIDATE_CAPTURE_ID --format markdown
```

Capture IDs are printed by import and deliberately not hard-coded; adapter revisions invalidate older reports. `python tools/generate_edit_pair.py --output .cache/regenerated-edit-pair` regenerates the original pair into a new directory. It refuses to overwrite existing captures, including the checked-in examples.
