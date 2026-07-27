from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from .models import ModelProviderError, ModelRequest, ModelResponse

Transport = Callable[[urllib.request.Request, int], bytes]


class OpenAIResponsesProvider:
    def __init__(self, api_key: str, transport: Transport | None = None):
        self.api_key = api_key
        self.transport = transport or self._urlopen

    @staticmethod
    def _urlopen(request: urllib.request.Request, timeout: int) -> bytes:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    def complete(self, request: ModelRequest) -> ModelResponse:
        payload = json.dumps({"model": request.model, "input": request.prompt, "store": False}).encode()
        http_request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={"authorization": f"Bearer {self.api_key}", "content-type": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        try:
            raw = self.transport(http_request, request.timeout_seconds)
        except urllib.error.HTTPError as exc:
            raise ModelProviderError("openai_http_error", exc.read().decode(errors="replace"), exc.code >= 500) from exc
        except OSError as exc:
            raise ModelProviderError("openai_network_error", str(exc), True) from exc

        data = json.loads(raw)
        usage: dict[str, Any] = data.get("usage", {})
        return ModelResponse(
            text=_output_text(data),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            latency_seconds=time.monotonic() - started,
        )


def _output_text(data: dict[str, Any]) -> str:
    if data.get("output_text"):
        return str(data["output_text"])
    parts: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(str(content.get("text", "")))
    return "\n".join(part for part in parts if part)

