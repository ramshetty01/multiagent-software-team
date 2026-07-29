# Multi-Agent Software Engineering Team

Autonomous multi-agent system that turns a GitHub issue into a merge-ready PR.

This repository starts from the PRD in `outputs/skill-multi-agent-team.md`.
The implementation backlog is split into GitHub-ready issues in
`docs/github-issues.md`.

## First Milestone

Create the coordination spine before adding agent intelligence:

1. File-backed task board and typed message schema.
2. Issue intake and architect plan DAG.
3. Isolated coder worktrees.
4. Deterministic merge staging.
5. Reviewer/tester gates.
6. Observability and evaluation reports.

## Create GitHub Issues

After GitHub auth is valid and the remote repo exists:

```sh
scripts/create_github_issues.sh owner/repo
```

## Run Locally

```sh
python3 -m mast.cli run --issue https://github.com/owner/repo/issues/1 --parallelism 4
scripts/self_check.py
```

The MVP uses local process isolation and git worktree helpers first. Daytona,
LangGraph, model clients, and LLM conflict resolution are kept behind narrow
interfaces so they can be swapped in without changing the task-board contract.

## Production Docs

- [Configuration](docs/configuration.md)
- [Operator setup](docs/operator-setup.md)
- [Architecture](docs/architecture.md)
- [Run lifecycle](docs/run-lifecycle.md)
- [Troubleshooting](docs/troubleshooting.md)
