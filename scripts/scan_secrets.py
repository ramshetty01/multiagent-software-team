#!/usr/bin/env python3
"""Heuristic scan of tracked UTF-8 files; report locations, never matched values."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{30,}(?![A-Za-z0-9_])"),
    re.compile(r"(?<![A-Za-z0-9_])sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_])"),
    re.compile(r"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{30,}(?![A-Za-z0-9_])"),
)


def finding_lines(text: str) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if any(p.search(line) for p in PATTERNS)]


def scan(root: Path) -> list[tuple[str, int]]:
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    findings = []
    for relative in files:
        if not relative:
            continue
        path = root / relative
        if path.is_symlink() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend((relative, line) for line in finding_lines(content))
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = scan(root)
    for path, line in findings:
        print(f"{path}:{line}: credential-like literal detected [REDACTED]")
    if not findings:
        print("No credential-like literals detected in tracked UTF-8 files.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
