from __future__ import annotations

from mast.failures import classify_retries, likely_owner


def test_classify_retries_detects_flake():
    assert classify_retries([1, 0]) == "flaky_test"
    assert classify_retries([1, 1]) == "code_regression"


def test_likely_owner_uses_trace_paths():
    assert likely_owner("File a.py failed", {"a.py": "s1"}) == ("s1", 0.8)

