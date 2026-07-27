from __future__ import annotations

from mast.scope import out_of_scope


def test_scope_accepts_exact_globs_and_directories():
    assert out_of_scope(["src/a.py", "tests/test_a.py", "docs/guide/setup.md"], ["src/*.py", "tests/test_a.py", "docs/guide"]) == []


def test_scope_allows_generated_lockfiles_only_when_configured():
    assert out_of_scope(["package-lock.json"], ["src/*.py"]) == ["package-lock.json"]
    assert out_of_scope(["package-lock.json"], ["src/*.py"], generated_lockfiles=True) == []

