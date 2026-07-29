from __future__ import annotations

import time
from pathlib import Path

from .eval import EvalResult
from .models import ModelProvider, ModelRequest, complete_with_retry
from .runner import LocalRunner


def run_single_agent_baseline(
    issue: str,
    repo: str | Path,
    provider: ModelProvider,
    test_command: list[str],
    model: str = "claude-sonnet",
) -> EvalResult:
    started = time.monotonic()
    response = complete_with_retry(provider, ModelRequest("baseline", "baseline", model, f"Solve this issue in one worktree:\n{issue}"))
    test = LocalRunner().run(test_command, repo)
    return EvalResult(
        issue=issue,
        multi_agent_passed=False,
        baseline_passed=test.returncode == 0,
        multi_agent_seconds=0.0,
        baseline_seconds=time.monotonic() - started,
        multi_agent_tokens=0,
        baseline_tokens=response.input_tokens + response.output_tokens,
    )

