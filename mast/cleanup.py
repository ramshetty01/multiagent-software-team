from __future__ import annotations

from pathlib import Path

from .gitops import git


def cleanup_plan(repo: str | Path, worktree_root: str | Path, branch_prefix: str = "mast/") -> dict[str, list[str]]:
    branches = []
    for line in git(repo, "branch", "--format=%(refname:short)").splitlines():
        name = line.strip()
        if name.startswith(branch_prefix):
            branches.append(name)
    worktrees = []
    root = Path(worktree_root)
    if root.exists():
        worktrees = [str(path) for path in root.glob("*/*") if path.is_dir()]
    return {"branches": branches, "worktrees": worktrees}

