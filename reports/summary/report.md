# Weekly customer update gate: GO

Agent `agent:live_summary`, 3 cases, 1 run(s).

- every rule held on all 1 run(s), no critical failures

## Pass counts by run

| Run | Passed | Critical failures |
|---|---|---|
| 1 | 3 of 3 | 0 |

Agent cost 0.0234 USD, judge cost 0.0187 USD, mean latency 3639.7 ms per case.

## Cases

| Case | Group | Result | Failed checks |
|---|---|---|---|
| Week 1 update | default | 1 of 1 runs |  |
| Week 2 update | default | 1 of 1 runs |  |
| Week 3 update | default | 1 of 1 runs |  |

## Checks

| Check | Critical | Text |
|---|---|---|
| numbers_from_facts | yes | Every number in the update appears in the week's fact sheet. |
| stage_stated |  | The update says whether next week is supervised or unsupervised. |
| short |  | The update is under 120 words, with no bullet points. |
| claims_supported | yes | Every claim in the update is supported by the fact sheet, including what the gate decided and why the robot is or is not working unsupervised next week. It does not promise dates, savings or results the fact sheet does not contain. |
