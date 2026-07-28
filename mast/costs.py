from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


DEFAULT_PRICES_PER_MILLION = {
    "claude-opus": (15.0, 75.0),
    "claude-sonnet": (3.0, 15.0),
    "gpt-5": (1.25, 10.0),
    "gemini-pro": (1.25, 5.0),
}


def call_cost(model: str, input_tokens: int, output_tokens: int, prices=DEFAULT_PRICES_PER_MILLION) -> float:
    input_price, output_price = prices.get(model, (0.0, 0.0))
    return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)


def cost_report(trace_path: str | Path, prices=DEFAULT_PRICES_PER_MILLION) -> dict:
    totals = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
    if not Path(trace_path).exists():
        return {}
    for line in Path(trace_path).read_text().splitlines():
        span = json.loads(line)
        role = span["role"]
        input_tokens = int(span.get("input_tokens", 0))
        output_tokens = int(span.get("output_tokens", 0))
        totals[role]["input_tokens"] += input_tokens
        totals[role]["output_tokens"] += output_tokens
        totals[role]["cost_usd"] += call_cost(span.get("model", ""), input_tokens, output_tokens, prices)
    return dict(totals)

