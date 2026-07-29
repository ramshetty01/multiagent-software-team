from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol


class ModelProviderError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = True):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def to_payload(self) -> dict[str, object]:
        return {"code": self.code, "message": self.message, "retryable": self.retryable}


@dataclass(frozen=True)
class ModelRequest:
    run_id: str
    role: str
    model: str
    prompt: str
    files: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 120
    prompt_name: str | None = None
    prompt_version: str | None = None


@dataclass(frozen=True)
class ModelResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    cost_usd: float = 0.0


class ModelProvider(Protocol):
    def complete(self, request: ModelRequest) -> ModelResponse:
        ...


class FakeModelProvider:
    def __init__(self, responses: dict[str, str] | None = None, fail: bool = False):
        self.responses = responses or {}
        self.fail = fail
        self.calls: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> ModelResponse:
        self.calls.append(request)
        if self.fail:
            raise ModelProviderError("model_provider_failed", "fake provider failure")
        started = time.monotonic()
        text = self.responses.get(request.role, self.responses.get("*", "approved"))
        return ModelResponse(
            text=text,
            input_tokens=max(1, len(request.prompt.split())),
            output_tokens=max(1, len(text.split())),
            latency_seconds=time.monotonic() - started,
        )


def complete_with_retry(provider: ModelProvider, request: ModelRequest, attempts: int = 2) -> ModelResponse:
    last_error: ModelProviderError | None = None
    for _ in range(max(1, attempts)):
        try:
            return provider.complete(request)
        except ModelProviderError as exc:
            last_error = exc
            if not exc.retryable:
                break
    assert last_error is not None
    raise last_error
