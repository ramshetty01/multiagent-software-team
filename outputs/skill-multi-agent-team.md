# Multi-Agent Software Engineering Team

## Product

Given a GitHub issue URL and a parallelism level, produce a merge-ready PR with
per-role token accounting, SWE-bench Pro evaluation results, and a handoff
failure post-mortem.

## Scope

Build a focused SWE-bench Pro issue-to-PR workflow, not a general-purpose agent
framework.

## Phases

1. Task board and message schema.
2. Orchestration skeleton and run CLI.
3. Architect role and plan DAG generation.
4. Coder worker with isolated git worktrees.
5. Sandbox execution boundary.
6. Scope guard and replan path.
7. Merge coordinator.
8. Reviewer gate with self-approval guard.
9. Tester gate in a clean sandbox.
10. Observability and token accounting.
11. Evaluation harness and single-agent baseline.
12. Post-mortem reporting.

## Core Message Types

- `plan_request`
- `subtask`
- `diff_ready`
- `review_needed`
- `review_feedback`
- `test_needed`
- `approved`
- `rejected`
- `replan_needed`
- `test_passed`
- `test_failed`

## Success Metrics

- Pass@1 on a fixed 50-issue SWE-bench Pro subset.
- Wall-clock speedup against a single-agent baseline.
- Reviewer false-approval rate below 5% on injected-bug probes.
- Token cost per solved issue.
- Handoff-failure histogram per run.

