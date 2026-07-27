from __future__ import annotations

from fnmatch import fnmatch


def out_of_scope(changed: list[str], allowed: list[str]) -> list[str]:
    return [path for path in changed if not any(fnmatch(path, pattern) for pattern in allowed)]

