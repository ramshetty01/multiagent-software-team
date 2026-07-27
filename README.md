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

