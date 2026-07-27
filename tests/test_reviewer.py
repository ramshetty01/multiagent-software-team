from __future__ import annotations

import json

from mast.models import FakeModelProvider
from mast.prompts import parse_review_json
from mast.reviewer import Reviewer


def test_parse_review_json_requires_structured_feedback():
    parsed = parse_review_json(json.dumps({"decision": "request_changes", "requests": [{"path": "a.py", "severity": "high", "message": "bug"}]}))
    assert parsed["requests"][0]["path"] == "a.py"


def test_reviewer_returns_structured_model_feedback():
    provider = FakeModelProvider({"reviewer": json.dumps({"decision": "request_changes", "requests": [{"path": "a.py", "line": 1, "severity": "high", "message": "bug", "subtask_id": "a"}]})})

    message = Reviewer(provider).review("r1", "coder", "reviewer", "diff --git")

    assert message.type == "review_feedback"
    assert message.payload["requests"][0]["subtask_id"] == "a"

