from __future__ import annotations

from mast.baseline import run_single_agent_baseline
from mast.models import FakeModelProvider


def test_single_agent_baseline_records_tokens(tmp_path):
    result = run_single_agent_baseline("issue", tmp_path, FakeModelProvider({"baseline": "ok"}), ["python3", "-c", "pass"])
    assert result.baseline_passed is True
    assert result.baseline_tokens > 0

