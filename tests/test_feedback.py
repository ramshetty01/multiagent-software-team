from __future__ import annotations

from mast.board import JsonlTaskBoard
from mast.feedback import route_review_feedback
from mast.messages import Message


def test_route_review_feedback_to_owning_subtask(tmp_path):
    board = JsonlTaskBoard(tmp_path / "feedback.jsonl")
    board.append(Message(type="subtask", run_id="r1", role="architect", subtask_id="s1", payload={"title": "s1", "contract": {"files": ["a.py"]}}))
    feedback = Message(type="review_feedback", run_id="r1", role="reviewer", payload={"requests": [{"path": "a.py", "message": "fix"}]})

    routed = route_review_feedback(board, "r1", feedback)

    assert routed[0].subtask_id == "s1"
