from __future__ import annotations

from mast.preflight import Check, preflight_ok, run_preflight


def test_preflight_ok_requires_all_checks():
    assert preflight_ok([Check("a", True, "ok")]) is True
    assert preflight_ok([Check("a", False, "bad")]) is False


def test_run_preflight_returns_named_checks():
    checks = run_preflight(repo=".")
    names = {check.name for check in checks}
    assert "config" in names
    assert "git_repo" in names

