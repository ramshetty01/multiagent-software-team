from __future__ import annotations

import json

from mast.artifacts import ArtifactStore
from mast.runner import CommandResult
from mast.tester import Tester


class FailingRunner:
    def run(self, command, cwd):
        return CommandResult(command, str(cwd), 1, "out", "err", 0.1)


def test_artifact_store_writes_json(tmp_path):
    path = ArtifactStore(tmp_path).write_json("r1", "data.json", {"ok": True})
    assert json.loads(open(path).read())["ok"] is True


def test_tester_failure_links_artifacts(tmp_path):
    message = Tester(FailingRunner()).test("r1", tmp_path, ["python3", "-V"], artifact_store=ArtifactStore(tmp_path / "artifacts"))
    assert "stderr" in message.payload["artifacts"]

