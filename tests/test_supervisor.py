from __future__ import annotations

from mast.board import JsonlTaskBoard
from mast.supervisor import WorkerSupervisor


def test_supervisor_limits_parallel_workers_and_records_lifecycle(tmp_path):
    board = JsonlTaskBoard(tmp_path / "supervisor.jsonl")
    seen = []

    def worker(worker_id: str) -> None:
        seen.append(worker_id)

    result = WorkerSupervisor(board, 3).run_coders("r1", worker)

    assert result.exit_code == 0
    assert len(seen) == 3
    assert len(board.query(run_id="r1", role="supervisor", tag="worker_lifecycle")) == 6


def test_supervisor_reports_worker_failure(tmp_path):
    board = JsonlTaskBoard(tmp_path / "supervisor-fail.jsonl")

    def worker(worker_id: str) -> None:
        if worker_id == "coder-2":
            raise RuntimeError("boom")

    result = WorkerSupervisor(board, 2).run_coders("r1", worker)

    assert result.exit_code == 1
    assert result.failed == 1

