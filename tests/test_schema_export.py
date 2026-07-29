from __future__ import annotations

from mast.schema_export import export_schema


def test_export_schema_lists_message_types():
    schema = export_schema()
    assert "subtask" in schema["message_types"]
    assert "files" in schema["subtask_contract"]

