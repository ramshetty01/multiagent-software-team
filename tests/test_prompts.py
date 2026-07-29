from __future__ import annotations

import json

from mast.board import JsonlTaskBoard
from mast.coder import CoderWorker
from mast.messages import Message
from mast.models import FakeModelProvider
from mast.prompts import parse_architect_json


def test_parse_architect_json_validates_subtasks():
    tasks = parse_architect_json(
        json.dumps(
            {
                "subtasks": [
                    {"id": "a", "title": "A", "depends_on": [], "contract": {"files": ["a.py"], "public_functions": [], "test_impact": []}}
                ]
            }
        )
    )

    assert tasks[0].id == "a"


def test_coder_can_draft_patch_from_declared_files(tmp_path):
    (tmp_path / "a.py").write_text("print('old')\n")
    subtask = Message(type="subtask", run_id="r1", role="architect", payload={"contract": {"files": ["a.py"]}})
    worker = CoderWorker(JsonlTaskBoard(tmp_path / "board.jsonl"), "coder-a", FakeModelProvider({"coder": "diff --git"}))

    assert worker.draft_patch("r1", str(tmp_path), subtask) == "diff --git"

