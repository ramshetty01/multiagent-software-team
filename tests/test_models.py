from __future__ import annotations

from mast.architect import plan_from_issue
import json

from mast.models import FakeModelProvider, ModelProviderError, ModelRequest, complete_with_retry
from mast.reviewer import Reviewer


def test_fake_provider_returns_token_usage():
    provider = FakeModelProvider({"*": "hello world"})
    response = provider.complete(ModelRequest(run_id="r1", role="architect", model="fake", prompt="one two"))

    assert response.input_tokens == 2
    assert response.output_tokens == 2


def test_complete_with_retry_surfaces_structured_failure():
    try:
        complete_with_retry(FakeModelProvider(fail=True), ModelRequest("r1", "coder", "fake", "prompt"), attempts=1)
    except ModelProviderError as exc:
        assert exc.to_payload()["retryable"] is True
    else:
        raise AssertionError("expected provider failure")


def test_roles_use_shared_provider_interface():
    provider = FakeModelProvider({"architect": "plan", "reviewer": json.dumps({"decision": "request_changes", "requests": [{"path": "a.py", "message": "fix this"}]})})

    assert plan_from_issue("r1", "Issue", "Long enough issue body for planning.", provider)[0].payload["model_output"] == "plan"
    assert Reviewer(provider).review("r1", "coder", "reviewer", "diff").type == "review_feedback"
