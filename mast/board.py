from __future__ import annotations

import fcntl
import json
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


def append_many(board: JsonlTaskBoard, messages: Iterable[Message]) -> None:
    for message in messages:
        board.append(message)

