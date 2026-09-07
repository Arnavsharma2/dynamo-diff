# Pilot results — provisional

Completed attempts: **60/60**. Human key and semantic review remain pending.

These are mechanical answer-field and literal-quotation checks. They are not reviewed diagnostic accuracy or proof of agent productivity.

| Condition | Attempts | All fields correct | Correct fields | Literal citations present | Unsupported affirmative claim fields | Median input/output tokens | Median tools | Median seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| raw | 20/20 | 0 | 21/86 | 36/53 | 3 | 8704.0 / 427.5 | 4.0 | 49.4 |
| tlparse | 20/20 | 1 | 21/86 | 18/31 | 0 | 12588.5 / 488.0 | 7.5 | 48.7 |
| dynamo | 20/20 | 0 | 0/86 | 0/0 | 0 | 2781.5 / 316.0 | 1.0 | 29.0 |

[Individual scores and paired outcomes](scores.json) retain every completed attempt, including failures. The run directory retains original model/tool transcripts; the review file below includes explanations without treating them as instructions.

Wall-time comparisons are descriptive and may reflect background local work. Read the frozen protocol and activity notes before interpreting timing. Each condition has only ten question instances repeated twice; no statistical-significance or generalization claim is made.
