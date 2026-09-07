"""Generate fresh, neutrally named held-out captures; never called during model trials."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(size=6, argument=2, dtype="float32", requires_grad=False, module_index=None):
    return {"shape": [size], "strides": [1], "dtype": dtype, "requires_grad": requires_grad,
        "device": "cpu", "grad_enabled": True, "argument": argument, "module_index": module_index}


STANDARD = "def f(x, argument):\n    return x.cos() * argument + x.tanh()\n"
TAG_BEFORE = "def f(x, argument):\n    if argument in ('east', 'north'):\n        return x.cos() + 1\n    return x.cos() + 1\n"
TAG_AFTER = "def f(x, argument):\n    return x.cos() + 1\n"
BREAK = "def f(x, argument):\n    z = x.cos()\n    torch._dynamo.graph_break()\n    return z.tanh() + argument\n"
MODULE = "class M(torch.nn.Module):\n    def forward(self, x, argument):\n        return x.cos() * argument + id(self)\n"


def settings(calls, **extra):
    return {"calls": calls, "seed": 731, **extra}


def cases():
    return {
        "q01": {"a": (STANDARD, settings([call(6), call(11), call(6), call(6)]))},
        "q02": {"a": (STANDARD, settings([call(argument=i) for i in [-3, 5, 9]]))},
        "q03": {"a": (TAG_BEFORE, settings([call(argument=i) for i in ["east", "north", "west"]])),
                "b": (TAG_AFTER, settings([call(argument=i) for i in ["east", "north", "west"]]))},
        "q04": {"a": (STANDARD, settings([call(6), call(12), call(6)])),
                "b": (STANDARD, settings([call(6)] * 3))},
        "q05": {"a": (STANDARD, settings([call()])),
                "b": (STANDARD, settings([call()], backend_raises=True))},
        "q06": {"a": (STANDARD, settings([call(argument=i) for i in [4, 7, 10, 4]])),
                "b": (STANDARD, settings([call(argument=i) for i in [4, 7, 10, 4]], recompile_limit=2))},
        "q07": {"a": (STANDARD, settings([call(6), call(11), call(6)]))},
        "q08": {"a": (BREAK, settings([call(9)] * 2))},
        "q09": {"a": (MODULE, settings([call(module_index=i) for i in range(3)], modules=True))},
        "q10": {"a": (STANDARD, settings([call(), call(dtype="float64"), call(dtype="float64", requires_grad=True)]))},
    }


def convert(raw: Path, report: Path) -> None:
    converter = Path(sys.executable).parent / "tlparse"
    result = subprocess.run([str(converter), str(raw), "--no-browser", "--plain-text", "-o", str(report)],
        text=True, capture_output=True, timeout=120)
    (report.parent / "conversion.txt").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Conversion failed: {report.parent}")


def capture(output: Path, question: str, variant: str, source: str, configuration: dict) -> None:
    bundle = output / "captures" / question / variant
    (bundle / "raw").mkdir(parents=True)
    (bundle / "sources").mkdir()
    worker = ROOT / ".cache/pilot-worker/model.py"
    worker.parent.mkdir(parents=True, exist_ok=True)
    worker.write_text((HERE / "driver.py.in").read_text().replace("# TARGET_DEFINITION", source))
    shutil.copyfile(worker, bundle / "sources/model.py")
    configuration_path = worker.with_name("inputs.json")
    configuration_path.write_text(json.dumps(configuration))
    outcome_path = bundle / "workload-result.json"
    env = dict(os.environ, TORCH_TRACE=str(bundle / "raw"), TORCH_LOGS="recompiles,graph_breaks", OMP_NUM_THREADS="1")
    run = subprocess.run([sys.executable, str(worker), str(configuration_path), str(outcome_path)],
        env=env, text=True, capture_output=True, timeout=120)
    (bundle / "stdout.txt").write_text(run.stdout)
    (bundle / "stderr.txt").write_text(run.stderr)
    if run.returncode:
        raise RuntimeError(f"Workload failed: {bundle / 'stderr.txt'}")
    raw_paths = list((bundle / "raw").glob("*.log"))
    if len(raw_paths) != 1:
        raise RuntimeError("Expected exactly one process trace")
    original = raw_paths[0]
    raw = original.with_name("trace.log")
    original.rename(raw)
    outcome = json.loads(outcome_path.read_text())
    producer = {"python": sys.version.split()[0], "torch": outcome["torch"], "torch_git": outcome["torch_git"], "tlparse": "0.4.3"}
    if question == "q07":
        # Preserve the full recording outside the agent-accessible bundle, then create
        # a cleanly truncated raw trace. Convert that prefix rather than editing JSONL.
        original_dir = output / "curator" / question
        original_dir.mkdir(parents=True)
        shutil.copyfile(raw, original_dir / "full-trace.log")
        shutil.copyfile(outcome_path, original_dir / "workload-result.json")
        lines = raw.read_text().splitlines(keepends=True)
        for index, line in enumerate(lines):
            if "compilation_metrics" not in line or "{" not in line:
                continue
            try:
                record = json.loads(line[line.index("{"):])
            except json.JSONDecodeError:
                continue
            if "compilation_metrics" in record:
                raw.write_text("".join(lines[:index + 1]))
                break
        else:
            raise RuntimeError("Cannot locate a terminal metadata boundary for truncation")
    convert(raw, bundle / "report")
    manifest = {"schema_version": "1", "producer": producer,
        "source": {"revision": None, "files": [{"captured_path": str(worker), "relative_path": "model.py",
            "snapshot": "sources/model.py", "sha256": digest(bundle / "sources/model.py")}]},
        "workload": {"calls": configuration["calls"], "seed": configuration["seed"],
            "backend": "failing_backend" if configuration.get("backend_raises") else "recording_eager",
            "backend_options": {"fullgraph": False}, "dynamic": False, "device": "cpu", "warmup_calls": 0,
            "cache_policy": "fresh_process_no_inductor", "environment": {"OMP_NUM_THREADS": "1"}},
        "capture": {"workload_completed": True, "process_exit_code": run.returncode, "converter_exit_code": 0,
            "report_sha256": digest(bundle / "report/raw.jsonl"),
            "raw_traces": [{"path": "raw/trace.log", "sha256": digest(raw)}], "result_sha256": digest(outcome_path)}}
    if "recompile_limit" in configuration:
        manifest["workload"]["recompile_limit"] = configuration["recompile_limit"]
    if question == "q07":
        # There is intentionally no trustworthy finalization declaration for this prefix.
        manifest.pop("capture")
        outcome_path.unlink()  # Full-run outcomes would reveal events absent from this artifact.
        (bundle / "stderr.txt").unlink()
        (bundle / "stdout.txt").unlink()
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{question}/{variant}: backend totals {[c['backend_calls_after'] for c in outcome['calls']]}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "corpus")
    args = parser.parse_args()
    for name, version in (("torch", "2.14.0"), ("tlparse", "0.4.3")):
        if importlib.metadata.version(name) != version:
            raise SystemExit(f"Requires {name}=={version}")
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite a corpus: {output}")
    output.mkdir(parents=True)
    files = sorted((ROOT / "src/dynamo_diff").rglob("*.py"))
    freeze = {"created_at": datetime.now(timezone.utc).isoformat(), "source_hashes": {
        str(path.relative_to(ROOT)): digest(path) for path in files},
        "generator_sha256": digest(Path(__file__)), "driver_sha256": digest(HERE / "driver.py.in"),
        "meaning": "Analyzer implementation recorded before fresh held-out captures were generated; model trials have not run."}
    (output / "implementation-freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
    for question, variants in cases().items():
        for variant, (source, configuration) in variants.items():
            capture(output, question, variant, source, configuration)
    print(f"Recorded {sum(len(v) for v in cases().values())} captures for {len(cases())} held-out questions")


if __name__ == "__main__":
    main()
