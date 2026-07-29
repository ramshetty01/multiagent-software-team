from __future__ import annotations

import json

from mast.conflicts import resolve_conflicts
from mast.models import FakeModelProvider


def test_resolve_conflicts_writes_only_conflicted_files(tmp_path):
    (tmp_path / "a.txt").write_text("<<<<<<< HEAD\nold\n=======\nnew\n>>>>>>> branch\n")
    provider = FakeModelProvider({"merge": json.dumps({"files": {"a.txt": "resolved\n"}})})

    message = resolve_conflicts("r1", tmp_path, ["a.txt"], provider, ["python3", "-c", "open('a.txt').read()"])

    assert message.type == "approved"
    assert (tmp_path / "a.txt").read_text() == "resolved\n"

