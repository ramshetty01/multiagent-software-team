from __future__ import annotations

from mast.eval import EvalResult, RunOutcome, load_issue_list, run_eval, run_paired_eval


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


def test_run_paired_eval_writes_multi_agent_and_baseline(tmp_path):
    summary = run_paired_eval(
        ["dry-1", "dry-2"],
        lambda issue: RunOutcome(issue == "dry-1", 1.0, 10),
        lambda issue: RunOutcome(False, 2.0, 20),
        tmp_path / "paired.json",
    )

    assert summary["multi_agent_pass_at_1"] == 0.5
    assert summary["baseline_pass_at_1"] == 0.0
