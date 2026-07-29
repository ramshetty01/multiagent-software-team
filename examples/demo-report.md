# Demo run report

Run ID: `demo-run`

## Outcome

Status: `succeeded`

Messages written: 7

## Role summary

| Role | Messages |
| --- | ---: |
| architect | 3 |
| coder | 2 |
| reviewer | 1 |
| tester | 1 |

## Handoff notes

- Architect declared file-level scope before coder work started.
- Coders emitted patch and test metadata through `diff_ready`.
- Reviewer approved the merged diff only.
- Tester produced a terminal `test_passed` message with artifact references.
