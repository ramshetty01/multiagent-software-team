from __future__ import annotations

from .board import JsonlTaskBoard
from .gitops import apply_patch, changed_files
from .messages import Message
from .models import ModelProvider, ModelRequest, complete_with_retry
from .prompts import coder_prompt, read_declared_files
from .runner import LocalRunner
from .scope import out_of_scope
from .worktree import WorktreeManager


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

    def implement(
        self,
        run_id: str,
        repo: str,
        worktree_root: str,
        subtask: Message,
        test_command: list[str],
        max_attempts: int = 2,
    ) -> Message:
        manager = WorktreeManager(repo, worktree_root)
        info = manager.prepare(run_id, subtask.subtask_id or "unknown")
        runner = LocalRunner()
        last_error = ""
        patch = ""
        tests = ""
        for _ in range(max(1, max_attempts)):
            try:
                patch = self.draft_patch(run_id, str(info.path), subtask)
                apply_patch(info.path, patch)
                result = runner.run(test_command, info.path)
                tests = result.stdout + result.stderr
                if result.returncode != 0:
                    last_error = tests
                    continue
                committed = manager.commit(info, subtask.subtask_id or "unknown")
                return self.submit_diff(run_id, subtask, changed_files(info.path, "HEAD~1"), patch, tests + f"\ncommit={committed.commit_sha}")
            except Exception as exc:
                last_error = str(exc)
        message = Message(
            type="replan_needed",
            run_id=run_id,
            role=self.coder_id,
            tags=["coder", "patch_failed"],
            subtask_id=subtask.subtask_id,
            payload={"error": last_error, "patch": patch, "tests": tests},
        )
        self.board.append(message)
        return message
