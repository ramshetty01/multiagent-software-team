from __future__ import annotations

from pathlib import Path


def test_operations_and_threat_model_docs_exist():
    operations = Path("docs/operations.md").read_text(encoding="utf-8")
    threat_model = Path("docs/threat-model.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    security = Path("SECURITY.md").read_text(encoding="utf-8")

    assert "Failure Recovery" in operations
    assert "Cost Controls" in operations
    assert "Prompt Injection" in threat_model
    assert "Untrusted Code Execution" in threat_model
    assert "Incident Response" in threat_model
    assert "docs/threat-model.md" in readme
    assert "docs/threat-model.md" in security
