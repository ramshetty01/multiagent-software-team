from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .architect import plan_from_issue
from .board import JsonlTaskBoard, append_many
from .coder import CoderWorker
from .config import AppConfig
from .feedback import route_review_feedback
from .github import GhIssueClient, parse_issue_ref, save_issue_context
from .gitops import git
from .merge import MergeCoordinator
from .messages import Message
from .models import ModelProvider
from .observability import TraceLog
from .pr import create_pr_after_test_pass
from .providers import provider_for_role
from .reviewer import Reviewer
from .runner import Runner, runner_for_backend
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
    demo: bool = True

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", self.run_id):
            raise ValueError("run_id must contain 1–64 letters, numbers, underscores or hyphens")
        if not 1 <= self.parallelism <= 16:
            raise ValueError("parallelism must be between 1 and 16")


class Orchestrator:
    nodes = ("intake", "architect", "coder_fanout", "merge", "review", "test", "pr")

    def __init__(
        self,
        board: JsonlTaskBoard,
        coder_provider: ModelProvider | None = None,
        pr_creator: Callable[..., Message] | None = None,
        trace_log: TraceLog | None = None,
        config: AppConfig | None = None,
        providers: dict[str, ModelProvider] | None = None,
        runner: Runner | None = None,
    ):
        self.board = board
        self.coder_provider = coder_provider
        self.pr_creator = pr_creator or create_pr_after_test_pass
        self.trace_log = trace_log
        self.config = config or AppConfig()
        self.providers = providers or {}
        if coder_provider is not None:
            self.providers["coder"] = coder_provider
        self.runner = runner
        self.test_runner = runner

    def run(self, state: RunState) -> RunState:
        if not state.demo:
            self._configure_execution()
        identity = {"issue": state.issue, "repo": str(Path(state.repo).resolve()), "demo": state.demo}
        manifests = self.board.query(run_id=state.run_id, role="orchestrator", tag="run_manifest")
        if manifests and manifests[-1].payload != identity:
            raise ValueError("Run ID already belongs to a different issue, repository or execution mode.")
        if not manifests:
            self.board.append(Message(type="approved", run_id=state.run_id, role="orchestrator", tags=["run_manifest"], payload=identity))
        terminal = self.board.query(run_id=state.run_id, role="orchestrator", tag="run_terminal")
        if terminal:
            state.status = terminal[-1].payload["status"]
            state.completed_nodes = self._completed_nodes(state.run_id)
            return state
        if state.create_pr and state.demo:
            raise ValueError("Demo runs cannot create pull requests; use explicit execution mode.")
        completed = self._completed_nodes(state.run_id)
        state.completed_nodes = completed
        state.status = "running"
        for node in self.nodes:
            if node in completed:
                continue
            before = len(self.board.query(run_id=state.run_id))
            state = getattr(self, node)(state)
            self._trace(state.run_id, node, len(self.board.query(run_id=state.run_id)) - before)
            if state.status == "failed":
                # A failed stage is not a checkpoint. A fresh invocation retries it.
                break
            self._mark_done(state.run_id, node)
            completed.append(node)
            if state.status != "running":
                self.board.append(Message(type="approved", run_id=state.run_id, role="orchestrator", tags=["run_terminal"], payload={"status": state.status}))
                break
        return state

    def _configure_execution(self) -> None:
        # Hosted sandbox file synchronization is not implemented; never silently use local execution.
        if self.config.environment != "production" or self.config.sandbox_backend != "docker":
            raise ValueError("Execution requires production configuration and the Docker backend.")
        self.config.validate()
        for role in ("architect", "coder", "reviewer", "tester"):
            if role not in self.providers:
                self.providers[role] = provider_for_role(self.config, role)
        if self.runner is None:
            self.runner = runner_for_backend("docker", image=self.config.sandbox_image, timeout_seconds=self.config.limits.role_timeout_seconds)
        if self.test_runner is None:
            self.test_runner = runner_for_backend("docker", tester=True, image=self.config.sandbox_image, timeout_seconds=self.config.limits.role_timeout_seconds)

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
        requests = self.board.query(run_id=state.run_id, type="plan_request", role="orchestrator")
        issue_artifact = Path(requests[-1].payload["issue_artifact"])
        import json

        data = json.loads(issue_artifact.read_text())
        messages = plan_from_issue(state.run_id, data["title"], data["body"], provider=None if state.demo else self.providers["architect"], model=self.config.models.architect, allow_fallback=state.demo)
        append_many(self.board, messages)
        if not any(message.type == "subtask" for message in messages):
            state.status = "failed"
        return state

    def coder_fanout(self, state: RunState) -> RunState:
        def work(worker_id: str) -> None:
            provider = None if state.demo else self.providers.get("coder", self.coder_provider)
            worker = CoderWorker(self.board, worker_id, provider, model=self.config.models.coder, runner=self.runner)
            subtask = worker.claim_next(state.run_id)
            if not subtask:
                return
            if not state.demo:
                if provider is None:
                    raise ValueError("Configured coder provider is required for execution.")
                diffs = self.board.current_diffs(state.run_id)
                dependencies = [diffs[task].payload["branch"] for task in subtask.payload.get("depends_on", [])]
                worker.implement(
                    state.run_id, state.repo, str(Path(state.artifact_dir) / "worktrees"), subtask,
                    resolve_test_command(state.repo, state.test_command, production=True),
                    dependency_branches=dependencies,
                )
                return
            files = subtask.payload["contract"]["files"]
            worker.submit_diff(state.run_id, subtask, files, f"DEMO ONLY: planned implementation for {subtask.subtask_id}", "not executed")

        tasks = {m.subtask_id for m in self.board.query(run_id=state.run_id, type="subtask")}
        for _ in range(max(1, len(tasks))):
            before = set(self.board.current_diffs(state.run_id))
            if tasks and tasks <= before:
                return state
            result = WorkerSupervisor(self.board, state.parallelism).run_coders(state.run_id, work)
            after = set(self.board.current_diffs(state.run_id))
            if result.exit_code or after == before:
                break
        if not tasks or not tasks <= set(self.board.current_diffs(state.run_id)):
            state.status = "failed"
            self.board.append(Message(type="rejected", run_id=state.run_id, role="orchestrator", tags=["incomplete_tasks"], payload={"reason": "Task DAG did not complete; downstream stages withheld."}))
        return state

    def merge(self, state: RunState) -> RunState:
        diffs = list(self.board.current_diffs(state.run_id).values())
        if not diffs:
            state.status = "failed"
            self.board.append(Message(type="rejected", run_id=state.run_id, role="merge", tags=["merge"], payload={"reason": "no coder diffs ready"}))
            return state
        tasks = {m.subtask_id for m in self.board.query(run_id=state.run_id, type="subtask")}
        if tasks and not tasks <= {d.subtask_id for d in diffs}:
            state.status = "failed"
            return state
        branches = [message.payload.get("branch") for message in diffs]
        overlaps = [path for message in diffs for path in message.payload.get("changed_files", [])]
        if len(overlaps) - len(set(overlaps)) > state.max_conflict_files:
            state.status = "failed"
            self.board.append(Message(type="rejected", run_id=state.run_id, role="merge", tags=["merge", "conflict"], payload={"reason": "conflict file limit exceeded"}))
            return state
        if branches and all(isinstance(branch, str) and branch for branch in branches):
            base_ref = git(state.repo, "branch", "--show-current") or "HEAD"
            valid_branches = [branch for branch in branches if isinstance(branch, str)]
            outcome = MergeCoordinator().merge_branches(state.run_id, state.repo, base_ref, valid_branches)
            self.board.append(outcome)
            if outcome.type == "rejected":
                state.status = "failed"
            return state
        if not state.demo:
            state.status = "failed"
            return state
        outcome = MergeCoordinator().merge(state.run_id, diffs)
        self.board.append(outcome)
        if outcome.type == "rejected":
            state.status = "failed"
        return state

    def review(self, state: RunState) -> RunState:
        if not self.board.query(run_id=state.run_id, type="review_needed"):
            state.status = "failed"
            return state
        diffs = list(self.board.current_diffs(state.run_id).values())
        diff_summary = "\n".join(message.payload.get("patch", "") for message in diffs)
        if not state.demo:
            review = self.board.query(run_id=state.run_id, type="review_needed")[-1]
            diff_summary = git(state.repo, "diff", review.payload["base_commit"], review.payload["staging_commit"])
        decision = Reviewer(provider=None if state.demo else self.providers["reviewer"], model=self.config.models.reviewer).review(state.run_id, "merge", "reviewer", diff_summary)
        if decision.type == "review_feedback":
            route_review_feedback(self.board, state.run_id, decision, max_attempts=state.max_review_loops)
            self.board.append(Message(type="approved", run_id=state.run_id, role="orchestrator", tags=["checkpoint_reset"], payload={"from_node": "coder_fanout"}))
            state.status = "failed"
            return state
        self.board.append(decision)
        if decision.type != "approved":
            state.status = "failed"
        return state

    def test(self, state: RunState) -> RunState:
        if not self.board.query(run_id=state.run_id, type="approved", role="reviewer"):
            state.status = "failed"
            return state
        if state.demo:
            self.board.append(Message(type="approved", run_id=state.run_id, role="tester", tags=["demo"], payload={"status": "tests_not_executed"}))
            return state
        result = Tester(runner=self.test_runner, provider=self.providers.get("tester"), model=self.config.models.tester).test(state.run_id, state.repo, resolve_test_command(state.repo, state.test_command, production=True), retries=state.max_tester_reruns)
        self.board.append(result)
        if result.type != "test_passed":
            state.status = "failed"
        return state

    def pr(self, state: RunState) -> RunState:
        if state.demo:
            if state.create_pr:
                state.status = "failed"
                return state
            state.status = "demo_completed"
            self.board.append(Message(type="approved", run_id=state.run_id, role="pr", tags=["terminal", "demo"], payload={"status": "demo_completed", "note": "No implementation, test verification or pull request was produced."}))
            return state
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
        completed: list[str] = []
        for message in self.board.query(run_id=run_id, role="orchestrator"):
            if "checkpoint_reset" in message.tags:
                reset = self.nodes.index(message.payload["from_node"])
                completed = [node for node in completed if self.nodes.index(node) < reset]
            elif "node_done" in message.tags:
                if message.payload.get("checkpoint_version") != 2:
                    raise ValueError("Legacy graph checkpoints cannot be safely resumed; use a new run ID.")
                if message.payload["node"] not in completed:
                    completed.append(message.payload["node"])
        return completed

    def _mark_done(self, run_id: str, node: str) -> None:
        self.board.append(Message(type="approved", run_id=run_id, role="orchestrator", tags=["node_done"], payload={"node": node, "checkpoint_version": 2}))

    def _trace(self, run_id: str, node: str, payload_size: int) -> None:
        if self.trace_log:
            self.trace_log.record(run_id=run_id, role=node, model="", payload_size=payload_size)


def compile_langgraph():
    raise NotImplementedError(
        "Durable LangGraph execution is not implemented. Use Orchestrator.run; the previous identity-node scaffold did not execute work."
    )
