from __future__ import annotations

from mast.runner import DockerRunner, runner_for_backend


def test_docker_runner_mounts_tester_readonly(tmp_path):
    command = DockerRunner(readonly=True).docker_command(["python", "-V"], tmp_path)

    assert "docker" == command[0]
    assert f"{tmp_path.resolve()}:/workspace:ro" in command


def test_runner_factory_selects_local_and_docker():
    assert runner_for_backend("local")
    assert isinstance(runner_for_backend("docker", tester=True), DockerRunner)



def test_timeout_removes_named_container_and_decodes_output(tmp_path, monkeypatch):
    import subprocess
    from types import SimpleNamespace

    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if command[1] == "run":
            raise subprocess.TimeoutExpired(command, 1, output=b"partial output", stderr=b"timed out")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("mast.runner.subprocess.run", run)
    result = DockerRunner(timeout_seconds=1).run(["python", "-V"], tmp_path)
    name = calls[0][calls[0].index("--name") + 1]
    assert calls[1] == ["docker", "rm", "-f", name]
    assert result.returncode == 124
    assert result.stdout == "partial output"
    assert result.stderr == "timed out"
