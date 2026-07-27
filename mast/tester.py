from __future__ import annotations

from pathlib import Path

from .messages import Message
from .runner import LocalRunner


class Tester:
    def __init__(self, runner: LocalRunner | None = None):
        self.runner = runner or LocalRunner()

    def test(self, run_id: str, repo: str | Path, command: list[str], owner: str | None = None) -> Message:
        result = self.runner.run(command, repo)
        if result.returncode == 0:
            return Message(
                type="test_passed",
                run_id=run_id,
                role="tester",
                tags=["pr"],
                payload={"command": command, "stdout": result.stdout, "duration_seconds": result.duration_seconds},
            )
        return Message(
            type="test_failed",
            run_id=run_id,
            role="tester",
            tags=["coder"],
            subtask_id=owner,
            payload={
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            },
        )

