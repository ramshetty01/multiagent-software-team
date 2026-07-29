from __future__ import annotations

from mast.eval import validate_issue_ids


def test_validate_issue_ids_rejects_placeholders():
    try:
        validate_issue_ids(["issue-001"])
    except ValueError as exc:
        assert "placeholder" in str(exc)
    else:
        raise AssertionError("expected placeholder rejection")

