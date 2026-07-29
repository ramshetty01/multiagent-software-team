from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class EvalResult:
    issue: str
    multi_agent_passed: bool
    baseline_passed: bool
    multi_agent_seconds: float
    baseline_seconds: float
    multi_agent_tokens: int
    baseline_tokens: int


def summarize(results: list[EvalResult]) -> dict[str, float]:
    solved = sum(result.multi_agent_passed for result in results)
    baseline = sum(result.baseline_passed for result in results)
    total = len(results) or 1
    multi_time = sum(result.multi_agent_seconds for result in results)
    base_time = sum(result.baseline_seconds for result in results)
    return {
        "multi_agent_pass_at_1": solved / total,
        "baseline_pass_at_1": baseline / total,
        "speedup": (base_time / multi_time) if multi_time else 0.0,
        "multi_agent_tokens": sum(result.multi_agent_tokens for result in results),
        "baseline_tokens": sum(result.baseline_tokens for result in results),
    }


def write_eval(path: str | Path, results: list[EvalResult]) -> None:
    payload = {"results": [asdict(result) for result in results], "summary": summarize(results)}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_issue_list(path: str | Path) -> list[str]:
    issues = [line.strip() for line in Path(path).read_text().splitlines() if line.strip() and not line.startswith("#")]
    if len(issues) != 50:
        raise ValueError("SWE-bench Pro evaluation requires exactly 50 issues")
    validate_issue_ids(issues)
    return issues


def validate_issue_ids(issues: list[str]) -> None:
    placeholders = [issue for issue in issues if issue.startswith("issue-")]
    if placeholders:
        raise ValueError("replace placeholder SWE-bench issue IDs before scoring")


def run_eval(issues: list[str], runner: Callable[[str], EvalResult], out: str | Path) -> dict[str, float]:
    results = [runner(issue) for issue in issues]
    write_eval(out, results)
    return summarize(results)
