# Scoring history

The mechanical scoring rules were written before actual final answers were inspected. Scorer 1 was exercised on 28 completed attempts; its source is retained as `scorer-v1.py`. Scorer 1.1 adds original final text to the human review packet, including malformed answers. It changes presentation and retained fields, not numeric scoring rules.

After inspecting the malformed `q02-dynamo-r1` response and valid but incorrect `q01-raw-r1` response, a separate post-hoc format sensitivity analysis was authored in `diagnose_formatting.py`. It extracts only an unchanged first answer member when that member itself is valid JSON. It never repairs text or changes the primary results. This exploratory analysis was not preregistered and does not validate explanations or evidence. Synthetic parser checks cover nested data, braces inside strings, malformed objects, duplicate keys and refusal to search later objects.

The original runner, core, protocol, questions, answer key and exposed captures remain frozen. Human key and semantic review remain pending.
