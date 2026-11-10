from __future__ import annotations

from dataclasses import replace

import pytest

from mast.architect import plan_from_issue
from mast.board import JsonlTaskBoard
from mast.cli import main
from mast.config import AppConfig
from mast.messages import Message
from mast.models import FakeModelProvider
from mast.orchestrator import Orchestrator, RunState
from mast.runner import CommandResult
from mast.status import run_status
from mast.tester import Tester as TestWorker


def task(board, task_id, dependencies=()):
    board.append(Message(type="subtask", run_id="regression", role="architect", subtask_id=task_id, payload={"title": task_id, "depends_on": list(dependencies), "contract": {"files": [f"{task_id}.txt"]}}))


def done(board, task_id):
    board.append(Message(type="diff_ready", run_id="regression", role="coder", subtask_id=task_id, payload={"patch": "demo", "changed_files": [f"{task_id}.txt"]}))


def state(tmp_path):
    return RunState("regression", "acme/project#1", str(tmp_path), 1, str(tmp_path / "board.jsonl"), str(tmp_path))


def test_dependencies_and_requeued_history_are_respected(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    task(board, "child", ["parent"])
    task(board, "parent")
    claim = board.claim_subtask("regression", "worker")
    assert claim.subtask_id == "parent"
    assert board.claim_subtask("regression", "other") is None
    done(board, "parent")
    assert board.claim_subtask("regression", "other").subtask_id == "child"
    done(board, "child")
    board.append(Message(type="subtask_requeued", run_id="regression", role="reviewer", subtask_id="child", payload={}))
    assert set(board.current_diffs("regression")) == {"parent"}
    assert board.claim_subtask("regression", "new-worker").subtask_id == "child"
    done(board, "child")
    board.append(Message(type="subtask_requeued", run_id="regression", role="reviewer", subtask_id="parent", payload={}))
    assert not board.current_diffs("regression")
    assert board.claim_subtask("regression", "another-worker").subtask_id == "parent"


def test_dag_larger_than_parallelism_drains_before_merge(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    for index in range(7):
        task(board, str(index), [str(index - 1)] if index else [])
    run = state(tmp_path)
    assert Orchestrator(board).coder_fanout(run).status == "running"
    assert len(board.current_diffs(run.run_id)) == 7
    assert not board.query(run_id=run.run_id, type="test_passed")


def test_unresolved_dependency_blocks_merge(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    task(board, "child", ["missing"])
    run = Orchestrator(board).coder_fanout(state(tmp_path))
    assert run.status == "failed"
    assert not board.current_diffs(run.run_id)


class RetryGraph(Orchestrator):
    nodes = ("intake", "architect", "pr")
    failures = 1

    def intake(self, run):
        return run

    def architect(self, run):
        if self.failures:
            self.failures -= 1
            run.status = "failed"
        return run

    def pr(self, run):
        run.status = "demo_completed"
        return run


def test_failed_node_is_retried_and_fresh_terminal_resume_is_idempotent(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    graph = RetryGraph(board)
    assert graph.run(state(tmp_path)).status == "failed"
    assert graph._completed_nodes("regression") == ["intake"]
    assert graph.run(state(tmp_path)).status == "demo_completed"
    count = len(board.read())
    assert RetryGraph(board).run(state(tmp_path)).status == "demo_completed"
    assert len(board.read()) == count
    assert run_status(board, "regression")["status"] == "demo_completed"


def test_run_identity_prevents_cross_repo_resume(tmp_path):
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    graph = RetryGraph(board)
    graph.run(state(tmp_path))
    with pytest.raises(ValueError, match="different issue"):
        graph.run(replace(state(tmp_path), issue="acme/other#1"))


def test_live_execution_cannot_fall_back_to_local_runner(tmp_path):
    graph = Orchestrator(JsonlTaskBoard(tmp_path / "board.jsonl"))
    with pytest.raises(ValueError, match="Docker"):
        graph.run(replace(state(tmp_path), demo=False))


def test_invalid_architect_output_does_not_use_canned_plan_for_execution():
    messages = plan_from_issue("r", "Fix issue", "An issue description with sufficient detail", provider=FakeModelProvider({"architect": "nonsense"}), allow_fallback=False)
    assert [m.type for m in messages] == ["replan_needed"]


def test_cli_returns_nonzero_for_failed_graph_and_prohibits_demo_pr(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("mast.cli.load_config", lambda _: AppConfig())
    monkeypatch.setattr("mast.cli.Orchestrator.run", lambda self, run: replace(run, status="failed"))
    args = ["run-graph", "--issue", "acme/project#1", "--run-id", "cli-regression", "--board", str(tmp_path / "board.jsonl"), "--artifact-dir", str(tmp_path)]
    assert main(args) == 2
    assert "status=failed" in capsys.readouterr().out


def test_demo_cannot_publish_pr(tmp_path):
    with pytest.raises(ValueError, match="Demo runs"):
        Orchestrator(JsonlTaskBoard(tmp_path / "board.jsonl")).run(replace(state(tmp_path), create_pr=True))


def test_tester_owner_assignment_preserves_frozen_message(tmp_path):
    class Runner:
        def run(self, command, cwd):
            return CommandResult(command, str(cwd), 1, "", "src/module.py: failure", 0.01)

    result = TestWorker(runner=Runner()).test("run", tmp_path, ["python3", "-m", "pytest"], ownership={"src/module.py": "task-a"})
    assert result.subtask_id == "task-a"


def test_real_graph_wires_roles_and_merges_dependency_context(tmp_path):
    import json
    import subprocess

    from mast.gitops import git
    from mast.models import ModelResponse

    repo = tmp_path / "target"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    (repo / "a.txt").write_text("old\n")
    (repo / "b.txt").write_text("old\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "fixture")
    board = JsonlTaskBoard(tmp_path / "board.jsonl")
    issue = tmp_path / "issue.json"
    issue.write_text(json.dumps({"title": "Update two files", "body": "Update both files with dependency context and verify the outcome."}))

    class Graph(Orchestrator):
        def intake(self, run):
            self.board.append(Message(type="plan_request", run_id=run.run_id, role="orchestrator", payload={"issue_artifact": str(issue)}))
            return run

    tasks = [{"id": "a", "title": "Update a", "depends_on": [], "contract": {"files": ["a.txt"]}}, {"id": "b", "title": "Update b", "depends_on": ["a"], "contract": {"files": ["a.txt", "b.txt"]}}]
    architect = FakeModelProvider({"architect": json.dumps({"subtasks": tasks})})
    reviewer = FakeModelProvider({"reviewer": '{"decision":"approved"}'})

    class Coder:
        def __init__(self):
            self.calls = []

        def complete(self, request):
            self.calls.append(request)
            filename = "b.txt" if "b.txt" in request.files else "a.txt"
            if filename == "b.txt":
                assert request.files["a.txt"] == "new\n"
            patch = f"diff --git a/{filename} b/{filename}\n--- a/{filename}\n+++ b/{filename}\n@@ -1 +1 @@\n-old\n+new\n"
            return ModelResponse(patch, 10, 10, 0.001)

    class Runner:
        def __init__(self):
            self.calls = []

        def run(self, command, cwd):
            self.calls.append(str(cwd))
            return CommandResult(command, str(cwd), 0, "fixture test", "", 0.001)

    coder, runner = Coder(), Runner()
    config = AppConfig(environment="production", sandbox_backend="docker", github_token="test-only", anthropic_api_key="test-only", openai_api_key="test-only", google_api_key="test-only")
    graph = Graph(board, config=config, providers={"architect": architect, "coder": coder, "reviewer": reviewer, "tester": FakeModelProvider()}, runner=runner)
    run = replace(state(tmp_path), repo=str(repo), demo=False, test_command=["git", "diff", "--check"])
    assert graph.run(run).status == "succeeded"
    assert (repo / "a.txt").read_text() == (repo / "b.txt").read_text() == "new\n"
    assert len(coder.calls) == 2
    assert len(runner.calls) == 3  # two coder checks and the final staged test
    assert len(reviewer.calls) == 1 and "a.txt" in reviewer.calls[0].prompt and "b.txt" in reviewer.calls[0].prompt
    assert board.query(run_id=run.run_id, type="test_passed")
    before = len(board.read())
    assert graph.run(replace(run, completed_nodes=None, status="running")).status == "succeeded"
    assert len(board.read()) == before
