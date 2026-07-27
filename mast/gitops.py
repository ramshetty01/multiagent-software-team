from __future__ import annotations

import subprocess
from pathlib import Path


def git(repo: str | Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def changed_files(repo: str | Path, base_ref: str = "HEAD") -> list[str]:
    output = git(repo, "diff", "--name-only", base_ref)
    return [line for line in output.splitlines() if line]


def ensure_worktree(repo: str | Path, branch: str, path: str | Path) -> Path:
    target = Path(path)
    if target.exists():
        if is_dirty(target):
            raise RuntimeError(f"worktree is dirty: {target}")
        return target
    git(repo, "worktree", "add", "-b", branch, str(target))
    return target


def branch_name(run_id: str, subtask_id: str) -> str:
    safe_run = _safe_ref(run_id)
    safe_subtask = _safe_ref(subtask_id)
    return f"mast/{safe_run}/{safe_subtask}"


def worktree_path(root: str | Path, run_id: str, subtask_id: str) -> Path:
    return Path(root) / _safe_ref(run_id) / _safe_ref(subtask_id)


def is_dirty(repo: str | Path) -> bool:
    return bool(git(repo, "status", "--porcelain"))


def commit_all(repo: str | Path, message: str) -> str | None:
    if not is_dirty(repo):
        return None
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def _safe_ref(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value).strip("-") or "unknown"
