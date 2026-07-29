from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from .architect import plan_from_issue
from .board import JsonlTaskBoard, append_many
from .config import load_config
from .github import GhIssueClient, GitHubError, parse_issue_ref, save_issue_context
from .messages import Message
from .orchestrator import Orchestrator, RunState
from .reporting import write_postmortem


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mast")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run")
    run.add_argument("--issue", required=True)
    run.add_argument("--repo", default=".")
    run.add_argument("--parallelism", type=int, default=4)
    run.add_argument("--run-id")
    run.add_argument("--board", default="runs/board.jsonl")
    run.add_argument("--artifact-dir", default="runs")
    run.add_argument("--config")

    report = sub.add_parser("report")
    report.add_argument("--out", default="runs/postmortem.md")
    report.add_argument("--failure", action="append", default=[])
    report.add_argument("--speedup", type=float, default=1.0)
    report.add_argument("--token-cost", type=float, default=0.0)

    run_graph = sub.add_parser("run-graph")
    run_graph.add_argument("--issue", required=True)
    run_graph.add_argument("--repo", default=".")
    run_graph.add_argument("--parallelism", type=int, default=4)
    run_graph.add_argument("--run-id", required=True)
    run_graph.add_argument("--board", default="runs/board.jsonl")
    run_graph.add_argument("--artifact-dir", default="runs")

    args = parser.parse_args(argv)
    if args.cmd == "report":
        write_postmortem(args.out, args.failure, args.speedup, args.token_cost)
        print(args.out)
        return 0
    if args.cmd == "run-graph":
        state = Orchestrator(JsonlTaskBoard(args.board)).run(
            RunState(args.run_id, args.issue, args.repo, args.parallelism, args.board, args.artifact_dir)
        )
        print(f"run_id={state.run_id}")
        print(f"status={state.status}")
        return 0

    run_id = args.run_id or str(uuid4())
    try:
        config = load_config(args.config)
    except ValueError as exc:
        print(json.dumps({"error": "invalid_config", "message": str(exc)}, sort_keys=True))
        return 2
    board = JsonlTaskBoard(args.board)
    if not board.query(run_id=run_id):
        try:
            issue_context = GhIssueClient().fetch_issue(parse_issue_ref(args.issue))
        except GitHubError as exc:
            print(json.dumps(exc.to_dict(), sort_keys=True))
            return 2
        issue_artifact = save_issue_context(issue_context, Path(args.artifact_dir) / run_id / "issue.json")
        append_many(
            board,
            [
                Message(
                    type="plan_request",
                    run_id=run_id,
                    role="orchestrator",
                    tags=["architect"],
                    payload={
                        "issue": issue_context.url,
                        "issue_artifact": str(issue_artifact),
                        "repo": str(Path(args.repo)),
                        "parallelism": args.parallelism,
                        "sandbox_backend": config.sandbox_backend,
                        "tracing_backend": config.tracing_backend,
                    },
                )
            ],
        )
        append_many(board, plan_from_issue(run_id, issue_context.title, issue_context.body))
    print(f"run_id={run_id}")
    print(f"board={board.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
