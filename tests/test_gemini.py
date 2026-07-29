from __future__ import annotations

import json

from mast.gemini import GeminiGenerateContentProvider
from mast.models import ModelRequest


def test_gemini_provider_maps_generate_content_response():
    def transport(request, timeout):
        assert ":generateContent" in request.full_url
        assert request.headers["X-goog-api-key"] == "key"
        return json.dumps(
            {
                "candidates": [{"content": {"parts": [{"text": "classified"}]}}],
                "usageMetadata": {"promptTokenCount": 4, "candidatesTokenCount": 1},
            }
        ).encode()

    response = GeminiGenerateContentProvider("key", transport).complete(ModelRequest("r1", "tester", "gemini-pro", "logs"))

    assert response.text == "classified"
    assert response.output_tokens == 1

