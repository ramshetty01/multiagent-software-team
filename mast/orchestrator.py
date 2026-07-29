from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .architect import plan_from_issue
from .board import JsonlTaskBoard, append_many
from .github import GhIssueClient, parse_issue_ref, save_issue_context
from .gitops import git
from .feedback import route_review_feedback
from .merge import MergeCoordinator
from .messages import Message
from .models import ModelProvider
from .observability import TraceLog
from .pr import create_pr_after_test_pass
from .reviewer import Reviewer
from .coder import CoderWorker
from .supervisor import WorkerSupervisor
from .tester import Tester, resolve_test_command

NodeFn = Callable[["RunState"], "RunState"]


@dataclass
class RunState:
    run_id: str
    issue: str
    repo: str
    parallelism: int
    board_path: str
    artifact_dir: str
    test_command: list[str] | None = None
    create_pr: bool = False
    max_review_loops: int = 3
    max_tester_reruns: int = 1
    max_conflict_files: int = 2
    status: str = "running"
    completed_nodes: list[str] | None = None


class Orchestrator:
    nodes = ("intake", "architect", "coder_fanout", "merge", "review", "test", "pr")

    def __init__(
        self,
        board: JsonlTaskBoard,
        coder_provider: ModelProvider | None = None,
        pr_creator: Callable[..., Message] | None = None,
        trace_log: TraceLog | None = None,
    ):
        self.board = board
        self.coder_provider = coder_provider
        self.pr_creator = pr_creator or create_pr_after_test_pass
        self.trace_log = trace_log

    def run(self, state: RunState) -> RunState:
        state.completed_nodes = state.completed_nodes or self._completed_nodes(state.run_id)
        for node in self.nodes:
            if node in state.completed_nodes:
                continue
            before = len(self.board.query(run_id=state.run_id))
            state = getattr(self, node)(state)
            self._trace(state.run_id, node, len(self.board.query(run_id=state.run_id)) - before)
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
        def work(worker_id: str) -> None:
            worker = CoderWorker(self.board, worker_id, self.coder_provider)
            subtask = worker.claim_next(state.run_id)
            if not subtask:
                return
            if self.coder_provider:
                worker.implement(
                    state.run_id,
                    state.repo,
                    str(Path(state.artifact_dir) / "worktrees"),
                    subtask,
                    state.test_command or ["git", "diff", "--check"],
                )
                return
            files = subtask.payload["contract"]["files"]
            worker.submit_diff(
                state.run_id,
                subtask,
                files,
                f"planned implementation for {subtask.subtask_id}",
                "deferred to tester",
            )

        result = WorkerSupervisor(self.board, state.parallelism).run_coders(state.run_id, work)
        if result.exit_code:
            state.status = "failed"
        return state

    def merge(self, state: RunState) -> RunState:
        diffs = self.board.query(run_id=state.run_id, type="diff_ready")
        if not diffs:
            state.status = "failed"
            self.board.append(Message(type="rejected", run_id=state.run_id, role="merge", tags=["merge"], payload={"reason": "no coder diffs ready"}))
            return state
        branches = [message.payload.get("branch") for message in diffs]
        overlaps = [path for message in diffs for path in message.payload.get("changed_files", [])]
        if len(overlaps) - len(set(overlaps)) > state.max_conflict_files:
            state.status = "failed"
            self.board.append(Message(type="rejected", run_id=state.run_id, role="merge", tags=["merge", "conflict"], payload={"reason": "conflict file limit exceeded"}))
            return state
        if branches and all(isinstance(branch, str) and branch for branch in branches):
            base_ref = git(state.repo, "branch", "--show-current") or "HEAD"
            self.board.append(MergeCoordinator().merge_branches(state.run_id, state.repo, base_ref, branches))
            return state
        self.board.append(MergeCoordinator().merge(state.run_id, diffs))
        return state

    def review(self, state: RunState) -> RunState:
        if not self.board.query(run_id=state.run_id, type="review_needed"):
            state.status = "failed"
            return state
        diffs = self.board.query(run_id=state.run_id, type="diff_ready")
        diff_summary = "\n".join(message.payload.get("patch", "") for message in diffs)
        decision = Reviewer().review(state.run_id, "merge", "reviewer", diff_summary)
        if decision.type == "review_feedback":
            route_review_feedback(self.board, state.run_id, decision, max_attempts=state.max_review_loops)
            state.status = "failed"
            return state
        self.board.append(decision)
        return state

    def test(self, state: RunState) -> RunState:
        if not self.board.query(run_id=state.run_id, type="approved", role="reviewer"):
            state.status = "failed"
            return state
        self.board.append(Tester().test(state.run_id, state.repo, resolve_test_command(state.repo, state.test_command), retries=state.max_tester_reruns))
        return state

    def pr(self, state: RunState) -> RunState:
        if not self.board.query(run_id=state.run_id, type="approved", role="reviewer") or not self.board.query(run_id=state.run_id, type="test_passed"):
            state.status = "failed"
            return state
        review = self.board.query(run_id=state.run_id, type="review_needed")[-1]
        if state.create_pr:
            issue = parse_issue_ref(state.issue)
            head = review.payload.get("staging_branch")
            if not isinstance(head, str) or not head:
                state.status = "failed"
                return state
            self.pr_creator(
                self.board,
                state.run_id,
                issue.repository,
                "main",
                head,
                f"Fix {state.issue}",
                f"Automated run `{state.run_id}`.\n\nCloses {state.issue}",
            )
            state.status = "succeeded"
            return state
        self.board.append(
            Message(
                type="approved",
                run_id=state.run_id,
                role="pr",
                tags=["terminal"],
                payload={"status": "pr_ready", "merge": review.payload},
            )
        )
        state.status = "succeeded"
        return state

    def _completed_nodes(self, run_id: str) -> list[str]:
        return [msg.payload["node"] for msg in self.board.query(run_id=run_id, role="orchestrator", tag="node_done")]

    def _mark_done(self, run_id: str, node: str) -> None:
        self.board.append(Message(type="approved", run_id=run_id, role="orchestrator", tags=["node_done"], payload={"node": node}))

    def _trace(self, run_id: str, node: str, payload_size: int) -> None:
        if self.trace_log:
            self.trace_log.record(run_id=run_id, role=node, model="", payload_size=payload_size)


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
