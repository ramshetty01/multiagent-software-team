from __future__ import annotations

import json

from mast.anthropic import AnthropicProvider
from mast.models import ModelRequest


def test_anthropic_provider_maps_messages_response():
    def transport(request, timeout):
        assert request.headers["X-api-key"] == "key"
        return json.dumps(
            {
                "content": [{"type": "text", "text": "hello"}],
                "usage": {"input_tokens": 3, "output_tokens": 1},
            }
        ).encode()

    response = AnthropicProvider("key", transport).complete(ModelRequest("r1", "architect", "claude", "prompt"))

    assert response.text == "hello"
    assert response.input_tokens == 3

