from __future__ import annotations

from mast.architect import plan_from_issue
from mast.board import JsonlTaskBoard
from mast.coder import CoderWorker
from mast.merge import MergeCoordinator, file_overlaps
from mast.messages import Message
from mast.observability import token_amplification
from mast.reporting import handoff_histogram
from mast.reviewer import Reviewer
from mast.schema import InterfaceContract, Subtask, validate_dag


def test_schema_dag_and_status():
    tasks = [Subtask("a", "A", InterfaceContract(["a.py"])), Subtask("b", "B", InterfaceContract(["b.py"]), ["a"])]
    validate_dag(tasks)
    tasks[0].transition("claimed")
    tasks[0].transition("done")
    assert tasks[0].status == "done"


def test_architect_rejects_ambiguous_issue():
    messages = plan_from_issue("r1", "", "short")
    assert messages[0].type == "replan_needed"


def test_coder_scope_guard(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    subtask = Message(
        type="subtask",
        run_id="r1",
        role="architect",
        subtask_id="s1",
        payload={"contract": {"files": ["src/a.py"], "test_impact": ["tests/test_a.py"]}},
    )
    worker = CoderWorker(board, "coder-a")
    rejected = worker.submit_diff("r1", subtask, ["src/b.py"], "", "")
    assert rejected.type == "replan_needed"
    assert rejected.payload["contract"]["files"] == ["src/a.py"]
    assert worker.submit_diff("r1", subtask, ["src/a.py"], "patch", "ok").type == "diff_ready"


def test_merge_reviewer_metrics_and_reporting():
    diffs = [
        Message(type="diff_ready", run_id="r1", role="coder-a", subtask_id="a", payload={"changed_files": ["a.py"]}),
        Message(type="diff_ready", run_id="r1", role="coder-b", subtask_id="b", payload={"changed_files": ["b.py"]}),
    ]
    assert file_overlaps(diffs) == []
    assert MergeCoordinator().merge("r1", diffs).type == "review_needed"
    assert Reviewer().review("r1", "coder-a", "reviewer", "ok").type == "approved"
    assert Reviewer().review("r1", "reviewer", "reviewer", "ok").type == "rejected"
    assert token_amplification(100, 300) == 4
    assert handoff_histogram(["merge_conflict", "nope"])["other"] == 1
