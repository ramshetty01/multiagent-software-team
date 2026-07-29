from __future__ import annotations

from pathlib import Path


def test_governance_docs_exist():
    root = Path(__file__).resolve().parents[1]
    for path in ["LICENSE", "CONTRIBUTING.md", "SECURITY.md", ".github/pull_request_template.md"]:
        assert (root / path).exists()

