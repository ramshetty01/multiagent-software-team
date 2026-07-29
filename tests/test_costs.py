from __future__ import annotations

from mast.costs import call_cost, cost_report
from mast.observability import TraceLog


def test_call_cost_uses_model_pricing():
    assert call_cost("model", 1000, 1000, {"model": (1.0, 2.0)}) == 0.003


def test_cost_report_groups_by_role(tmp_path):
    trace = TraceLog(tmp_path / "trace.jsonl")
    trace.record(run_id="r1", role="coder", model="model", payload_size=1, input_tokens=1000, output_tokens=1000)

    report = cost_report(tmp_path / "trace.jsonl", {"model": (1.0, 2.0)})

    assert report["coder"]["cost_usd"] == 0.003

