from __future__ import annotations

import subprocess

from mast.cleanup import cleanup_plan
from mast.gitops import git


def test_cleanup_plan_lists_mast_branches_and_worktrees(tmp_path):
    repo = tmp_path / "cleanup-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "a").write_text("a")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init")
    git(repo, "branch", "mast/r1/s1")
    worktree = tmp_path / "cleanup-worktrees/r1/s1"
    worktree.mkdir(parents=True)
    plan = cleanup_plan(repo, tmp_path / "cleanup-worktrees")
    assert "mast/r1/s1" in plan["branches"]
    assert str(worktree) in plan["worktrees"]
