from __future__ import annotations

import os

import pytest

from mast.config import AppConfig
from mast.models import ModelRequest
from mast.providers import provider_for_role


pytestmark = pytest.mark.skipif(os.environ.get("MAST_LIVE_PROVIDER_TESTS") != "1", reason="live provider tests are opt-in")


def _config() -> AppConfig:
    missing = [
        name
        for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        pytest.skip(f"missing live provider keys: {', '.join(missing)}")
    return AppConfig(
        environment="production",
        github_token=os.environ.get("GITHUB_TOKEN", "live-provider-test-token"),
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        openai_api_key=os.environ["OPENAI_API_KEY"],
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )


@pytest.mark.parametrize(
    ("role", "model"),
    [
        ("architect", "claude-opus"),
        ("coder", "claude-sonnet"),
        ("reviewer", "gpt-5"),
        ("tester", "gemini-pro"),
    ],
)
def test_live_provider_returns_text_and_usage(role: str, model: str):
    provider = provider_for_role(_config(), role)

    response = provider.complete(ModelRequest("live-provider-test", role, model, "Reply with exactly: ok"))

    assert response.text
    assert response.input_tokens >= 0
    assert response.output_tokens >= 0
