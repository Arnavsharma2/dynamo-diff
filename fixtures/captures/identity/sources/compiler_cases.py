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


def graph_break_compute(x: torch.Tensor, scale: int = 2) -> torch.Tensor:
    y = x.sin()
    torch._dynamo.graph_break()
    return y * scale


def no_graph_compute(x: torch.Tensor, scale: int = 2) -> torch.Tensor:
    return x


class IdentityModule(torch.nn.Module):
    def forward(self, x: torch.Tensor, scale: int = 2) -> torch.Tensor:
        return x.sin() + id(self)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["stable", "shape", "scalar", "multiple_guards", "dynamic", "grad",
                                         "graph_break", "backend_failure", "no_graph", "limit", "identity"])
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(2026)
    torch.set_num_threads(1)
    backend_calls: list[dict] = []

    def recording_backend(graph: torch.fx.GraphModule, example_inputs: list) -> object:
        backend_calls.append({"graph": graph.code})
        if args.case == "backend_failure":
            raise RuntimeError("Owned fixture: intentional backend failure after graph emission")
        return graph.forward

    sequences = {
        "stable": [(4, 2, False)] * 3,
        "shape": [(4, 2, False), (8, 2, False), (4, 2, False)],
        "scalar": [(4, 1, False), (4, 2, False), (4, 1, False)],
        "multiple_guards": [(4, 1, False), (4, 2, False), (4, 3, False)],
        "dynamic": [(4, 2, False), (8, 2, False), (16, 2, False)],
        "grad": [(4, 2, False), (4, 2, True), (4, 2, False)],
        "graph_break": [(4, 2, False)] * 2,
        "backend_failure": [(4, 2, False)],
        "no_graph": [(4, 2, False)] * 2,
        "limit": [(4, i, False) for i in [1, 2, 3, 4]],
        "identity": [(4, 2, False)] * 3,
    }
    target = {"graph_break": graph_break_compute, "no_graph": no_graph_compute}.get(args.case, compute)
    if args.case == "limit":
        torch._dynamo.config.recompile_limit = 2
    modules = [IdentityModule() for _ in range(3)] if args.case == "identity" else []
    compiled_modules = [torch.compile(m, backend=recording_backend, dynamic=False) for m in modules]
    compiled = torch.compile(target, backend=recording_backend, dynamic=None if args.case == "dynamic" else False)
    calls: list[dict] = []
    expected_error = None
    for i, (size, scale, requires_grad) in enumerate(sequences[args.case]):
        x = torch.arange(size, dtype=torch.float32, requires_grad=requires_grad)
        try:
            actual = compiled_modules[i](x, scale) if modules else compiled(x, scale)
        except torch._dynamo.exc.BackendCompilerFailed as error:
            if args.case != "backend_failure":
                raise
            expected_error = type(error).__name__
            break
        torch.testing.assert_close(actual, modules[i](x, scale) if modules else target(x, scale))
        calls.append({"shape": [size], "dtype": "float32", "device": "cpu", "requires_grad": requires_grad,
                      "scale": scale, "backend_calls_so_far": len(backend_calls), "output_correct": True})
    args.result.write_text(json.dumps({"case": args.case, "backend_calls": backend_calls, "calls": calls,
                                       "expected_error": expected_error,
                                       "workload_completed": True, "torch_version": torch.__version__,
                                       "torch_git_version": torch.version.git_version}, indent=2) + "\n")


if __name__ == "__main__":
    main()
