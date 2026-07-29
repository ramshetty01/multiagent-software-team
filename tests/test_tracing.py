from __future__ import annotations

from mast.observability import LangfuseTraceLog, trace_log_for_backend


class FakeLangfuse:
    def __init__(self):
        self.calls = []

    def trace(self, **kwargs):
        self.calls.append(kwargs)


def test_langfuse_trace_log_writes_fallback_and_client(tmp_path):
    client = FakeLangfuse()
    log = LangfuseTraceLog(tmp_path / "trace.jsonl", client)

    span = log.record(run_id="r1", role="coder", model="m", payload_size=1)

    assert span.trace_id
    assert client.calls[0]["name"] == "coder"
    assert (tmp_path / "trace.jsonl").exists()


def test_trace_log_factory_selects_backends(tmp_path):
    assert trace_log_for_backend("jsonl", tmp_path / "a.jsonl")
    assert isinstance(trace_log_for_backend("langfuse", tmp_path / "b.jsonl"), LangfuseTraceLog)

