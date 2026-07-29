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


def reviewer_prompt(diff: str, ownership: dict[str, str] | None = None) -> str:
    return (
        "Review only this merged diff. Return JSON: "
        '{"decision":"approved"} or '
        '{"decision":"request_changes","requests":[{"path":"...","line":0,'
        '"severity":"low|medium|high","message":"...","subtask_id":"..."}]}.\n\n'
        f"Ownership:\n{json.dumps(ownership or {}, indent=2, sort_keys=True)}\n\n"
        f"Diff:\n{diff}"
    )


def parse_review_json(text: str) -> dict[str, Any]:
    data = json.loads(text)
    decision = data.get("decision")
    if decision not in {"approved", "request_changes"}:
        raise ValueError("review decision must be approved or request_changes")
    if decision == "request_changes" and not isinstance(data.get("requests"), list):
        raise ValueError("review change requests are required")
    return data


def tester_prompt(stdout: str, stderr: str, diff: str, ownership: dict[str, str]) -> str:
    return (
        "Classify this test failure. Return JSON with `classification` as one of "
        "code_regression, flaky_test, environment_error, unknown, plus `subtask_id`, "
        "`confidence`, and `evidence`. Do not suggest code edits.\n\n"
        f"Ownership:\n{json.dumps(ownership, indent=2, sort_keys=True)}\n\n"
        f"Diff:\n{diff}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
    )


def parse_test_failure_json(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if data.get("classification") not in {"code_regression", "flaky_test", "environment_error", "unknown"}:
        raise ValueError("invalid test failure classification")
    return data


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
