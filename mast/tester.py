from __future__ import annotations

from pathlib import Path

from .artifacts import ArtifactStore
from .failures import classify_retries, likely_owner
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
        retries: int = 0,
    ) -> Message:
        attempts = [self.runner.run(command, repo)]
        for _ in range(retries):
            if attempts[-1].returncode == 0:
                break
            attempts.append(self.runner.run(command, repo))
        result = attempts[-1]
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
                "attempt_returncodes": [attempt.returncode for attempt in attempts],
                "retry_classification": classify_retries([attempt.returncode for attempt in attempts]),
            },
        )
        owner_guess, confidence = likely_owner(result.stderr, ownership or {})
        if owner_guess and not message.subtask_id:
            message.subtask_id = owner_guess
        message.payload["owner_confidence"] = confidence
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
