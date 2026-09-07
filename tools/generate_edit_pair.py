"""Capture an actual source edit with unchanged inputs and shifted frame IDs."""

from __future__ import annotations

import hashlib
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '''import json
from pathlib import Path
import sys
import torch

torch.manual_seed(2026)
torch.set_num_threads(1)

'''
BEFORE = '''def compute(x, step):
    if step > 0:
        return x.sin() * 2
    return x.sin() * 2

'''
AFTER = '''def compute(x, step):
    # The output never depended on step; remove the redundant specialization.
    return x.sin() * 2

'''
SUFFIX = '''backend_calls = []
def recording_backend(graph, inputs):
    backend_calls.append(graph.code)
    return graph.forward

def helper(x):
    return x + 1

if VARIANT == "after":
    torch.compile(helper, backend=recording_backend, dynamic=False)(torch.ones(4))

compiled = torch.compile(compute, backend=recording_backend, dynamic=False)
calls = []
for step in [1, 2, 3]:
    x = torch.arange(4, dtype=torch.float32)
    value = compiled(x, step)
    torch.testing.assert_close(value, x.sin() * 2)
    calls.append({"shape": [4], "dtype": "float32", "device": "cpu", "step": step, "output_correct": True})
Path(sys.argv[1]).write_text(json.dumps({"calls": calls, "backend_calls": backend_calls,
    "torch_version": torch.__version__, "torch_git": torch.version.git_version}, indent=2))
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "fixtures/captures", help="Parent directory for edit_before and edit_after; existing captures are never overwritten")
    args = parser.parse_args()
    output = args.output.resolve()
    for variant in ["before", "after"]:
        if (output / f"edit_{variant}").exists():
            raise SystemExit(f"Refusing to overwrite {output / f'edit_{variant}'}")
    worker = ROOT / ".cache/edited-workload/model.py"
    worker.parent.mkdir(parents=True, exist_ok=True)
    for variant, body in [("before", BEFORE), ("after", AFTER)]:
        dest = output / f"edit_{variant}"
        if dest.exists():
            raise SystemExit(f"Refusing to overwrite {dest}")
        (dest / "raw").mkdir(parents=True)
        (dest / "sources").mkdir()
        worker.write_text(PREFIX + body + f'VARIANT = "{variant}"\n' + SUFFIX)
        shutil.copyfile(worker, dest / "sources/model.py")
        result_path = dest / "workload-result.json"
        env = dict(os.environ, TORCH_TRACE=str(dest / "raw"), TORCH_LOGS="recompiles,graph_breaks", OMP_NUM_THREADS="1")
        run = subprocess.run([sys.executable, str(worker), str(result_path)], env=env, capture_output=True, text=True, timeout=120)
        (dest / "stdout.txt").write_text(run.stdout)
        (dest / "stderr.txt").write_text(run.stderr)
        if run.returncode:
            raise SystemExit(run.stderr)
        raw_files = list((dest / "raw").glob("*.log"))
        assert len(raw_files) == 1
        convert = subprocess.run([str(Path(sys.executable).parent / "tlparse"), str(raw_files[0]), "--no-browser", "--plain-text", "-o", str(dest / "report")],
                                 capture_output=True, text=True, timeout=120)
        (dest / "conversion.txt").write_text(convert.stdout + convert.stderr)
        if convert.returncode:
            raise SystemExit(convert.stderr)
        result = json.loads(result_path.read_text())
        manifest = {"schema_version": "1", "producer": {"python": sys.version.split()[0], "torch": result["torch_version"],
                    "torch_git": result["torch_git"], "tlparse": importlib.metadata.version("tlparse")},
            "source": {"files": [{"captured_path": str(worker), "relative_path": "model.py", "snapshot": "sources/model.py", "sha256": digest(worker)}]},
            "workload": {"calls": [{k:v for k,v in call.items() if k != "output_correct"} for call in result["calls"]], "seed": 2026,
                "backend": "recording_eager", "dynamic": False, "device": "cpu", "warmup_calls": 0,
                "cache_policy": "fresh_process_no_inductor", "environment": {"OMP_NUM_THREADS": "1"}},
            "capture": {"workload_completed": True, "process_exit_code": run.returncode, "converter_exit_code": convert.returncode,
                "report_sha256": digest(dest / "report/raw.jsonl"), "raw_traces": [{"path": str(p.relative_to(dest)), "sha256": digest(p)} for p in raw_files]}}
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"edit_{variant}: backend invocations={len(result['backend_calls'])}", flush=True)


if __name__ == "__main__":
    main()
