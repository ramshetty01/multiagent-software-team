from __future__ import annotations

import subprocess

from mast.board import JsonlTaskBoard
from mast.coder import CoderWorker
from mast.gitops import git
from mast.messages import Message
from mast.models import FakeModelProvider


def test_coder_patch_loop_applies_diff_and_commits(tmp_path):
    repo = tmp_path / "patch-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "a.txt").write_text("old\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init")
    patch = """diff --git a/a.txt b/a.txt
--- a/a.txt
+++ b/a.txt
@@ -1 +1 @@
-old
+new
"""
    subtask = Message(type="subtask", run_id="r2", role="architect", subtask_id="patch", payload={"title": "patch", "contract": {"files": ["a.txt"], "test_impact": []}})
    worker = CoderWorker(JsonlTaskBoard(tmp_path / "board.jsonl"), "coder-a", FakeModelProvider({"coder": patch}))

    message = worker.implement("r2", str(repo), str(tmp_path / "patch-worktrees"), subtask, ["git", "diff", "--check"])

    assert message.type == "diff_ready"
    assert "commit=" in message.payload["tests"]
