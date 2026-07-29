from __future__ import annotations

from typing import Any


def require_keys(payload: dict[str, Any], keys: list[str], context: str) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise ValueError(f"{context} missing required keys: {', '.join(missing)}")


def validate_subtask_payload(payload: dict[str, Any]) -> None:
    require_keys(payload, ["title", "contract"], "subtask")
    contract = payload["contract"]
    if not isinstance(contract, dict):
        raise ValueError("subtask contract must be an object")
    require_keys(contract, ["files"], "subtask contract")
    if not isinstance(contract["files"], list) or not all(isinstance(item, str) for item in contract["files"]):
        raise ValueError("subtask contract files must be list[str]")


def validate_review_feedback(payload: dict[str, Any]) -> None:
    require_keys(payload, ["requests"], "review_feedback")
    if not isinstance(payload["requests"], list):
        raise ValueError("review_feedback requests must be a list")

