from __future__ import annotations

from collections import Counter
from pathlib import Path


FAILURE_TYPES = {"plan_too_vague", "merge_conflict", "reviewer_false_approve", "tester_flake", "other"}


def handoff_histogram(labels: list[str]) -> dict[str, int]:
    counts = Counter(label if label in FAILURE_TYPES else "other" for label in labels)
    return {key: counts.get(key, 0) for key in sorted(FAILURE_TYPES)}


def write_postmortem(path: str | Path, failures: list[str], speedup: float, token_cost: float) -> None:
    histogram = handoff_histogram(failures)
    lines = [
        "# Run Post-Mortem",
        "",
        f"- Parallel speedup: {speedup:.2f}x",
        f"- Token cost per solved issue: ${token_cost:.2f}",
        "",
        "## Handoff-Failure Histogram",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in histogram.items())
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n")

