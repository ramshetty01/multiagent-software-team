from __future__ import annotations

import json

from mast.models import FakeModelProvider
from mast.prompts import parse_test_failure_json
from mast.runner import CommandResult
from mast.tester import Tester, resolve_test_command


class FailingRunner:
    def run(self, command, cwd):
        return CommandResult(command, str(cwd), 1, "", "AssertionError", 0.1)


def test_tester_classifies_failure_without_editing(tmp_path):
    provider = FakeModelProvider({"tester": json.dumps({"classification": "code_regression", "subtask_id": "a", "confidence": 0.9, "evidence": "AssertionError"})})

    message = Tester(FailingRunner(), provider).test("r1", tmp_path, ["test"], ownership={"a.py": "a"})

    assert message.type == "test_failed"
    assert message.payload["classification"]["subtask_id"] == "a"


def test_parse_test_failure_json_rejects_unknown_label():
    try:
        parse_test_failure_json(json.dumps({"classification": "bad"}))
    except ValueError:
        pass
    else:
        raise AssertionError("expected validation failure")


def test_resolve_test_command_uses_project_metadata(tmp_path):
    repo = tmp_path / "test-command-repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    assert resolve_test_command(repo) == ["python3", "-m", "pytest"]


def test_resolve_test_command_rejects_noop_in_production(tmp_path):
    try:
        resolve_test_command(tmp_path, ["python3", "-c", "pass"], production=True)
    except ValueError as exc:
        assert "no-op" in str(exc)
    else:
        raise AssertionError("expected production no-op rejection")
