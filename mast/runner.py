from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


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
    raise ValueError(f"unsupported runner backend: {backend}")
