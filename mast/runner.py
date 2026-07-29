from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .security import validate_command


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float


class LocalRunner:
    def run(self, command: list[str], cwd: str | Path) -> CommandResult:
        validate_command(command)
        started = time.monotonic()
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=time.monotonic() - started,
        )


class Runner(Protocol):
    def run(self, command: list[str], cwd: str | Path) -> CommandResult:
        ...


class DockerRunner:
    def __init__(self, image: str = "python:3.12-slim", readonly: bool = False, timeout_seconds: int = 900, memory: str = "2g", cpus: str = "2"):
        self.image = image
        self.readonly = readonly
        self.timeout_seconds = timeout_seconds
        self.memory = memory
        self.cpus = cpus

    def docker_command(self, command: list[str], cwd: str | Path) -> list[str]:
        validate_command(command)
        mount_mode = "ro" if self.readonly else "rw"
        return [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            self.memory,
            "--cpus",
            self.cpus,
            "-v",
            f"{Path(cwd).resolve()}:/workspace:{mount_mode}",
            "-w",
            "/workspace",
            self.image,
            *command,
        ]

    def run(self, command: list[str], cwd: str | Path) -> CommandResult:
        docker = self.docker_command(command, cwd)
        started = time.monotonic()
        try:
            result = subprocess.run(docker, text=True, capture_output=True, timeout=self.timeout_seconds)
            return CommandResult(docker, str(cwd), result.returncode, result.stdout, result.stderr, time.monotonic() - started)
        except subprocess.TimeoutExpired as exc:
            return CommandResult(docker, str(cwd), 124, exc.stdout or "", exc.stderr or "command timed out", time.monotonic() - started)


def runner_for_backend(backend: str, *, tester: bool = False) -> Runner:
    if backend == "local":
        return LocalRunner()
    if backend == "docker":
        return DockerRunner(readonly=tester)
    if backend == "daytona":
        return DaytonaRunner()
    raise ValueError(f"unsupported runner backend: {backend}")


class DaytonaRunner:
    def __init__(self, daytona_client=None, timeout_seconds: int = 900):
        self.daytona_client = daytona_client
        self.timeout_seconds = timeout_seconds
        self.sandbox = None

    def _client(self):
        if self.daytona_client:
            return self.daytona_client
        try:
            from daytona import Daytona
        except ImportError as exc:
            raise RuntimeError("install daytona to use the Daytona sandbox backend") from exc
        self.daytona_client = Daytona()
        return self.daytona_client

    def ensure_sandbox(self):
        if self.sandbox is None:
            self.sandbox = self._client().create()
        return self.sandbox

    def close(self) -> None:
        if self.sandbox is not None and hasattr(self._client(), "remove"):
            self._client().remove(self.sandbox)
            self.sandbox = None

    def run(self, command: list[str], cwd: str | Path) -> CommandResult:
        validate_command(command)
        sandbox = self.ensure_sandbox()
        sandbox_id = str(getattr(sandbox, "id", getattr(sandbox, "sandbox_id", "unknown")))
        started = time.monotonic()
        response = sandbox.process.exec(" ".join(command), cwd=str(cwd), timeout=self.timeout_seconds)
        exit_code = int(getattr(response, "exit_code", 0))
        stdout = str(getattr(response, "result", ""))
        artifacts = getattr(response, "artifacts", None)
        if artifacts and getattr(artifacts, "stdout", None):
            stdout = str(artifacts.stdout)
        return CommandResult(["daytona", sandbox_id, *command], str(cwd), exit_code, stdout, "", time.monotonic() - started)
