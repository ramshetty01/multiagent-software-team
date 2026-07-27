from __future__ import annotations

import json

from mast.models import ModelRequest
from mast.openai_provider import OpenAIResponsesProvider


def test_openai_provider_maps_responses_output():
    def transport(request, timeout):
        assert request.full_url == "https://api.openai.com/v1/responses"
        assert request.headers["Authorization"] == "Bearer key"
        return json.dumps({"output_text": "approved", "usage": {"input_tokens": 5, "output_tokens": 1}}).encode()

    response = OpenAIResponsesProvider("key", transport).complete(ModelRequest("r1", "reviewer", "gpt", "diff"))

    assert response.text == "approved"
    assert response.input_tokens == 5

