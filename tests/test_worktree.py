from __future__ import annotations

import subprocess

from mast.gitops import branch_name, git, is_dirty, worktree_path
from mast.worktree import WorktreeManager


def test_branch_and_worktree_names_are_deterministic(tmp_path):
    assert branch_name("run/1", "task board") == "mast/run-1/task-board"
    assert str(worktree_path(tmp_path, "run/1", "task board")).endswith("run-1/task-board")


def test_worktree_manager_prepares_and_commits(tmp_path):
    repo = tmp_path / "repo"
    worktrees = tmp_path / "worktrees"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("root\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init")

    manager = WorktreeManager(repo, worktrees)
    info = manager.prepare("r1", "s1")
    (info.path / "README.md").write_text("changed\n")
    committed = manager.commit(info, "s1")

    assert committed.commit_sha
    assert not is_dirty(info.path)
