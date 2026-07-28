from __future__ import annotations

from mast.reporting import final_report, write_final_report


def test_final_report_combines_metrics(tmp_path):
    report = final_report({"pass": 1}, {"coder": {"cost": 2}}, ["merge_conflict"])
    path = tmp_path / "report.md"
    write_final_report(path, report)
    assert "merge_conflict" in path.read_text()

