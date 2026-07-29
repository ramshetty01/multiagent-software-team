from __future__ import annotations

from mast.board import JsonlTaskBoard
from mast.messages import Message
from mast.pr import create_pr_after_test_pass


def test_pr_creation_requires_test_pass(tmp_path):
    board = JsonlTaskBoard(tmp_path / "pr.jsonl")
    try:
        create_pr_after_test_pass(board, "r1", "o/r", "main", "h", "t", "b")
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected test gate")


def test_pr_creation_is_idempotent(tmp_path):
    board = JsonlTaskBoard(tmp_path / "pr-existing.jsonl")
    message = Message(type="approved", run_id="r1", role="pr", payload={"url": "u"})
    board.append(message)
    assert create_pr_after_test_pass(board, "r1", "o/r", "main", "h", "t", "b").payload["url"] == "u"

