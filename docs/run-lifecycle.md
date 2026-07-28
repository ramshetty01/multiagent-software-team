# Run Lifecycle

1. Intake fetches the GitHub issue and stores `issue.json`.
2. Architect writes a schema-valid subtask DAG.
3. Coder workers claim subtasks with leases.
4. Each coder works in its own worktree and sandbox.
5. Merge coordinator creates a staging branch.
6. Reviewer checks the merged diff only.
7. Tester runs in a clean sandbox and stores artifacts.
8. PR creation runs only after `test_passed`.

Terminal states:

- `succeeded`: PR is ready or created.
- `failed`: worker or test gate failed with artifacts.
- `blocked`: scope, merge, or review loop needs a human decision.

