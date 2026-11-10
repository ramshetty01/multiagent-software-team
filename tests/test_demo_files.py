from __future__ import annotations

import json

from scripts.demo_local import write_demo


def test_demo_script_writes_board_and_status(tmp_path):
    status = write_demo(tmp_path, "demo-test")

    board = tmp_path / "board.jsonl"
    status_file = tmp_path / "status.json"

    assert board.exists()
    assert status_file.exists()
    assert status["status"] == "succeeded"
    assert status["messages"] == 7
    assert json.loads(status_file.read_text(encoding="utf-8"))["run_id"] == "demo-test"


def test_checked_in_demo_artifacts_exist():
    assert "demo-api" in __import__("pathlib").Path("examples/demo-board.jsonl").read_text()
    assert "Role summary" in __import__("pathlib").Path("examples/demo-report.md").read_text()
