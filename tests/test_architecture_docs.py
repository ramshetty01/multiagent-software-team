from __future__ import annotations

from pathlib import Path


def test_diagrams_and_adrs_exist():
    root = Path(__file__).resolve().parents[1]
    assert "sequenceDiagram" in (root / "docs/diagrams.md").read_text()
    assert (root / "docs/adr/0001-task-board.md").exists()
    assert (root / "docs/adr/0002-model-provider.md").exists()
    assert (root / "docs/adr/0003-sandbox-backends.md").exists()

