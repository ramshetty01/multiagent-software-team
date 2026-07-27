# Implementation Matrix

| Issue | Coverage |
|---|---|
| #1 Task board | `mast.board.JsonlTaskBoard`, `mast.messages.Message`, concurrent append self-check |
| #2 Schema | `mast.schema.Subtask`, `InterfaceContract`, DAG validation, status transitions |
| #3 Architect | `mast.architect.plan_from_issue`, ambiguity escape hatch |
| #4 CLI | `mast.cli run`, run ID resume behavior |
| #5 Coder worker | `mast.coder.CoderWorker`, one-subtask claim and diff handoff |
| #6 Scope guard | `mast.scope.out_of_scope`, `replan_needed` emission |
| #7 Sandbox runner | `mast.runner.LocalRunner`, command artifacts |
| #8 Merge coordinator | `mast.merge.MergeCoordinator`, deterministic no-overlap merge gate |
| #9 Conflict logging | `mast.merge.file_overlaps`, rejected conflict payload |
| #10 Reviewer | `mast.reviewer.Reviewer`, self-approval guard |
| #11 Tester | `mast.tester.Tester`, clean runner boundary, pass/fail messages |
| #12 Observability | `mast.observability.TraceLog`, token amplification |
| #13 Evaluation | `mast.eval.EvalResult`, baseline summary export |
| #14 Post-mortem | `mast.reporting.write_postmortem`, handoff histogram |

## Validation

```sh
scripts/self_check.py
python3 -m mast.cli run --issue https://github.com/ramshetty01/multiagent-software-team/issues/1 --parallelism 4 --run-id demo --board /tmp/mast-board.jsonl
python3 -m mast.cli report --failure merge_conflict --failure tester_flake --speedup 1.8 --token-cost 12.5 --out /tmp/mast-postmortem.md
```

