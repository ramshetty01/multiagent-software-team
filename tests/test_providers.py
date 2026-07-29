from __future__ import annotations

from mast.config import AppConfig
from mast.models import FakeModelProvider
from mast.providers import provider_for_role


def test_provider_factory_uses_fake_in_local():
    assert isinstance(provider_for_role(AppConfig(environment="local"), "reviewer"), FakeModelProvider)


def test_provider_factory_requires_prod_keys():
    try:
        provider_for_role(AppConfig(environment="production"), "reviewer")
    except ValueError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("expected missing key failure")

