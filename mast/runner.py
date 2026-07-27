from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float


class LocalRunner:
    def run(self, command: list[str], cwd: str | Path) -> CommandResult:
        started = time.monotonic()
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=time.monotonic() - started,
        )

