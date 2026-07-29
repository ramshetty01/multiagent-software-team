from __future__ import annotations

from pathlib import Path

from .config import AppConfig, redact_secrets


class SecurityError(RuntimeError):
    pass


DEFAULT_ALLOWED_PREFIXES = (
    ("python3",),
    ("python",),
    ("git", "diff"),
    ("git", "status"),
    ("git", "log"),
    ("git", "show"),
    ("git", "apply"),
    ("git", "add"),
    ("git", "commit"),
    ("pytest",),
    ("npm", "test"),
    ("npm", "run"),
)


def validate_command(command: list[str], allowed_prefixes=DEFAULT_ALLOWED_PREFIXES) -> None:
    if not command:
        raise SecurityError("empty command is not allowed")
    if command[0] in {"rm", "sudo", "curl", "wget", "ssh"}:
        raise SecurityError(f"blocked command: {command[0]}")
    if not any(tuple(command[: len(prefix)]) == prefix for prefix in allowed_prefixes):
        raise SecurityError(f"command is not allowlisted: {' '.join(command)}")


def validate_repo(repo: str | Path, allowlist: list[str] | None = None) -> None:
    if not allowlist:
        return
    root = Path(repo).resolve()
    allowed = [Path(path).resolve() for path in allowlist]
    if not any(root == path or root.is_relative_to(path) for path in allowed):
        raise SecurityError(f"repo is not allowlisted: {root}")


def redact_artifact(text: str, config: AppConfig) -> str:
    return redact_secrets(text, config)

