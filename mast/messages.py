from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from .validation import validate_review_feedback, validate_subtask_payload

MessageType = Literal[
    "plan_request",
    "subtask",
    "diff_ready",
    "review_needed",
    "review_feedback",
    "test_needed",
    "approved",
    "rejected",
    "replan_needed",
    "test_passed",
    "test_failed",
    "subtask_claimed",
    "subtask_requeued",
]

MESSAGE_TYPES = set(MessageType.__args__)


@dataclass(frozen=True)
class Message:
    type: MessageType
    run_id: str
    role: str
    payload: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    subtask_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["type"] not in MESSAGE_TYPES:
            raise ValueError(f"unknown message type: {data['type']}")
        if not data["run_id"]:
            raise ValueError("run_id is required")
        if not data["role"]:
            raise ValueError("role is required")
        if data["type"] == "subtask":
            validate_subtask_payload(data["payload"])
        if data["type"] == "review_feedback" and "requests" in data["payload"]:
            validate_review_feedback(data["payload"])
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        msg_type = data.get("type")
        if msg_type not in MESSAGE_TYPES:
            raise ValueError(f"unknown message type: {msg_type}")
        return cls(
            type=msg_type,
            run_id=data["run_id"],
            role=data["role"],
            payload=data.get("payload", {}),
            tags=list(data.get("tags", [])),
            subtask_id=data.get("subtask_id"),
            id=data.get("id", str(uuid4())),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            trace_id=data.get("trace_id"),
        )
