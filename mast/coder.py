from __future__ import annotations

from .board import JsonlTaskBoard
from .messages import Message
from .models import ModelProvider, ModelRequest, complete_with_retry
from .prompts import coder_prompt, read_declared_files
from .scope import out_of_scope


class CoderWorker:
    def __init__(self, board: JsonlTaskBoard, coder_id: str, provider: ModelProvider | None = None, model: str = "claude-sonnet"):
        self.board = board
        self.coder_id = coder_id
        self.provider = provider
        self.model = model

    def claim_next(self, run_id: str) -> Message | None:
        claim = self.board.claim_subtask(run_id, self.coder_id)
        if not claim:
            return None
        matches = self.board.query(run_id=run_id, type="subtask", subtask_id=claim.subtask_id)
        return matches[-1] if matches else None

    def submit_diff(self, run_id: str, subtask: Message, changed: list[str], patch: str, tests: str) -> Message:
        allowed = subtask.payload["contract"]["files"] + subtask.payload["contract"].get("test_impact", [])
        bad = out_of_scope(changed, allowed)
        if bad:
            message = Message(
                type="replan_needed",
                run_id=run_id,
                role=self.coder_id,
                tags=["architect", "scope"],
                subtask_id=subtask.subtask_id,
                payload={"changed_files": changed, "out_of_scope": bad},
            )
        else:
            message = Message(
                type="diff_ready",
                run_id=run_id,
                role=self.coder_id,
                tags=["merge"],
                subtask_id=subtask.subtask_id,
                payload={"changed_files": changed, "patch": patch, "tests": tests},
            )
        self.board.append(message)
        return message

    def draft_patch(self, run_id: str, repo: str, subtask: Message) -> str:
        if not self.provider:
            raise RuntimeError("model provider is required to draft patches")
        files = read_declared_files(repo, subtask.payload["contract"]["files"])
        response = complete_with_retry(
            self.provider,
            ModelRequest(
                run_id=run_id,
                role="coder",
                model=self.model,
                prompt=coder_prompt(subtask.payload, files),
                files=files,
            ),
        )
        return response.text
