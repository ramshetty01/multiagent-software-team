from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Status = Literal["planned", "claimed", "done", "blocked"]
ALLOWED_STATUS: dict[str, set[str]] = {
    "planned": {"claimed", "blocked"},
    "claimed": {"done", "blocked"},
    "done": set(),
    "blocked": {"planned"},
}


@dataclass
class InterfaceContract:
    files: list[str]
    public_functions: list[str] = field(default_factory=list)
    test_impact: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.files:
            raise ValueError("contract files are required")


@dataclass
class Subtask:
    id: str
    title: str
    contract: InterfaceContract
    depends_on: list[str] = field(default_factory=list)
    status: Status = "planned"
    owner: str | None = None

    def transition(self, status: Status) -> None:
        if status not in ALLOWED_STATUS[self.status]:
            raise ValueError(f"invalid transition: {self.status} -> {status}")
        self.status = status

    def validate(self) -> None:
        if self.id in self.depends_on:
            raise ValueError("subtask cannot depend on itself")
        self.contract.validate()


def validate_dag(subtasks: list[Subtask]) -> None:
    by_id = {task.id: task for task in subtasks}
    if len(by_id) != len(subtasks):
        raise ValueError("duplicate subtask id")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            raise ValueError("subtask cycle detected")
        if task_id not in by_id:
            raise ValueError(f"unknown dependency: {task_id}")
        visiting.add(task_id)
        for dep in by_id[task_id].depends_on:
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task in subtasks:
        task.validate()
        visit(task.id)

