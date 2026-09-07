# Import and comparison measurements

These are tool-processing measurements on an **Apple M1 Pro MacBook Pro with 32 GiB RAM** (MacBookPro18,3), macOS arm64, Python 3.13.2/Pydantic 2.13.5. Hardware identifiers were checked locally after the run. They are not application-speed results or developer-productivity measurements. Individual trials are retained in [import-baseline.json](../benchmarks/results/import-baseline.json).

## Measured baseline

| Input target | Actual input | Median import, 3 trials | Maximum process peak RSS |
|---|---:|---:|---:|
| 10 MiB | 10,547,826 bytes | 0.949 s | 58.6 MiB |
| 100 MiB | 104,957,295 bytes | 9.460 s | 254.8 MiB |

Inputs replicate the actual `multiple_guards` metadata/payload structure into separate frame namespaces, without arbitrary padding. They are labeled **synthetic scale inputs**, not newly recorded large applications. The 100 MiB case contains 2,358 completed compilation identities, 1,572 confirmed successful recompilations and 6,289 payload files; each trial checks the expected counts. Its metadata accounts for about 93% of the imported bytes. Other artifact distributions, source sizes and operating systems may behave differently.

Each import runs in a fresh worker and a new store. Generation and process startup are excluded from the reported import time; parent process wall times are also retained. OS file caches were not flushed. Peak RSS includes Python/libraries and uses the operating system's high-water measurement. This is not a cold-disk benchmark.

The actual recorded source-edit pair was compared 20 times after one excluded warmup. Median comparison time was **1.242 ms**, with nearest-rank p95 **1.611 ms**. Each comparison reloads normalized data and checks the relevant snapshots. The pair contains two result rows; this is not a latency claim for thousands of matched functions.

The full comparison JSON was **8,033 characters/UTF-8 bytes**. The initial compact MCP result was **7,258 characters**, below the 12,000-character limit. These are this pair's output sizes, not a fixed reduction factor or an agent token-saving result.

## After input validation changes

Adapter revision 4 adds strict JSON validation, nested-manifest validation, regular-file checks and source-analysis bounds. [The retained rerun](../benchmarks/results/import-hardening-v4.json) uses the same input hashes, machine/profile and three trials per size:

| Input target | Median import | Maximum process peak RSS |
|---|---:|---:|
| 10 MiB | 1.349 s | 58.8 MiB |
| 100 MiB | 13.466 s | 254.7 MiB |

Import time increased about **42%** in this measurement; peak memory remained approximately unchanged. The extra validation has a measurable cost, and the original faster baseline remains labeled historical. The rerun stays within the previously defined 2× import and 1.5× memory investigation thresholds. The same tiny edit pair had a 1.371 ms median / 1.748 ms p95 warm comparison, with unchanged output sizes. This is one before/after measurement sequence, not a randomized causal estimate of each validation check's cost.

## Upstream conversion is separate

[conversion-baseline.json](../benchmarks/results/conversion-baseline.json) records three tlparse 0.4.3 conversion trials for each small retained raw trace. Median whole-process conversion times were about **12.8 ms** (`multiple_guards`), **13.3 ms** (`edit_before`) and **11.3 ms** (`edit_after`). Fresh output directories were used; OS caches were not flushed. Output byte counts and raw hashes are retained.

Those small-trace conversion timings cannot be extrapolated to the synthetic 100 MiB input. The import benchmark starts from converted exports and does not include conversion or workload runtime.

## Reproduce and detect regressions

With the installed analyzer available to Python:

```sh
python benchmarks/import_scaling.py --output .cache/import-candidate.json
python benchmarks/check_regression.py benchmarks/results/import-baseline.json .cache/import-candidate.json
python benchmarks/conversion_costs.py --tlparse /absolute/path/to/tlparse --output .cache/conversion-candidate.json
```

Measurement scripts refuse to overwrite results. The baseline uses three imports at each size and 20 warm comparisons. Run on comparable hardware with similar background load; the checker verifies recorded platform/profile and input identity, but cannot establish identical CPU load or physical hardware by itself.

After collecting the initial baseline, investigation thresholds were set to **2× median import time**, **1.5× peak RSS**, and **max(5 ms, 3× median)** for the tiny warm comparison. Exceeding a threshold means investigate and repeat the measurement; it is not proof of a bug. The MCP limit remains 12,000 characters. These thresholds are local regression controls, not advertised performance guarantees.
