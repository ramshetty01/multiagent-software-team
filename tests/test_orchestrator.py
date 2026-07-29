from __future__ import annotations

import subprocess

from mast.board import JsonlTaskBoard
from mast.gitops import git
from mast.messages import Message
from mast.models import FakeModelProvider
from mast.orchestrator import Orchestrator, RunState


class FakeOrchestrator(Orchestrator):
    def intake(self, state):
        return state

    def architect(self, state):
        return state

    def coder_fanout(self, state):
        self.board.append(Message(type="diff_ready", run_id=state.run_id, role="coder-1", subtask_id="s1", payload={"changed_files": ["a.py"], "patch": "patch"}))
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


def test_orchestrator_fails_without_required_role_artifacts(tmp_path):
    board = JsonlTaskBoard(tmp_path / "flow.jsonl")
    state = RunState("r3", "acme/project#1", str(tmp_path), 1, str(tmp_path / "flow.jsonl"), str(tmp_path))

    result = Orchestrator(board).merge(state)

    assert result.status == "failed"
    assert board.query(run_id="r3", type="rejected", role="merge")


def test_orchestrator_coder_node_uses_worktree_patch_loop(tmp_path):
    repo = tmp_path / "orchestrator-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "a.txt").write_text("old\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init")
    patch = """diff --git a/a.txt b/a.txt
--- a/a.txt
+++ b/a.txt
@@ -1 +1 @@
-old
+new
"""
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    board.append(
        Message(
            type="subtask",
            run_id="r4",
            role="architect",
            tags=["coder"],
            subtask_id="s1",
            payload={"title": "Change a", "contract": {"files": ["a.txt"], "test_impact": []}},
        )
    )
    state = RunState("r4", "acme/project#1", str(repo), 1, str(tmp_path / "board.jsonl"), str(tmp_path))

    Orchestrator(board, coder_provider=FakeModelProvider({"coder": patch})).coder_fanout(state)

    diff = board.query(run_id="r4", type="diff_ready")[-1]
    assert diff.payload["changed_files"] == ["a.txt"]
    assert "commit=" in diff.payload["tests"]


def test_orchestrator_merge_node_stages_coder_branches(tmp_path):
    repo = tmp_path / "merge-orchestrator-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init")
    git(repo, "switch", "-c", "coder-a")
    (repo / "a.txt").write_text("aa\n", encoding="utf-8")
    git(repo, "commit", "-am", "a")
    git(repo, "switch", "main")
    git(repo, "switch", "-c", "coder-b")
    (repo / "b.txt").write_text("bb\n", encoding="utf-8")
    git(repo, "commit", "-am", "b")
    git(repo, "switch", "main")
    board = JsonlTaskBoard(tmp_path / "merge-board.jsonl")
    board.append(Message(type="diff_ready", run_id="r5", role="coder-a", subtask_id="a", payload={"changed_files": ["a.txt"], "patch": "a", "branch": "coder-a"}))
    board.append(Message(type="diff_ready", run_id="r5", role="coder-b", subtask_id="b", payload={"changed_files": ["b.txt"], "patch": "b", "branch": "coder-b"}))
    state = RunState("r5", "acme/project#1", str(repo), 2, str(tmp_path / "merge-board.jsonl"), str(tmp_path))

    Orchestrator(board).merge(state)

    message = board.query(run_id="r5", type="review_needed")[-1]
    assert message.payload["staging_branch"] == "staging/r5"
    assert message.payload["staging_commit"]
    assert git(repo, "branch", "--show-current") == "staging/r5"
