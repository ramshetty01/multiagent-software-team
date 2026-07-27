from __future__ import annotations

from mast.runner import DockerRunner, runner_for_backend


def test_docker_runner_mounts_tester_readonly(tmp_path):
    command = DockerRunner(readonly=True).docker_command(["python", "-V"], tmp_path)

    assert "docker" == command[0]
    assert f"{tmp_path.resolve()}:/workspace:ro" in command


def test_runner_factory_selects_local_and_docker():
    assert runner_for_backend("local")
    assert isinstance(runner_for_backend("docker", tester=True), DockerRunner)

