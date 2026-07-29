from __future__ import annotations

from .anthropic import AnthropicProvider
from .config import AppConfig
from .gemini import GeminiGenerateContentProvider
from .models import FakeModelProvider, ModelProvider
from .openai_provider import OpenAIResponsesProvider


def provider_for_role(config: AppConfig, role: str) -> ModelProvider:
    if config.environment == "local":
        return FakeModelProvider({"*": "approved"})
    if role in {"architect", "coder"}:
        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        return AnthropicProvider(config.anthropic_api_key)
    if role == "reviewer":
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        return OpenAIResponsesProvider(config.openai_api_key)
    if role == "tester":
        if not config.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        return GeminiGenerateContentProvider(config.google_api_key)
    raise ValueError(f"unknown provider role: {role}")

