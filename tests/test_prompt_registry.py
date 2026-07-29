from __future__ import annotations

from mast.models import ModelRequest
from mast.prompt_registry import get_prompt


def test_prompt_registry_exposes_versions():
    prompt = get_prompt("architect.plan")
    assert prompt.version
    assert "Title" in prompt.render(title="T", body="B")


def test_model_request_carries_prompt_metadata():
    request = ModelRequest("r1", "architect", "m", "p", prompt_name="architect.plan", prompt_version="v1")
    assert request.prompt_name == "architect.plan"

