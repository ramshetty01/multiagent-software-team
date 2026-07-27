from __future__ import annotations

import argparse
from pathlib import Path
from uuid import uuid4

from .architect import plan_from_issue
from .board import JsonlTaskBoard, append_many
from .messages import Message
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

    report = sub.add_parser("report")
    report.add_argument("--out", default="runs/postmortem.md")
    report.add_argument("--failure", action="append", default=[])
    report.add_argument("--speedup", type=float, default=1.0)
    report.add_argument("--token-cost", type=float, default=0.0)

    args = parser.parse_args(argv)
    if args.cmd == "report":
        write_postmortem(args.out, args.failure, args.speedup, args.token_cost)
        print(args.out)
        return 0

    run_id = args.run_id or str(uuid4())
    board = JsonlTaskBoard(args.board)
    if not board.query(run_id=run_id):
        append_many(
            board,
            [
                Message(
                    type="plan_request",
                    run_id=run_id,
                    role="orchestrator",
                    tags=["architect"],
                    payload={"issue": args.issue, "repo": str(Path(args.repo)), "parallelism": args.parallelism},
                )
            ],
        )
        append_many(board, plan_from_issue(run_id, args.issue, f"Implement issue from {args.issue}"))
    print(f"run_id={run_id}")
    print(f"board={board.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

