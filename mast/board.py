from __future__ import annotations

import fcntl
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

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
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            for line in handle:
                if line.strip():
                    messages.append(Message.from_dict(json.loads(line)))
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
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

    def current_diffs(self, run_id: str) -> dict[str, Message]:
        return _current_diffs(self.query(run_id=run_id))

    def claim_subtask(self, run_id: str, worker_id: str, lease_seconds: int = 900) -> Message | None:
        with self.path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            messages = [Message.from_dict(json.loads(line)) for line in handle if line.strip()]
            current = [msg for msg in messages if msg.run_id == run_id]
            done = _current_diffs(current)
            claimed: dict[str, Message] = {}
            subtasks: dict[str, Message] = {}
            for msg in current:
                if not msg.subtask_id:
                    continue
                if msg.type == "subtask":
                    subtasks[msg.subtask_id] = msg
                elif msg.type == "subtask_claimed" and not _lease_expired(msg):
                    claimed[msg.subtask_id] = msg
                elif msg.type == "subtask_requeued":
                    for task_id in _affected_tasks(current, msg.subtask_id):
                        claimed.pop(task_id, None)
            for subtask in subtasks.values():
                if subtask.subtask_id in claimed or subtask.subtask_id in done:
                    continue
                if not set(subtask.payload.get("depends_on", [])) <= done.keys():
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
    return (datetime.now(UTC) - created).total_seconds() > lease_seconds


def append_many(board: JsonlTaskBoard, messages: Iterable[Message]) -> None:
    for message in messages:
        board.append(message)


def _current_diffs(messages: list[Message]) -> dict[str, Message]:
    done: dict[str, Message] = {}
    for message in messages:
        if message.subtask_id:
            if message.type == "subtask_requeued":
                for task_id in _affected_tasks(messages, message.subtask_id):
                    done.pop(task_id, None)
            elif message.type == "diff_ready":
                done[message.subtask_id] = message
    return done


def _affected_tasks(messages: list[Message], task_id: str) -> set[str]:
    affected = {task_id}
    tasks = [m for m in messages if m.type == "subtask" and m.subtask_id]
    while True:
        previous = len(affected)
        for task in tasks:
            if set(task.payload.get("depends_on", [])) & affected and task.subtask_id:
                affected.add(task.subtask_id)
        if len(affected) == previous:
            return affected
