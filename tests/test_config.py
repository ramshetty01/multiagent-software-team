from __future__ import annotations

import json

from mast.config import AppConfig, load_config, redact_secrets


def test_load_config_from_file_and_env(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"sandbox_backend": "docker", "models": {"coder": "sonnet-prod"}, "limits": {"max_review_loops": 4}}))

    config = load_config(path, {"MAST_ENV": "local", "MAST_REVIEWER_MODEL": "gpt-prod"})

    assert config.sandbox_backend == "docker"
    assert config.models.coder == "sonnet-prod"
    assert config.models.reviewer == "gpt-prod"
    assert config.limits.max_review_loops == 4


def test_runtime_limits_must_be_positive():
    try:
        load_config(env={"MAST_MAX_REVIEW_LOOPS": "0"})
    except ValueError as exc:
        assert "runtime limits" in str(exc)
    else:
        raise AssertionError("expected invalid runtime limit")


def test_production_config_requires_provider_keys():
    try:
        load_config(env={"MAST_ENV": "production"})
    except ValueError as exc:
        assert "GITHUB_TOKEN" in str(exc)
    else:
        raise AssertionError("expected production config validation failure")


def test_redact_secrets():
    config = AppConfig(github_token="secret-token")
    assert redact_secrets("token=secret-token", config) == "token=[REDACTED]"
