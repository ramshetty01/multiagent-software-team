from __future__ import annotations

from mast.config import AppConfig
from mast.security import SecurityError, redact_artifact, validate_command, validate_repo


def test_validate_command_blocks_obvious_danger():
    try:
        validate_command(["rm", "-rf", "."])
    except SecurityError:
        pass
    else:
        raise AssertionError("expected command block")


def test_validate_repo_allowlist(tmp_path):
    validate_repo(tmp_path, [str(tmp_path.parent)])
    try:
        validate_repo(tmp_path, [str(tmp_path / "other")])
    except SecurityError:
        pass
    else:
        raise AssertionError("expected repo block")


def test_redact_artifact_hides_config_secrets():
    assert redact_artifact("x=token", AppConfig(github_token="token")) == "x=[REDACTED]"

