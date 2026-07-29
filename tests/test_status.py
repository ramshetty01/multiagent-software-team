from __future__ import annotations

from mast.board import JsonlTaskBoard
from mast.messages import Message
from mast.status import run_status


def test_run_status_summarizes_terminal_state(tmp_path):
    board = JsonlTaskBoard(tmp_path / "status.jsonl")
    board.append(Message(type="test_passed", run_id="r1", role="tester", payload={}))
    summary = run_status(board, "r1")
    assert summary["status"] == "succeeded"
    assert summary["counts"]["test_passed"] == 1

