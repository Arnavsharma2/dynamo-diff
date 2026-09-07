"""Record an offline CLI walkthrough from actual subprocess output (asciicast v2)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time

from dynamo_diff.store import Store

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pause", type=float, default=5, help="Actual presentation pause after each command, not a performance measurement")
    args = parser.parse_args()
    if not 0 <= args.pause <= 15:
        raise SystemExit("Use a presentation pause between 0 and 15 seconds")
    if args.output.exists():
        raise SystemExit("Choose a new output directory; recordings are not overwritten")
    args.output.mkdir(parents=True)
    started = time.monotonic()
    events, steps, transcript = [], [], []

    def emit(text):
        transcript.append(text)
        events.append([round(time.monotonic() - started, 6), "o", text.replace("\n", "\r\n")])

    with tempfile.TemporaryDirectory(prefix="dynamo-diff-cli-demo-") as temporary:
        store_path = Path(temporary) / "store"
        base = [sys.executable, "-m", "dynamo_diff.cli", "--store", str(store_path)]

        def command(title, arguments, expected_status=0):
            events.append([round(time.monotonic() - started, 6), "m", title])
            emit(f"\n# {title}\n$ {shlex.join(arguments)}\n")
            before = time.monotonic()
            result = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, timeout=60)
            elapsed = time.monotonic() - before
            emit(result.stdout)
            if result.stderr:
                emit(result.stderr)
            emit(f"[exit {result.returncode}]\n")
            steps.append({"title": title, "argv": arguments, "exit_code": result.returncode,
                "subprocess_wall_seconds": elapsed, "stdout": result.stdout, "stderr": result.stderr})
            if result.returncode != expected_status:
                raise SystemExit(f"Unexpected command status: {title}")
            time.sleep(args.pause)
            return result.stdout

        emit("Dynamo Diff: recorded offline CLI walkthrough\nSaved compiler captures; no PyTorch, model inference, workload execution or speed claim.\nPresentation pauses are intentional. Command output is retained verbatim.\n")
        ids = []
        for name, title in (("edit_before", "1. Import the baseline"), ("edit_after", "2. Import the candidate")):
            bundle = ROOT / "fixtures/captures" / name
            output = command(title, [*base, "import", str(bundle / "report"), "--manifest", str(bundle / "manifest.json")])
            ids.append(json.loads(output)["capture_id"])
        comparison = command("3. Compare functions, workload declarations and counts", [*base, "compare", *ids])
        if "Application performance: not measured." not in comparison:
            raise SystemExit("Comparison lost the explicit unmeasured-performance conclusion")
        store = Store(store_path)
        capture = store.load(ids[0])
        reason = next(e for e in capture.evidence.values() if e.kind == "recompile_reasons")
        evidence = command("4. Inspect an original guard reason and its artifact hash", [*base, "evidence", ids[0], reason.id])
        if not json.loads(evidence)["sha256"]:
            raise SystemExit("Evidence provenance is missing")
        command("5. Verify the authored edit and the unmatched helper", [sys.executable, "tools/demo.py"])
        emit("\nThe edited compute function matched automatically. The added helper remains in totals.\nFewer compilations do not establish an application speedup.\n")
    duration = time.monotonic() - started
    header = {"version": 2, "width": 140, "height": 46, "timestamp": int(time.time() - duration),
        "duration": duration, "title": "Dynamo Diff offline CLI walkthrough", "idle_time_limit": 5}
    cast = args.output / "walkthrough.cast"
    cast.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in [header, *events]) + "\n")
    (args.output / "transcript.txt").write_text("".join(transcript))
    receipt = {"created_at": datetime.now(timezone.utc).isoformat(), "python_executable": sys.executable,
        "recording_kind": "Actual CLI subprocess output with narrated command labels and intentional presentation pauses; not a native editor video or a benchmark",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "presentation_pause_seconds": args.pause, "recording_seconds": duration, "steps": steps,
        "recording_sha256": hashlib.sha256(cast.read_bytes()).hexdigest()}
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "commands_passed": len(steps), "recording_seconds": duration}))


if __name__ == "__main__":
    main()
