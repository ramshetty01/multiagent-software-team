from __future__ import annotations

from mast.board import JsonlTaskBoard
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

