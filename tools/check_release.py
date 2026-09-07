"""Run reproducible core release checks against an installed package."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import dynamo_diff
from dynamo_diff.compare import Comparison
from dynamo_diff.model import Capture

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True, timeout=180)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-wheel", action="store_true")
    parser.add_argument("--junit", type=Path)
    args = parser.parse_args()
    if args.require_wheel:
        if "site-packages" not in Path(dynamo_diff.__file__).parts:
            raise SystemExit(f"Expected an installed wheel; imported {dynamo_diff.__file__}")
        for name in ("torch", "transformers"):
            if importlib.util.find_spec(name) is not None:
                raise SystemExit(f"The inspection-only release check must not have {name} installed")
    print(f"Package under test: {dynamo_diff.__file__}", flush=True)
    for name, model in (("capture", Capture), ("comparison", Comparison)):
        recorded = json.loads((ROOT / f"docs/schemas/{name}-v1.schema.json").read_text())
        if recorded != model.model_json_schema():
            raise SystemExit(f"The checked-in {name} schema does not match the installed model")
    pytest = ["-m", "pytest", "-q", "-o", "pythonpath=", "--import-mode=importlib"]
    if args.junit:
        args.junit.parent.mkdir(parents=True, exist_ok=True)
        pytest.append(f"--junitxml={args.junit.resolve()}")
    run(*pytest)
    run("tools/demo.py")
    run("case_studies/transformers_cache/verify.py")
    print("Core release checks passed. Human review, agent evaluation and editor/release gates are separate.")


if __name__ == "__main__":
    main()
