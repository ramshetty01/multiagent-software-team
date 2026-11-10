from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

from .gitops import git
from .messages import Message


def file_overlaps(diff_messages: list[Message]) -> list[str]:
    counts = Counter(path for msg in diff_messages for path in msg.payload.get("changed_files", []))
    return sorted(path for path, count in counts.items() if count > 1)


class MergeCoordinator:
    def merge(self, run_id: str, diff_messages: list[Message]) -> Message:
        overlaps = file_overlaps(diff_messages)
        if overlaps:
            return Message(
                type="rejected",
                run_id=run_id,
                role="merge",
                tags=["merge", "conflict"],
                payload={"conflicts": overlaps, "resolution": "blocked until resolver is supplied"},
            )
        return Message(
            type="review_needed",
            run_id=run_id,
            role="merge",
            tags=["reviewer"],
            payload={"subtasks": [msg.subtask_id for msg in diff_messages], "conflicts": []},
        )

    def merge_branches(self, run_id: str, repo: str | Path, base_ref: str, branches: list[str]) -> Message:
        staging = f"staging/{run_id}"
        base_commit = git(repo, "rev-parse", base_ref)
        try:
            git(repo, "switch", "-C", staging, base_ref)
            for branch in sorted(branches):
                git(repo, "merge", "--no-edit", branch)
        except (OSError, subprocess.SubprocessError) as exc:
            conflicts = _conflicted_files(repo)
            return Message(
                type="rejected",
                run_id=run_id,
                role="merge",
                tags=["merge", "conflict"],
                payload={"staging_branch": staging, "branches": sorted(branches), "conflicts": conflicts, "error": str(exc)},
            )
        return Message(
            type="review_needed",
            run_id=run_id,
            role="merge",
            tags=["reviewer"],
            payload={"staging_branch": staging, "staging_commit": git(repo, "rev-parse", "HEAD"), "base_commit": base_commit, "branches": sorted(branches), "conflicts": []},
        )


def _conflicted_files(repo: str | Path) -> list[str]:
    try:
        output = git(repo, "diff", "--name-only", "--diff-filter=U")
    except (OSError, subprocess.SubprocessError):
        return []
    return [line for line in output.splitlines() if line]
