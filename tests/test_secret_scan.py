from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scan_secrets", ROOT / "scripts/scan_secrets.py")
assert SPEC and SPEC.loader
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)


def test_scanner_ignores_task_names_and_its_own_patterns():
    assert scanner.finding_lines("task-board task-a desk-token") == []
    assert scanner.finding_lines((ROOT / "scripts/scan_secrets.py").read_text()) == []


def test_scanner_detects_token_shapes_without_short_placeholders():
    tokens = ["gh" + "p_" + "x" * 36, "s" + "k-proj-" + "x" * 32, "github_" + "pat_" + "x" * 40]
    assert scanner.finding_lines("\n".join(tokens)) == [1, 2, 3]
    assert scanner.finding_lines("s" + "k-placeholder") == []


def test_scan_reports_only_tracked_files_and_line_numbers(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    secret = "gh" + "o_" + "a" * 36
    (tmp_path / "tracked.txt").write_text("ordinary\n" + secret)
    (tmp_path / "ignored.txt").write_text(secret)
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    assert scanner.scan(tmp_path) == [("tracked.txt", 2)]
    assert secret not in repr(scanner.scan(tmp_path))
