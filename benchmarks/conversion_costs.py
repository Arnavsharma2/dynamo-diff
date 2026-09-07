"""Measure external tlparse conversion separately from Dynamo Diff imports."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tlparse", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks/results/conversion-baseline.json")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.output.exists() or args.repeats < 3:
        raise SystemExit("Use a new output path and at least three repetitions")
    executable = args.tlparse.resolve()
    version = subprocess.run([str(executable), "--version"], text=True, capture_output=True, check=True, timeout=15).stdout.strip()
    if version != "tlparse 0.4.3":
        raise SystemExit(f"Expected pinned tlparse 0.4.3; got {version}")
    result = {"created_at": datetime.now(timezone.utc).isoformat(), "tlparse": version,
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "method": "External converter wall time including process startup, fresh output directory per trial, OS filesystem cache not flushed; no Dynamo Diff import or workload execution included.",
        "cases": []}
    with tempfile.TemporaryDirectory(prefix="dynamo-diff-conversion-") as temporary:
        for case in ["multiple_guards", "edit_before", "edit_after"]:
            logs = list((ROOT / f"fixtures/captures/{case}/raw").glob("*.log"))
            if len(logs) != 1:
                raise RuntimeError(f"Expected one retained raw trace for {case}")
            raw = logs[0]
            trials = []
            for trial in range(args.repeats):
                output = Path(temporary) / f"{case}-{trial}"
                start = time.perf_counter()
                process = subprocess.run([str(executable), str(raw), "--no-browser", "--plain-text", "-o", str(output)],
                    capture_output=True, text=True, timeout=120)
                elapsed = time.perf_counter() - start
                if process.returncode or not (output / "raw.jsonl").is_file():
                    raise RuntimeError(process.stderr or "Missing metadata export")
                trials.append({"seconds": elapsed, "output_bytes": sum(p.stat().st_size for p in output.rglob("*") if p.is_file())})
            result["cases"].append({"case": case, "raw_bytes": raw.stat().st_size,
                "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
                "median_seconds": statistics.median(t["seconds"] for t in trials), "trials": trials})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({case["case"]: case["median_seconds"] for case in result["cases"]}, indent=2))


if __name__ == "__main__":
    main()
