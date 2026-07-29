from __future__ import annotations

from mast.eval import EvalResult, load_issue_list, run_eval


def test_load_issue_list_requires_50(tmp_path):
    path = tmp_path / "issues.txt"
    path.write_text("\n".join(f"i-{i}" for i in range(50)))
    assert len(load_issue_list(path)) == 50


def test_run_eval_writes_summary(tmp_path):
    summary = run_eval(
        ["i-1"],
        lambda issue: EvalResult(issue, True, False, 1.0, 2.0, 10, 20),
        tmp_path / "eval.json",
    )
    assert summary["multi_agent_pass_at_1"] == 1.0

