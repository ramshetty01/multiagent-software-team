from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import InterfaceContract, Subtask, validate_dag


def architect_prompt(title: str, body: str) -> str:
    return (
        "Decompose this GitHub issue into a JSON object with a `subtasks` array. "
        "Each subtask must include id, title, depends_on, and contract with files, "
        "public_functions, and test_impact.\n\n"
        f"Title: {title}\n\nBody:\n{body}"
    )


def coder_prompt(subtask: dict[str, Any], files: dict[str, str]) -> str:
    return (
        "Implement exactly this subtask and return a unified diff only. "
        "Do not edit files outside the contract.\n\n"
        f"Subtask:\n{json.dumps(subtask, indent=2, sort_keys=True)}\n\n"
        f"Files:\n{json.dumps(files, indent=2, sort_keys=True)}"
    )


def parse_architect_json(text: str) -> list[Subtask]:
    data = json.loads(text)
    tasks = []
    for item in data.get("subtasks", []):
        contract = item["contract"]
        tasks.append(
            Subtask(
                id=item["id"],
                title=item["title"],
                depends_on=list(item.get("depends_on", [])),
                contract=InterfaceContract(
                    files=list(contract["files"]),
                    public_functions=list(contract.get("public_functions", [])),
                    test_impact=list(contract.get("test_impact", [])),
                ),
            )
        )
    validate_dag(tasks)
    return tasks


def read_declared_files(repo: str | Path, files: list[str]) -> dict[str, str]:
    root = Path(repo)
    result = {}
    for name in files:
        path = root / name
        if path.exists() and path.is_file():
            result[name] = path.read_text(errors="replace")
    return result

