from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mast.gitops import commit_all, git


def repository(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.org"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("before\n")
    commit_all(tmp_path, "initial")
    return tmp_path


def marker_script(path: Path, marker: Path) -> None:
    path.write_text(f"#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n")
    path.chmod(0o755)


def test_host_commit_does_not_execute_repository_hook(tmp_path):
    repo = repository(tmp_path)
    marker = repo / "hook-ran"
    marker_script(repo / ".git/hooks/pre-commit", marker)
    (repo / "file.txt").write_text("after\n")
    assert commit_all(repo, "change")
    assert not marker.exists()


def test_review_diff_does_not_execute_external_helpers(tmp_path):
    repo = repository(tmp_path)
    marker = repo / "diff-ran"
    helper = repo / ".git/diff-helper"
    marker_script(helper, marker)
    subprocess.run(["git", "config", "diff.external", str(helper)], cwd=repo, check=True)
    (repo / "file.txt").write_text("after\n")
    assert "+after" in git(repo, "diff")
    assert not marker.exists()


def test_git_environment_strips_secrets_and_disables_prompt(monkeypatch, tmp_path):
    from types import SimpleNamespace

    captured = {}
    def run(command, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(stdout="ok")
    monkeypatch.setenv("PROVIDER_API_KEY", "test-secret")
    monkeypatch.setattr("mast.gitops.subprocess.run", run)
    git(tmp_path, "status")
    assert "PROVIDER_API_KEY" not in captured["env"]
    assert captured["env"]["GIT_TERMINAL_PROMPT"] == "0"


def test_status_does_not_execute_fsmonitor_helper(tmp_path):
    repo = repository(tmp_path)
    marker = repo / "monitor-ran"
    helper = repo / ".git/monitor-helper"
    marker_script(helper, marker)
    subprocess.run(["git", "config", "core.fsmonitor", str(helper)], cwd=repo, check=True)
    git(repo, "status", "--porcelain")
    assert not marker.exists()


def test_review_diff_does_not_execute_text_conversion(tmp_path):
    repo = repository(tmp_path)
    marker = repo / "textconv-ran"
    helper = repo / ".git/textconv-helper"
    marker_script(helper, marker)
    (repo / ".gitattributes").write_text("*.txt diff=render\n")
    subprocess.run(["git", "config", "diff.render.textconv", str(helper)], cwd=repo, check=True)
    commit_all(repo, "attributes")
    (repo / "file.txt").write_text("after\n")
    assert "+after" in git(repo, "diff")
    assert not marker.exists()
