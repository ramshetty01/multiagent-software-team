from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

from .board import JsonlTaskBoard
from .messages import Message

WorkerFn = Callable[[str], None]


@dataclass
class SupervisorResult:
    started: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.failed else 0


class WorkerSupervisor:
    def __init__(self, board: JsonlTaskBoard, parallelism: int):
        self.board = board
        self.parallelism = max(1, parallelism)

    def run_coders(self, run_id: str, worker_fn: WorkerFn) -> SupervisorResult:
        result = SupervisorResult()
        worker_ids = [f"coder-{index + 1}" for index in range(self.parallelism)]
        with ThreadPoolExecutor(max_workers=self.parallelism) as pool:
            futures = {}
            for worker_id in worker_ids:
                self._event(run_id, worker_id, "started")
                result.started += 1
                futures[pool.submit(worker_fn, worker_id)] = worker_id
            for future in as_completed(futures):
                worker_id = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    result.failed += 1
                    result.errors.append(f"{worker_id}: {exc}")
                    self._event(run_id, worker_id, "failed", {"error": str(exc)})
                else:
                    self._event(run_id, worker_id, "finished")
        return result

    def _event(self, run_id: str, worker_id: str, status: str, payload: dict | None = None) -> None:
        self.board.append(
            Message(
                type="approved",
                run_id=run_id,
                role="supervisor",
                tags=["worker_lifecycle", worker_id],
                payload={"worker_id": worker_id, "status": status, **(payload or {})},
            )
        )

