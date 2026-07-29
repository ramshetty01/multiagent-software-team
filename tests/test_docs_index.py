from __future__ import annotations

from pathlib import Path


def test_readme_links_operator_docs():
    text = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    assert "docs/operator-setup.md" in text
    assert "docs/troubleshooting.md" in text
