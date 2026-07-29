from __future__ import annotations

import fcntl
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .messages import Message


class JsonlTaskBoard:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, message: Message) -> None:
        line = json.dumps(message.to_dict(), sort_keys=True)
        with self.path.open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.write(line + "\n")
            handle.flush()
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def read(self) -> list[Message]:
        messages: list[Message] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    messages.append(Message.from_dict(json.loads(line)))
        return messages

    def query(
        self,
        *,
        run_id: str | None = None,
        role: str | None = None,
        tag: str | None = None,
        subtask_id: str | None = None,
        type: str | None = None,
    ) -> list[Message]:
        return [
            message
            for message in self.read()
            if (run_id is None or message.run_id == run_id)
            and (role is None or message.role == role)
            and (tag is None or tag in message.tags)
            and (subtask_id is None or message.subtask_id == subtask_id)
            and (type is None or message.type == type)
        ]

    def seen_ids(self) -> set[str]:
        return {message.id for message in self.read()}

    def claim_subtask(self, run_id: str, worker_id: str, lease_seconds: int = 900) -> Message | None:
        with self.path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            messages = [Message.from_dict(json.loads(line)) for line in handle if line.strip()]
            claimed = {
                msg.subtask_id
                for msg in messages
                if msg.run_id == run_id and msg.type == "subtask_claimed" and not _lease_expired(msg)
            }
            done = {msg.subtask_id for msg in messages if msg.run_id == run_id and msg.type == "diff_ready"}
            for subtask in [msg for msg in messages if msg.run_id == run_id and msg.type == "subtask"]:
                if subtask.subtask_id in claimed or subtask.subtask_id in done:
                    continue
                claim = Message(
                    type="subtask_claimed",
                    run_id=run_id,
                    role=worker_id,
                    tags=["claim", worker_id],
                    subtask_id=subtask.subtask_id,
                    payload={"worker_id": worker_id, "lease_seconds": lease_seconds},
                )
                handle.seek(0, 2)
                handle.write(json.dumps(claim.to_dict(), sort_keys=True) + "\n")
                handle.flush()
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                return claim
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return None


def _lease_expired(message: Message) -> bool:
    lease_seconds = int(message.payload.get("lease_seconds", 900))
    created = datetime.fromisoformat(message.created_at)
    return (datetime.now(timezone.utc) - created).total_seconds() > lease_seconds


def append_many(board: JsonlTaskBoard, messages: Iterable[Message]) -> None:
    for message in messages:
        board.append(message)
