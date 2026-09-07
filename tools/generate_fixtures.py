"""Generate controlled local compiler captures; never called by the analyzer."""

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

ROOT = Path(__file__).resolve().parents[1]
WORKLOAD = ROOT / "fixtures/workloads/compiler_cases.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", nargs="*", default=["stable", "shape", "scalar", "multiple_guards", "dynamic", "grad"])
    parser.add_argument("--output", type=Path, default=ROOT / "fixtures/captures")
    args = parser.parse_args()
    tlparse = Path(sys.executable).parent / "tlparse"
    for case in args.cases:
        dest = (args.output / case).resolve()
        if dest.exists():
            raise SystemExit(f"Refusing to overwrite existing capture: {dest}")
        raw = dest / "raw"
        raw.mkdir(parents=True)
        (dest / "sources").mkdir()
        shutil.copyfile(WORKLOAD, dest / "sources/compiler_cases.py")
        env = dict(os.environ, TORCH_TRACE=str(raw), TORCH_LOGS="recompiles,graph_breaks", OMP_NUM_THREADS="1")
        result_path = dest / "workload-result.json"
        command = [sys.executable, str(WORKLOAD), case, "--result", str(result_path)]
        run = subprocess.run(command, env=env, text=True, capture_output=True, timeout=120)
        (dest / "stdout.txt").write_text(run.stdout)
        (dest / "stderr.txt").write_text(run.stderr)
        if run.returncode:
            raise SystemExit(f"Workload failed ({run.returncode}): {dest / 'stderr.txt'}")
        raw_files = sorted(raw.glob("*.log"))
        if len(raw_files) != 1:
            raise SystemExit(f"Expected one raw trace; found {len(raw_files)} in {raw}")
        report = dest / "report"
        convert = subprocess.run([str(tlparse), str(raw_files[0]), "--no-browser", "--plain-text", "-o", str(report)],
                                 text=True, capture_output=True, timeout=120)
        (dest / "conversion.txt").write_text(convert.stdout + convert.stderr)
        if convert.returncode:
            raise SystemExit(f"Conversion failed: {dest / 'conversion.txt'}")
        result = json.loads(result_path.read_text())
        manifest = {
            "schema_version": "1", "producer": {"python": sys.version.split()[0],
                "torch": result["torch_version"], "torch_git": result["torch_git_version"],
                "tlparse": importlib.metadata.version("tlparse")},
            "source": {"revision": None, "files": [{"captured_path": str(WORKLOAD),
                "relative_path": "fixtures/workloads/compiler_cases.py", "snapshot": "sources/compiler_cases.py",
                "sha256": sha256(dest / "sources/compiler_cases.py")}]},
            "workload": {"calls": [{k: v for k, v in c.items() if k not in ["backend_calls_so_far", "output_correct"]}
                for c in result["calls"]], "seed": 2026, "backend": "recording_eager",
                "dynamic": None if case == "dynamic" else False, "device": "cpu",
                "warmup_calls": 0, "cache_policy": "fresh_process_no_inductor", "environment": {"OMP_NUM_THREADS": "1"}},
            "capture": {"workload_completed": True, "process_exit_code": run.returncode,
                "converter_exit_code": convert.returncode, "report_sha256": sha256(report / "raw.jsonl"),
                "raw_traces": [{"path": str(p.relative_to(dest)), "sha256": sha256(p)} for p in raw_files],
                "result_sha256": sha256(result_path)},
        }
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"{case}: backend calls={len(result['backend_calls'])}; report={report}", flush=True)


if __name__ == "__main__":
    main()
