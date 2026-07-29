from __future__ import annotations

from fnmatch import fnmatch

DEFAULT_GENERATED_LOCKFILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock")


def out_of_scope(changed: list[str], allowed: list[str], generated_lockfiles: bool = False) -> list[str]:
    patterns = list(allowed)
    if generated_lockfiles:
        patterns.extend(DEFAULT_GENERATED_LOCKFILES)
    return [path for path in changed if not any(_matches(path, pattern) for pattern in patterns)]


def _matches(path: str, pattern: str) -> bool:
    return fnmatch(path, pattern) or path == pattern or path.startswith(pattern.rstrip("/") + "/")
