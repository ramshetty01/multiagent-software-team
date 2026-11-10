from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _git_command(args: tuple[str, ...]) -> list[str]:
    options = [
        "git", "--no-pager", "-c", f"core.hooksPath={os.devnull}",
        "-c", "core.fsmonitor=false", "-c", "commit.gpgsign=false",
    ]
    if args and args[0] in {"diff", "show", "log"}:
        return [*options, args[0], "--no-ext-diff", "--no-textconv", *args[1:]]
    return [*options, *args]


def _git_environment() -> dict[str, str]:
    # Git helper processes must not inherit provider credentials or redirect the target repo.
    env = {
        name: value for name, value in os.environ.items()
        if not name.upper().startswith("GIT_")
        and not any(marker in name.upper() for marker in ("API_KEY", "TOKEN", "SECRET", "PASSWORD"))
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def git(repo: str | Path, *args: str) -> str:
    result = subprocess.run(
        _git_command(args), cwd=repo, text=True, capture_output=True,
        check=True, env=_git_environment(), timeout=120,
    )
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


def apply_patch(repo: str | Path, patch: str) -> None:
    process = subprocess.run(_git_command(("apply", "-")), cwd=repo, input=patch, text=True, capture_output=True, check=False, env=_git_environment(), timeout=120)
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or "git apply failed")


def _safe_ref(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value).strip("-") or "unknown"
