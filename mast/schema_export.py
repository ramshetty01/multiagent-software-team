from __future__ import annotations

from .messages import MESSAGE_TYPES


def export_schema() -> dict[str, object]:
    return {
        "message_types": sorted(MESSAGE_TYPES),
        "subtask_contract": {
            "files": "list[str]",
            "public_functions": "list[str]",
            "test_impact": "list[str]",
            "allow_generated_lockfiles": "bool optional",
        },
        "required_message_fields": ["type", "run_id", "role", "payload"],
    }

