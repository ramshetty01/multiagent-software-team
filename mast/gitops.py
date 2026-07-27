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
        return target
    git(repo, "worktree", "add", "-b", branch, str(target))
    return target

