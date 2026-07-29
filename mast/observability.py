from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class Span:
    trace_id: str
    run_id: str
    role: str
    model: str
    payload_size: int
    input_tokens: int = 0
    output_tokens: int = 0
    subtask_id: str | None = None


class TraceLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, **kwargs) -> Span:
        span = Span(trace_id=str(uuid4()), **kwargs)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(span), sort_keys=True) + "\n")
        return span

    def metrics(self) -> dict[str, dict[str, int]]:
        totals: dict[str, dict[str, int]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0})
        if not self.path.exists():
            return {}
        for line in self.path.read_text().splitlines():
            span = json.loads(line)
            role = span["role"]
            totals[role]["input_tokens"] += int(span.get("input_tokens", 0))
            totals[role]["output_tokens"] += int(span.get("output_tokens", 0))
        return dict(totals)


class LangfuseTraceLog(TraceLog):
    def __init__(self, path: str | Path, client=None):
        super().__init__(path)
        self.client = client

    def record(self, **kwargs) -> Span:
        span = super().record(**kwargs)
        if self.client:
            try:
                self.client.trace(id=span.trace_id, name=span.role, metadata=asdict(span))
            except Exception:
                pass
        return span


def trace_log_for_backend(backend: str, path: str | Path, client=None) -> TraceLog:
    if backend == "jsonl":
        return TraceLog(path)
    if backend == "langfuse":
        return LangfuseTraceLog(path, client)
    raise ValueError(f"unsupported tracing backend: {backend}")


def token_amplification(coder_tokens: int, extra_tokens: int) -> float:
    if coder_tokens <= 0:
        return 0.0
    return (coder_tokens + extra_tokens) / coder_tokens
