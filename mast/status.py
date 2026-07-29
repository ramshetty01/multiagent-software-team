from __future__ import annotations

from collections import Counter

from .board import JsonlTaskBoard


def run_status(board: JsonlTaskBoard, run_id: str) -> dict[str, object]:
    messages = board.query(run_id=run_id)
    counts = Counter(message.type for message in messages)
    terminal = "running"
    if counts.get("test_passed") or any(m.role == "pr" for m in messages):
        terminal = "succeeded"
    if counts.get("test_failed") or counts.get("rejected"):
        terminal = "blocked"
    return {
        "run_id": run_id,
        "status": terminal,
        "messages": sum(counts.values()),
        "counts": dict(counts),
        "claims": counts.get("subtask_claimed", 0),
        "failures": counts.get("test_failed", 0) + counts.get("rejected", 0),
    }

