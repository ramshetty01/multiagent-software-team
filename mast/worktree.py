from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .gitops import branch_name, commit_all, ensure_worktree, worktree_path


@dataclass(frozen=True)
class WorktreeInfo:
    branch: str
    path: Path
    commit_sha: str | None = None


class WorktreeManager:
    def __init__(self, repo: str | Path, root: str | Path):
        self.repo = Path(repo)
        self.root = Path(root)

    def prepare(self, run_id: str, subtask_id: str) -> WorktreeInfo:
        branch = branch_name(run_id, subtask_id)
        path = ensure_worktree(self.repo, branch, worktree_path(self.root, run_id, subtask_id))
        return WorktreeInfo(branch, path)

    def commit(self, info: WorktreeInfo, subtask_id: str) -> WorktreeInfo:
        sha = commit_all(info.path, f"Implement subtask {subtask_id}")
        return WorktreeInfo(info.branch, info.path, sha)

