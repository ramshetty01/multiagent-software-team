from __future__ import annotations

import subprocess

from mast.gitops import git
from mast.merge import MergeCoordinator


def _repo(path):
    path.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "a.txt").write_text("a\n")
    (path / "b.txt").write_text("b\n")
    git(path, "add", "-A")
    git(path, "commit", "-m", "init")
    return path


def test_merge_branches_creates_staging_branch(tmp_path):
    repo = _repo(tmp_path / "merge-repo")
    git(repo, "switch", "-c", "branch-a")
    (repo / "a.txt").write_text("aa\n")
    git(repo, "commit", "-am", "a")
    git(repo, "switch", "main")
    git(repo, "switch", "-c", "branch-b")
    (repo / "b.txt").write_text("bb\n")
    git(repo, "commit", "-am", "b")
    git(repo, "switch", "main")

    message = MergeCoordinator().merge_branches("r1", repo, "main", ["branch-b", "branch-a"])

    assert message.type == "review_needed"
    assert git(repo, "branch", "--show-current") == "staging/r1"

