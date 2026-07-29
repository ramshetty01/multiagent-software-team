from __future__ import annotations

from pathlib import Path


def test_ci_workflow_runs_self_check():
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"
    text = workflow.read_text()
    assert "scripts/self_check.py" in text
    assert "Secret scan" in text
    assert "ruff check" in text
    assert "mypy mast" in text
    assert "github/codeql-action" in text
