from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from .models import ModelProviderError, ModelRequest, ModelResponse

Transport = Callable[[urllib.request.Request, int], bytes]


class AnthropicProvider:
    def __init__(self, api_key: str, transport: Transport | None = None):
        self.api_key = api_key
        self.transport = transport or self._urlopen

    @staticmethod
    def _urlopen(request: urllib.request.Request, timeout: int) -> bytes:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    def complete(self, request: ModelRequest) -> ModelResponse:
        payload = json.dumps(
            {
                "model": request.model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": request.prompt}],
            }
        ).encode()
        http_request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self.api_key,
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            raw = self.transport(http_request, request.timeout_seconds)
        except urllib.error.HTTPError as exc:
            raise ModelProviderError("anthropic_http_error", exc.read().decode(errors="replace"), exc.code >= 500) from exc
        except OSError as exc:
            raise ModelProviderError("anthropic_network_error", str(exc), True) from exc

        data = json.loads(raw)
        text = "\n".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
        usage: dict[str, Any] = data.get("usage", {})
        return ModelResponse(
            text=text,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            latency_seconds=time.monotonic() - started,
        )

