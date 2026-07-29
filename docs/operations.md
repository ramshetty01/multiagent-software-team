# Operations Runbook

This runbook describes the minimum production controls for running the
multi-agent team against real repositories.

## Preflight

Run before every production batch:

```sh
mast preflight --repo /path/to/target-repo
```

Required checks:

- provider credentials are present for every enabled role
- repository target matches the allowlist
- sandbox backend is `docker` or `daytona`, not `local`
- tracing backend is configured
- task board path is writable
- artifact directory is writable and outside the target repository

## Run Start

1. Create a new run ID with a date and short issue identifier.
2. Clone or refresh the target repository at the exact base commit.
3. Start with an empty board and artifact directory.
4. Store issue context before the architect call.
5. Record model names, provider versions, and sandbox backend.

## During Run

- Watch task-board growth and worker leases.
- Alert if a subtask lease expires more than twice.
- Alert if conflict resolution is invoked on more than two files.
- Alert if reviewer feedback touches files outside the subtask contracts.
- Alert if tester retries classify the same failure as flaky more than once.

## Failure Recovery

| Failure | Recovery |
| --- | --- |
| Coder crash | reclaim expired lease and rerun the same subtask |
| Sandbox crash | create a fresh sandbox and replay from board state |
| Merge conflict | preserve conflict artifact and run conflict resolver only for overlapped files |
| Reviewer rejection | route feedback to owning subtask and append `subtask_requeued` |
| Tester failure | attach logs and route to likely owning subtask |
| PR creation failure | retry idempotently with the same run ID and branch |

Never delete board messages to repair a run. Append corrective messages so the
post-mortem can reconstruct what happened.

## Scaling

- Scale coder workers from task-board backlog, not CPU alone.
- Keep one merge coordinator per run.
- Keep one reviewer per staging diff.
- Keep tester workers isolated from coder sandboxes.
- Prefer a Redis-backed board before running large concurrent batches.

## Cost Controls

- Set per-role token budgets.
- Track retry counts separately from first-pass calls.
- Stop runs when the reviewer loop exceeds the configured maximum.
- Include conflict-resolution tokens in the merge coordinator role.
- Export cost by run ID before cleaning artifacts.

## Shutdown

After every run:

```sh
mast cleanup --repo /path/to/target-repo --dry-run
```

Then remove stale worktrees, close sandbox sessions, archive artifacts, and
write the final report.
