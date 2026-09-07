"""Capture the actual Transformers generate() path before/after eager cache setup."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "captures")
    args = parser.parse_args()
    for name, expected in [("torch", "2.14.0"), ("tlparse", "0.4.3"), ("transformers", "5.10.1")]:
        if importlib.metadata.version(name) != expected:
            raise SystemExit(f"This reproduction requires {name}=={expected}")
    output = args.output.resolve()
    for name in ["baseline", "candidate"]:
        if (output / name).exists():
            raise SystemExit(f"Refusing to overwrite capture: {output / name}")
    worker = ROOT / ".cache/transformers-case-worker/run.py"
    worker.parent.mkdir(parents=True, exist_ok=True)
    template = (HERE / "workload.py.in").read_text()
    results = []
    for name, preparation in [("baseline", "# Cache initializes lazily inside the first compiled prefill."),
                              ("candidate", "cache.early_initialization(1, 2, 8, torch.float32, torch.device('cpu'))")]:
        bundle = output / name
        (bundle / "raw").mkdir(parents=True)
        (bundle / "sources").mkdir()
        worker.write_text(template.replace("# CACHE_PREPARATION", preparation))
        shutil.copyfile(worker, bundle / "sources/run.py")
        result_path = bundle / "workload-result.json"
        env = dict(os.environ, TORCH_TRACE=str(bundle / "raw"), TORCH_LOGS="recompiles,graph_breaks",
            HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", OMP_NUM_THREADS="1")
        run = subprocess.run([sys.executable, str(worker), str(result_path)], env=env, capture_output=True, text=True, timeout=180)
        (bundle / "stdout.txt").write_text(run.stdout)
        (bundle / "stderr.txt").write_text(run.stderr)
        if run.returncode:
            raise SystemExit(f"Workload failed; inspect {bundle / 'stderr.txt'}")
        raw = list((bundle / "raw").glob("*.log"))
        if len(raw) != 1:
            raise SystemExit(f"Expected one raw trace; got {len(raw)}")
        converter = Path(sys.executable).parent / "tlparse"
        conversion = subprocess.run([str(converter), str(raw[0]), "--no-browser", "--plain-text", "-o", str(bundle / "report")],
            capture_output=True, text=True, timeout=120)
        (bundle / "conversion.txt").write_text(conversion.stdout + conversion.stderr)
        if conversion.returncode:
            raise SystemExit(f"Conversion failed; inspect {bundle / 'conversion.txt'}")
        result = json.loads(result_path.read_text())
        records = [json.loads(line) for line in (bundle / "report/raw.jsonl").read_text().splitlines()]
        source_paths = set(result["source_paths"]) | set(records[0]["string_table"])
        source_files = []
        for raw_path in sorted(source_paths):
            path = Path(raw_path)
            if not path.is_file() or path.suffix != ".py":
                continue
            if path == worker:
                relative, snapshot = "case_studies/transformers_cache/run.py", "sources/run.py"
            elif "site-packages" in path.parts:
                relative = "/".join(path.parts[path.parts.index("site-packages") + 1:])
                if not relative.startswith(("torch/", "transformers/")):
                    continue
                snapshot = f"sources/{relative}"
            else:
                continue
            target = bundle / snapshot
            target.parent.mkdir(parents=True, exist_ok=True)
            if path != worker:
                shutil.copyfile(path, target)
            source_files.append({"captured_path": str(path), "relative_path": relative, "snapshot": snapshot, "sha256": digest(target)})
        calls = [{key: call[key] for key in ["request", "input_ids", "shape", "strides", "dtype", "device",
            "requires_grad", "grad_enabled", "model_training", "attention_mask"]} for call in result["calls"]]
        manifest = {"schema_version": "1", "producer": {"python": sys.version.split()[0], "torch": result["torch"],
            "torch_git": result["torch_git"], "tlparse": "0.4.3", "transformers": result["transformers"]},
            "source": {"revision": None, "dirty_patch_sha256": None, "driver_sha256": digest(worker), "files": source_files},
            "workload": {"calls": calls, "seed": 101, "backend": "recording_eager", "dynamic": False,
                "backend_options": {"fullgraph": True, "mode": "default", "compile_all_devices": True},
                "model_config": result["model_config"], "parameter_hashes": result["parameter_hashes"],
                "device": "cpu", "warmup_calls": 0, "measurement_calls": None,
                "cache_policy": "fresh_process_no_inductor_fresh_static_cache_reset_between_requests",
                "cache_directories": [], "environment": {"OMP_NUM_THREADS": "1", "HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1"},
                "generation": {"max_new_tokens": 3, "prefill_chunk_size": 8, "do_sample": False,
                    "max_cache_len": 16, "attention_implementation": "eager", "requests": 3}},
            "capture": {"workload_completed": True, "process_exit_code": run.returncode,
                "converter_exit_code": conversion.returncode, "report_sha256": digest(bundle / "report/raw.jsonl"),
                "raw_traces": [{"path": str(path.relative_to(bundle)), "sha256": digest(path)} for path in raw],
                "result_sha256": digest(result_path)}}
        (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        results.append(result)
        print(f"{name}: backend totals {[call['backend_calls_after'] for call in result['calls']]}", flush=True)
    if results[0]["parameter_hashes"] != results[1]["parameter_hashes"]:
        raise SystemExit("Model weights differ between source variants")
    for left, right in zip(results[0]["calls"], results[1]["calls"], strict=True):
        if left["output_tokens"] != right["output_tokens"] or left["output_logits_sha256"] != right["output_logits_sha256"]:
            raise SystemExit("Before/after outputs differ; inspect the recorded numerical results")
    print("Before/after weights, tokens and logit hashes agree; each run passed its separate eager oracle.")


if __name__ == "__main__":
    main()
