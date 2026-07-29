from __future__ import annotations

from pathlib import Path

from .artifacts import ArtifactStore
from .messages import Message
from .models import ModelProvider, ModelRequest, complete_with_retry
from .prompts import parse_test_failure_json, tester_prompt
from .runner import LocalRunner


class Tester:
    def __init__(self, runner: LocalRunner | None = None, provider: ModelProvider | None = None, model: str = "gemini-pro"):
        self.runner = runner or LocalRunner()
        self.provider = provider
        self.model = model

    def test(
        self,
        run_id: str,
        repo: str | Path,
        command: list[str],
        owner: str | None = None,
        diff: str = "",
        ownership: dict[str, str] | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> Message:
        result = self.runner.run(command, repo)
        if result.returncode == 0:
            return Message(
                type="test_passed",
                run_id=run_id,
                role="tester",
                tags=["pr"],
                payload={"command": command, "stdout": result.stdout, "duration_seconds": result.duration_seconds},
            )
        message = Message(
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
        if artifact_store:
            message.payload["artifacts"] = {
                "stdout": artifact_store.write_text(run_id, "tester/stdout.log", result.stdout),
                "stderr": artifact_store.write_text(run_id, "tester/stderr.log", result.stderr),
            }
        if self.provider:
            response = complete_with_retry(
                self.provider,
                ModelRequest(
                    run_id=run_id,
                    role="tester",
                    model=self.model,
                    prompt=tester_prompt(result.stdout, result.stderr, diff, ownership or {}),
                ),
            )
            try:
                message.payload["classification"] = parse_test_failure_json(response.text)
            except ValueError as exc:
                message.payload["classification"] = {"classification": "unknown", "evidence": str(exc)}
        return message
