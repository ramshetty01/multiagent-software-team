from __future__ import annotations

from mast.runner import DaytonaRunner, runner_for_backend


class FakeProcess:
    def exec(self, command, cwd=None, timeout=None):
        self.command = command
        self.cwd = cwd
        self.timeout = timeout
        return type("Response", (), {"exit_code": 0, "result": "ok"})()


class FakeSandbox:
    id = "sandbox-1"

    def __init__(self):
        self.process = FakeProcess()


class FakeDaytona:
    def __init__(self):
        self.created = 0
        self.removed = 0

    def create(self):
        self.created += 1
        return FakeSandbox()

    def remove(self, sandbox):
        self.removed += 1


def test_daytona_runner_reuses_and_closes_sandbox(tmp_path):
    client = FakeDaytona()
    runner = DaytonaRunner(client)

    result = runner.run(["echo", "ok"], tmp_path)
    runner.close()

    assert result.command[:2] == ["daytona", "sandbox-1"]
    assert client.created == 1
    assert client.removed == 1


def test_runner_factory_selects_daytona():
    assert isinstance(runner_for_backend("daytona"), DaytonaRunner)

