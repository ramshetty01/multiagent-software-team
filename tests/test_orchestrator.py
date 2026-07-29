from __future__ import annotations

from mast.board import JsonlTaskBoard
from mast.messages import Message
from mast.orchestrator import Orchestrator, RunState


class FakeOrchestrator(Orchestrator):
    def intake(self, state):
        return state

    def architect(self, state):
        return state

    def coder_fanout(self, state):
        state.parallelism_seen = state.parallelism
        return state


def test_orchestrator_resumes_completed_nodes(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    state = RunState("r1", "acme/project#1", ".", 2, str(tmp_path / "board.jsonl"), str(tmp_path))
    first = FakeOrchestrator(board).run(state)
    second = FakeOrchestrator(board).run(state)

    assert first.status == "succeeded"
    assert second.status == "succeeded"
    assert len(board.query(run_id="r1", role="orchestrator", tag="node_done")) == 7


def test_orchestrator_uses_real_merge_review_test_nodes(tmp_path):
    board = JsonlTaskBoard(tmp_path / "flow.jsonl")
    state = RunState("r2", "acme/project#1", str(tmp_path), 1, str(tmp_path / "flow.jsonl"), str(tmp_path))
    board.append(Message(type="diff_ready", run_id="r2", role="coder-1", subtask_id="s1", payload={"changed_files": ["a.py"], "patch": ""}))
    orchestrator = Orchestrator(board)

    orchestrator.merge(state)
    orchestrator.review(state)
    orchestrator.test(state)

    assert board.query(run_id="r2", type="review_needed")
    assert board.query(run_id="r2", type="approved")
    assert board.query(run_id="r2", type="test_passed")
