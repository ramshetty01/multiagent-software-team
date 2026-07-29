from __future__ import annotations

import fcntl
from pathlib import Path


class RunLock:
    def __init__(self, root: str | Path, run_id: str):
        self.path = Path(root) / f"{run_id}.lock"
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("w")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"run is already locked: {self.path}") from exc
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.handle:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()

