# Architecture

The system is intentionally narrow: one GitHub issue becomes one staged PR.

Core modules:

- `mast.github`: issue intake through GitHub.
- `mast.board`: append-only JSONL task board and worker leases.
- `mast.models`: shared model provider contract.
- `mast.orchestrator`: resumable role graph.
- `mast.worktree`: branch and worktree lifecycle.
- `mast.runner`: local, Docker, and Daytona command runners.
- `mast.merge` and `mast.conflicts`: staging merge and conflict resolution.
- `mast.reviewer`, `mast.tester`, `mast.pr`: gates and final PR creation.
- `mast.observability`, `mast.costs`, `mast.reporting`: traces, cost, and reports.

Provider-specific adapters stay thin. Role logic should depend on `ModelProvider`,
not SDK clients.

See [diagrams](diagrams.md) and [ADRs](adr/0001-task-board.md).
