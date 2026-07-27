from __future__ import annotations

from .messages import Message


class Reviewer:
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
        return Message(
            type="approved",
            run_id=run_id,
            role=reviewer_id,
            tags=["tester"],
            payload={"summary": "merged diff approved"},
        )

