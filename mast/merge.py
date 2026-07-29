from __future__ import annotations

from collections import Counter

from .messages import Message


def file_overlaps(diff_messages: list[Message]) -> list[str]:
    counts = Counter(path for msg in diff_messages for path in msg.payload.get("changed_files", []))
    return sorted(path for path, count in counts.items() if count > 1)


class MergeCoordinator:
    def merge(self, run_id: str, diff_messages: list[Message]) -> Message:
        overlaps = file_overlaps(diff_messages)
        if overlaps:
            return Message(
                type="rejected",
                run_id=run_id,
                role="merge",
                tags=["merge", "conflict"],
                payload={"conflicts": overlaps, "resolution": "blocked until resolver is supplied"},
            )
        return Message(
            type="review_needed",
            run_id=run_id,
            role="merge",
            tags=["reviewer"],
            payload={"subtasks": [msg.subtask_id for msg in diff_messages], "conflicts": []},
        )

