from __future__ import annotations

from ..messages import Message
from ..models import ModelProvider, ModelRequest, complete_with_retry
from ..prompts import parse_review_json, reviewer_prompt


class Reviewer:
    def __init__(self, provider: ModelProvider | None = None, model: str = "gpt-5"):
        self.provider = provider
        self.model = model

    def review(self, run_id: str, diff_author: str, reviewer_id: str, diff_summary: str) -> Message:
        if diff_author == reviewer_id:
            return Message(
                type="rejected",
                run_id=run_id,
                role=reviewer_id,
                tags=["reviewer"],
                payload={"reason": "reviewer cannot approve its own diff"},
            )
        if "TODO: broken" in diff_summary:
            return Message(
                type="review_feedback",
                run_id=run_id,
                role=reviewer_id,
                tags=["coder"],
                payload={"requests": [{"path": "unknown", "message": "remove broken TODO before approval"}]},
            )
        if self.provider:
            response = complete_with_retry(
                self.provider,
                ModelRequest(
                    run_id=run_id,
                    role="reviewer",
                    model=self.model,
                    prompt=reviewer_prompt(diff_summary),
                    prompt_name="reviewer.diff",
                    prompt_version="2026-07-30",
                ),
            )
            try:
                parsed = parse_review_json(response.text)
            except ValueError as exc:
                return Message(
                    type="rejected",
                    run_id=run_id,
                    role=reviewer_id,
                    tags=["reviewer"],
                    payload={"reason": f"invalid reviewer output: {exc}"},
                )
            if parsed["decision"] == "request_changes":
                return Message(
                    type="review_feedback",
                    run_id=run_id,
                    role=reviewer_id,
                    tags=["coder"],
                    payload={"requests": parsed["requests"]},
                )
        return Message(
            type="approved",
            run_id=run_id,
            role=reviewer_id,
            tags=["tester"],
            payload={"summary": "merged diff approved"},
        )
