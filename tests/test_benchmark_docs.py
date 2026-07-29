from __future__ import annotations

import json
from pathlib import Path


def test_benchmark_docs_define_required_protocol():
    text = Path("docs/benchmarks.md").read_text(encoding="utf-8")

    assert "SWE-bench Pro 50-issue subset" in text
    assert "pass@1" in text
    assert "Single-agent baseline" in text
    assert "Reviewer false-approval rate" in text
    assert "Until those artifacts exist" in text


def test_example_eval_result_matches_summary_shape():
    payload = json.loads(Path("examples/eval-result.example.json").read_text(encoding="utf-8"))

    assert payload["results"][0]["issue"] == "django__django-12345"
    assert "multi_agent_pass_at_1" in payload["summary"]
    assert "speedup" in payload["summary"]
