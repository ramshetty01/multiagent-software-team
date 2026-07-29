from __future__ import annotations

from .board import JsonlTaskBoard
from .messages import Message


def ownership_from_subtasks(subtasks: list[Message]) -> dict[str, str]:
    owner: dict[str, str] = {}
    for subtask in subtasks:
        for path in subtask.payload.get("contract", {}).get("files", []):
            if subtask.subtask_id:
                owner[path] = subtask.subtask_id
    return owner


def route_review_feedback(board: JsonlTaskBoard, run_id: str, feedback: Message, max_attempts: int = 3) -> list[Message]:
    ownership = ownership_from_subtasks(board.query(run_id=run_id, type="subtask"))
    routed: list[Message] = []
    attempts = len(board.query(run_id=run_id, type="review_feedback"))
    if attempts > max_attempts:
        blocked = Message(type="rejected", run_id=run_id, role="reviewer", tags=["blocked"], payload={"reason": "review feedback loop limit exceeded"})
        board.append(blocked)
        return [blocked]
    for request in feedback.payload.get("requests", []):
        subtask_id = request.get("subtask_id") or ownership.get(request.get("path", ""))
        message = Message(
            type="review_feedback",
            run_id=run_id,
            role="reviewer",
            tags=["coder", subtask_id or "unowned"],
            subtask_id=subtask_id,
            payload={"request": request},
        )
        board.append(message)
        routed.append(message)
    return routed

