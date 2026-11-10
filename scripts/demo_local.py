#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mast.board import JsonlTaskBoard, append_many
from mast.messages import Message
from mast.status import run_status


def demo_messages(run_id: str) -> list[Message]:
    return [
        Message(
            type="plan_request",
            run_id=run_id,
            role="architect",
            tags=["architect"],
            payload={
                "issue_url": "https://github.com/example/service/issues/42",
                "subtasks": ["demo-api", "demo-tests"],
            },
        ),
        Message(
            type="subtask",
            run_id=run_id,
            role="architect",
            tags=["coder"],
            subtask_id="demo-api",
            payload={
                "title": "Add read-only health endpoint",
                "contract": {
                    "files": ["src/service.py"],
                    "public_interfaces": ["GET /healthz -> {status, version}"],
                    "test_impact": "covered by service tests",
                },
                "depends_on": [],
            },
        ),
        Message(
            type="subtask",
            run_id=run_id,
            role="architect",
            tags=["coder"],
            subtask_id="demo-tests",
            payload={
                "title": "Cover health endpoint response shape",
                "contract": {
                    "files": ["tests/test_service.py"],
                    "public_interfaces": ["test_healthz_response_shape"],
                    "test_impact": "new unit test",
                },
                "depends_on": ["demo-api"],
            },
        ),
        Message(
            type="diff_ready",
            run_id=run_id,
            role="coder-a",
            tags=["diff"],
            subtask_id="demo-api",
            payload={"branch": "mast/demo-api", "tests": "pytest tests/test_service.py"},
        ),
        Message(
            type="diff_ready",
            run_id=run_id,
            role="coder-b",
            tags=["diff"],
            subtask_id="demo-tests",
            payload={"branch": "mast/demo-tests", "tests": "pytest tests/test_service.py"},
        ),
        Message(
            type="approved",
            run_id=run_id,
            role="reviewer",
            tags=["review"],
            payload={"decision": "approved", "summary": "Diff is scoped and covered."},
        ),
        Message(
            type="test_passed",
            run_id=run_id,
            role="tester",
            tags=["test"],
            payload={"command": "pytest", "duration_seconds": 12.4, "artifacts": ["test.log"]},
        ),
    ]


def write_demo(out_dir: Path, run_id: str) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    board = JsonlTaskBoard(out_dir / "board.jsonl")
    append_many(board, demo_messages(run_id))
    status = run_status(board, run_id)
    (out_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Create local demo artifacts for a dry-run multi-agent workflow.")
    parser.add_argument("--out", default="runs/demo", help="Directory for generated board and status artifacts.")
    parser.add_argument("--run-id", default="demo-run", help="Run ID to write into the demo board.")
    args = parser.parse_args()

    status = write_demo(Path(args.out), args.run_id)
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
