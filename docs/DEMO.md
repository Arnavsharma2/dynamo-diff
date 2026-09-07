# Inspect the recorded example

The authored before/after captures demonstrate source matching and compiler-event accounting without running a workload. With Dynamo Diff installed, run from the source checkout:

```sh
python tools/demo.py
```

This imports both captures into a temporary store, checks their expected comparison and prints a Markdown table. PyTorch and a GPU are not required.

The comparison matches `compute` across an ordinary source edit and changed frame IDs. Three completed compilations, including two confirmed recompilations, become one completed compilation with no confirmed recompilation. The candidate's new helper remains unmatched and adds another completed compilation to candidate totals, making the overall comparison three → two.

Original baseline evidence retains `step == 1`, its captured `if step > 0` context, artifact `-_0_1_0/recompile_reasons_4.json`, record 10 and SHA-256 `832c22b265eea6007916338024fa9ad308f931e2ca6ecf4bbc57ce205b43dc6a`. Manifest consistency describes matching declarations; it does not prove equivalent execution. Application speed remains unmeasured.

[Installation instructions](INSTALL.md) explain how to import the same saved captures in VS Code. [Integration instructions](INTEGRATIONS.md) cover the CLI, MCP server and editor configuration. [Verification evidence](../artifacts/VERIFICATION.md) preserves the separately completed editor checks.
