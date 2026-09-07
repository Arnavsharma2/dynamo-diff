# Capture recipe and manifests

## Use the controlled recipe first

From the checkout, with the fixture extra installed under the pinned toolchain:

```sh
python -m pip install '.[fixtures]'
python tools/generate_fixtures.py stable shape scalar multiple_guards --output .cache/new-captures
python tools/generate_edit_pair.py --output .cache/new-edit-pair
python tools/demo.py --captures .cache/new-edit-pair
```

Output directories must be new. Both generators refuse to overwrite retained captures. They run authored CPU workloads in fresh subprocesses, convert their traces, snapshot the source and write manifests with actual process/converter status and artifact hashes. The original bundles remain under `fixtures/captures` for offline inspection.

## Capture your application

Use PyTorch 2.14.0 and tlparse 0.4.3 for this adapter. Before the diagnostic run, copy the exact source files and record their paths and SHA-256 hashes. Record the Git revision and dirty patch hash when available. Keep ordered input descriptions, seed, compiler backend/options, grad/eval mode, device and cache policy.

Run your normal application command with `TORCH_TRACE` pointing to a new directory. For example, substitute your actual workload for `your_workload.py`:

```sh
TORCH_TRACE=/absolute/path/to/bundle/raw TORCH_LOGS=recompiles,graph_breaks python your_workload.py
```

Record its exit status immediately. Convert the single-process trace after the workload exits; replace the example filename with the one emitted:

```sh
tlparse /absolute/path/to/bundle/raw/trace.log --no-browser --plain-text -o /absolute/path/to/bundle/report
```

Record the converter exit status and keep the original raw log. Do not concatenate process logs. The supported export is `report/raw.jsonl` plus referenced payloads; human-readable text alone is insufficient.

Populate [manifest.template.json](manifest.template.json) from the actual run, then import:

```sh
dynamo-diff import /absolute/path/to/bundle/report --manifest /absolute/path/to/bundle/manifest.json
```

Import without `--manifest` still works, with unknown workload completion/comparability and potentially unresolved source matching. The analyzer never executes the workload to fill missing fields.

## Manifest fields

`producer` records the exact Python, PyTorch, PyTorch Git commit and tlparse versions used. `source.files` contains entries of this form, using actual values:

```json
{
  "captured_path": "/absolute/path/from/the/trace/model.py",
  "relative_path": "model.py",
  "snapshot": "sources/model.py",
  "sha256": "REPLACE_WITH_THE_SNAPSHOT_SHA256"
}
```

Snapshot and raw-trace paths are relative to the manifest directory and must stay inside it. `relative_path` is a stable comparison identity across checkouts; `captured_path` associates that snapshot with the trace. Do not relabel two unrelated files with the same relative identity.

`workload.calls` describes the ordered inputs, including relevant tensor shapes, strides, dtypes, device, requires-grad state, scalar arguments and model mode. Record warmup and measurement boundaries separately. `dynamic` follows `torch.compile`: `false` is static, `true` is dynamic, and explicit `null` means its automatic policy. Omit `dynamic` if unknown; unlike other required fields, its explicit null has a defined meaning. Empty/null required backend, version, seed and other declarations cannot establish comparability.

Record relevant environment settings explicitly rather than dumping every environment variable. A fresh process does not imply a cold persistent compiler cache. `cache_policy` and `cache_directories` must describe disk cache behavior; `torch._dynamo.reset()` is not a universal cold-cache reset. The controlled recording backend does not invoke Inductor.

The `capture` completion declaration is accepted only when the manifest marks the workload completed, both process and converter exit codes are zero, `report_sha256` matches the exact `raw.jsonl` bytes, and `raw_traces` contains verified path/hash entries. The result is **declared completed**. This binds a declaration to artifacts; it is not proof from an independent observer. Missing finalization leaves completion unknown, and stale hash claims are rejected.

Do not claim completion after cutting a valid-looking prefix from a longer run. Keep compiler failures/no-graph events in the capture even when the application handles them. A diagnostic trace is separate from an application timing experiment; use separate correctness checks and repeated timing runs before making speed claims.
