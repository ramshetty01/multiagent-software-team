from __future__ import annotations

from mast.runner import safe_command_env


def test_safe_command_env_removes_common_secret_names():
    env = safe_command_env({"PATH": "/bin", "OPENAI_API_KEY": "x", "GITHUB_TOKEN": "y", "NORMAL": "z"})

    assert env == {"PATH": "/bin", "NORMAL": "z"}
