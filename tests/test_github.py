from __future__ import annotations

import json

from mast.github import IssueContext, parse_issue_ref, save_issue_context


def test_parse_issue_ref_accepts_url_and_short_form():
    assert parse_issue_ref("https://github.com/acme/project/issues/42").repository == "acme/project"
    assert parse_issue_ref("acme/project#42").number == 42


def test_save_issue_context_writes_normalized_artifact(tmp_path):
    context = IssueContext(
        repository="acme/project",
        number=42,
        url="https://github.com/acme/project/issues/42",
        title="Bug",
        body="Fix this bug with enough detail.",
        labels=["bug"],
        comments=[],
        linked_pull_requests=[],
        repository_metadata={"nameWithOwner": "acme/project"},
    )

    path = save_issue_context(context, tmp_path / "issue.json")

    assert json.loads(path.read_text())["repository"] == "acme/project"

