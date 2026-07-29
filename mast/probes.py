from __future__ import annotations

from dataclasses import dataclass

from .reviewer import Reviewer


@dataclass(frozen=True)
class ProbeResult:
    name: str
    approved: bool


def injected_bug_probe(reviewer: Reviewer, run_id: str, diff: str, name: str = "injected-bug") -> ProbeResult:
    message = reviewer.review(run_id, "coder", "reviewer", diff)
    return ProbeResult(name=name, approved=message.type == "approved")


def false_approval_rate(results: list[ProbeResult]) -> float:
    if not results:
        return 0.0
    return sum(result.approved for result in results) / len(results)

