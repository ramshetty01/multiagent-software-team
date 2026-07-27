from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from mast.board import JsonlTaskBoard
from mast.messages import Message


def test_board_handles_parallel_writes(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")

    def write(index: int) -> None:
        board.append(Message(type="subtask", run_id="r1", role="architect", payload={"index": index}))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(write, range(50)))

    assert len(board.query(run_id="r1", type="subtask")) == 50

