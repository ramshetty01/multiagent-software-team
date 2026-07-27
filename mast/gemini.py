from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from .models import ModelProviderError, ModelRequest, ModelResponse

Transport = Callable[[urllib.request.Request, int], bytes]


class GeminiGenerateContentProvider:
    def __init__(self, api_key: str, transport: Transport | None = None):
        self.api_key = api_key
        self.transport = transport or self._urlopen

    @staticmethod
    def _urlopen(request: urllib.request.Request, timeout: int) -> bytes:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    def complete(self, request: ModelRequest) -> ModelResponse:
        payload = json.dumps({"contents": [{"parts": [{"text": request.prompt}]}]}).encode()
        http_request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent",
            data=payload,
            headers={"x-goog-api-key": self.api_key, "content-type": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        try:
            raw = self.transport(http_request, request.timeout_seconds)
        except urllib.error.HTTPError as exc:
            raise ModelProviderError("gemini_http_error", exc.read().decode(errors="replace"), exc.code >= 500) from exc
        except OSError as exc:
            raise ModelProviderError("gemini_network_error", str(exc), True) from exc

        data = json.loads(raw)
        usage: dict[str, Any] = data.get("usageMetadata", {})
        return ModelResponse(
            text=_candidate_text(data),
            input_tokens=int(usage.get("promptTokenCount", 0)),
            output_tokens=int(usage.get("candidatesTokenCount", 0)),
            latency_seconds=time.monotonic() - started,
        )


def _candidate_text(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                parts.append(str(part["text"]))
    return "\n".join(parts)

