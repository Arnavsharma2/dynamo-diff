"""Small owned workloads. Run only through tools/generate_fixtures.py.

The backend invocation log is an independent oracle for these one-graph cases;
it is not a general definition of Dynamo compilation count.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch


def compute(x: torch.Tensor, scale: int = 2) -> torch.Tensor:
    return x.sin() * scale


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["stable", "shape", "scalar", "multiple_guards", "dynamic", "grad"])
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(2026)
    torch.set_num_threads(1)
    backend_calls: list[dict] = []

    def recording_backend(graph: torch.fx.GraphModule, example_inputs: list) -> object:
        backend_calls.append({"graph": graph.code})
        return graph.forward

    sequences = {
        "stable": [(4, 2, False)] * 3,
        "shape": [(4, 2, False), (8, 2, False), (4, 2, False)],
        "scalar": [(4, 1, False), (4, 2, False), (4, 1, False)],
        "multiple_guards": [(4, 1, False), (4, 2, False), (4, 3, False)],
        "dynamic": [(4, 2, False), (8, 2, False), (16, 2, False)],
        "grad": [(4, 2, False), (4, 2, True), (4, 2, False)],
    }
    compiled = torch.compile(compute, backend=recording_backend, dynamic=None if args.case == "dynamic" else False)
    calls: list[dict] = []
    for size, scale, requires_grad in sequences[args.case]:
        x = torch.arange(size, dtype=torch.float32, requires_grad=requires_grad)
        actual = compiled(x, scale)
        torch.testing.assert_close(actual, compute(x, scale))
        calls.append({"shape": [size], "dtype": "float32", "device": "cpu", "requires_grad": requires_grad,
                      "scale": scale, "backend_calls_so_far": len(backend_calls), "output_correct": True})
    args.result.write_text(json.dumps({"case": args.case, "backend_calls": backend_calls, "calls": calls,
                                       "workload_completed": True, "torch_version": torch.__version__,
                                       "torch_git_version": torch.version.git_version}, indent=2) + "\n")


if __name__ == "__main__":
    main()
