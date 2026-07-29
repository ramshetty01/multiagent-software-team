from __future__ import annotations


def likely_owner(stderr: str, ownership: dict[str, str]) -> tuple[str | None, float]:
    for path, subtask_id in ownership.items():
        if path in stderr:
            return subtask_id, 0.8
    return None, 0.0


def classify_retries(returncodes: list[int]) -> str:
    if not returncodes:
        return "unknown"
    if 0 in returncodes and any(code != 0 for code in returncodes):
        return "flaky_test"
    if all(code == 0 for code in returncodes):
        return "passed"
    return "code_regression"

