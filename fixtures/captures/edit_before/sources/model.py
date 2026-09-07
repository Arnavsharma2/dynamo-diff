import json
from pathlib import Path
import sys
import torch

torch.manual_seed(2026)
torch.set_num_threads(1)

def compute(x, step):
    if step > 0:
        return x.sin() * 2
    return x.sin() * 2

VARIANT = "before"
backend_calls = []
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
