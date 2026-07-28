from __future__ import annotations

import subprocess
import tempfile

from .board import JsonlTaskBoard
from .messages import Message


def create_pr_after_test_pass(
    board: JsonlTaskBoard,
    run_id: str,
    repo_full_name: str,
    base: str,
    head: str,
    title: str,
    body: str,
    draft: bool = False,
) -> Message:
    existing = board.query(run_id=run_id, role="pr", type="approved")
    if existing:
        return existing[-1]
    if not board.query(run_id=run_id, type="test_passed"):
        raise RuntimeError("cannot create PR before test_passed")
    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        handle.write(body)
        body_file = handle.name
    cmd = ["gh", "pr", "create", "--repo", repo_full_name, "--base", base, "--head", head, "--title", title, "--body-file", body_file]
    if draft:
        cmd.append("--draft")
    result = subprocess.run(cmd, text=True, capture_output=True, check=True)
    message = Message(type="approved", run_id=run_id, role="pr", tags=["terminal"], payload={"url": result.stdout.strip(), "base": base, "head": head})
    board.append(message)
    return message

