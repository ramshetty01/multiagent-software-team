from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .architect import plan_from_issue
from .board import JsonlTaskBoard, append_many
from .github import GhIssueClient, parse_issue_ref, save_issue_context
from .messages import Message

NodeFn = Callable[["RunState"], "RunState"]


@dataclass
class RunState:
    run_id: str
    issue: str
    repo: str
    parallelism: int
    board_path: str
    artifact_dir: str
    status: str = "running"
    completed_nodes: list[str] | None = None


class Orchestrator:
    nodes = ("intake", "architect", "coder_fanout", "merge", "review", "test", "pr")

    def __init__(self, board: JsonlTaskBoard):
        self.board = board

    def run(self, state: RunState) -> RunState:
        state.completed_nodes = state.completed_nodes or self._completed_nodes(state.run_id)
        for node in self.nodes:
            if node in state.completed_nodes:
                continue
            state = getattr(self, node)(state)
            self._mark_done(state.run_id, node)
            state.completed_nodes.append(node)
            if state.status != "running":
                break
        return state

    def intake(self, state: RunState) -> RunState:
        context = GhIssueClient().fetch_issue(parse_issue_ref(state.issue))
        artifact = save_issue_context(context, Path(state.artifact_dir) / state.run_id / "issue.json")
        self.board.append(
            Message(
                type="plan_request",
                run_id=state.run_id,
                role="orchestrator",
                tags=["architect"],
                payload={"issue": context.url, "issue_artifact": str(artifact), "repo": state.repo, "parallelism": state.parallelism},
            )
        )
        return state

    def architect(self, state: RunState) -> RunState:
        requests = self.board.query(run_id=state.run_id, type="plan_request")
        issue_artifact = Path(requests[-1].payload["issue_artifact"])
        import json

        data = json.loads(issue_artifact.read_text())
        append_many(self.board, plan_from_issue(state.run_id, data["title"], data["body"]))
        return state

    def coder_fanout(self, state: RunState) -> RunState:
        subtasks = self.board.query(run_id=state.run_id, type="subtask")
        for subtask in subtasks[: state.parallelism]:
            self.board.append(
                Message(type="diff_ready", run_id=state.run_id, role=f"coder-{subtask.subtask_id}", tags=["merge"], subtask_id=subtask.subtask_id, payload={"changed_files": [], "patch": "", "tests": "not run"})
            )
        return state

    def merge(self, state: RunState) -> RunState:
        self.board.append(Message(type="review_needed", run_id=state.run_id, role="merge", tags=["reviewer"], payload={"staging_branch": f"staging/{state.run_id}"}))
        return state

    def review(self, state: RunState) -> RunState:
        self.board.append(Message(type="approved", run_id=state.run_id, role="reviewer", tags=["tester"], payload={"summary": "approved by orchestration placeholder"}))
        return state

    def test(self, state: RunState) -> RunState:
        self.board.append(Message(type="test_passed", run_id=state.run_id, role="tester", tags=["pr"], payload={"command": [], "stdout": "orchestration placeholder"}))
        return state

    def pr(self, state: RunState) -> RunState:
        self.board.append(Message(type="approved", run_id=state.run_id, role="pr", tags=["terminal"], payload={"status": "pr_ready"}))
        state.status = "succeeded"
        return state

    def _completed_nodes(self, run_id: str) -> list[str]:
        return [msg.payload["node"] for msg in self.board.query(run_id=run_id, role="orchestrator", tag="node_done")]

    def _mark_done(self, run_id: str, node: str) -> None:
        self.board.append(Message(type="approved", run_id=run_id, role="orchestrator", tags=["node_done"], payload={"node": node}))


def compile_langgraph():
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("install langgraph to compile the production graph") from exc

    graph = StateGraph(dict)
    for node in Orchestrator.nodes:
        graph.add_node(node, lambda state: state)
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "architect")
    graph.add_edge("architect", "coder_fanout")
    graph.add_edge("coder_fanout", "merge")
    graph.add_edge("merge", "review")
    graph.add_edge("review", "test")
    graph.add_edge("test", "pr")
    graph.add_edge("pr", END)
    return graph.compile()

