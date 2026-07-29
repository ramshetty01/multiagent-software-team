from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

from .config import AppConfig, load_config


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_preflight(config_path: str | None = None, repo: str | Path = ".") -> list[Check]:
    checks: list[Check] = []
    try:
        config = load_config(config_path)
        checks.append(Check("config", True, f"{config.environment}/{config.sandbox_backend}/{config.tracing_backend}"))
    except Exception as exc:
        config = AppConfig()
        checks.append(Check("config", False, str(exc)))
    checks.append(_tool_check("git"))
    checks.append(_tool_check("gh"))
    checks.append(_git_repo_check(repo))
    checks.append(_gh_auth_check())
    checks.append(Check("sandbox_backend", config.sandbox_backend in {"local", "docker", "daytona"}, config.sandbox_backend))
    checks.append(Check("tracing_backend", config.tracing_backend in {"jsonl", "langfuse"}, config.tracing_backend))
    return checks


def preflight_ok(checks: list[Check]) -> bool:
    return all(check.ok for check in checks)


def _tool_check(name: str) -> Check:
    path = shutil.which(name)
    return Check(f"tool:{name}", bool(path), path or "not found")


def _git_repo_check(repo: str | Path) -> Check:
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo, text=True, capture_output=True)
    return Check("git_repo", result.returncode == 0 and result.stdout.strip() == "true", result.stderr.strip() or result.stdout.strip())


def _gh_auth_check() -> Check:
    if not shutil.which("gh"):
        return Check("gh_auth", False, "gh not found")
    result = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True)
    detail = result.stderr.strip() or result.stdout.strip()
    return Check("gh_auth", result.returncode == 0, detail.splitlines()[0] if detail else "ok")

