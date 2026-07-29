from __future__ import annotations

from mast.messages import Message
from mast.validation import validate_subtask_payload


def test_subtask_payload_validation_rejects_missing_files():
    try:
        validate_subtask_payload({"title": "x", "contract": {}})
    except ValueError as exc:
        assert "files" in str(exc)
    else:
        raise AssertionError("expected validation failure")


def test_message_validation_runs_for_subtasks():
    try:
        Message(type="subtask", run_id="r1", role="architect", payload={"title": "x", "contract": {}}).to_dict()
    except ValueError:
        pass
    else:
        raise AssertionError("expected message validation failure")

