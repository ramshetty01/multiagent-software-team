from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SECRET_NAMES = ("API_KEY", "TOKEN", "SECRET", "PASSWORD")


@dataclass(frozen=True)
class ModelConfig:
    architect: str = "claude-opus"
    coder: str = "claude-sonnet"
    reviewer: str = "gpt-5"
    tester: str = "gemini-pro"


@dataclass(frozen=True)
class RuntimeLimits:
    role_timeout_seconds: int = 900
    retry_count: int = 2
    max_review_loops: int = 3
    max_tester_reruns: int = 1
    max_conflict_files: int = 2
    max_role_tokens: int = 200_000

    def validate(self) -> None:
        values = self.__dict__
        invalid = [name for name, value in values.items() if int(value) <= 0]
        if invalid:
            raise ValueError(f"runtime limits must be positive: {', '.join(invalid)}")


@dataclass(frozen=True)
class AppConfig:
    environment: str = "local"
    github_token: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    sandbox_backend: str = "local"
    tracing_backend: str = "jsonl"
    models: ModelConfig = ModelConfig()
    limits: RuntimeLimits = RuntimeLimits()

    def validate(self) -> None:
        self.limits.validate()
        if self.environment == "production":
            missing = [
                name
                for name, value in {
                    "GITHUB_TOKEN": self.github_token,
                    "ANTHROPIC_API_KEY": self.anthropic_api_key,
                    "OPENAI_API_KEY": self.openai_api_key,
                    "GOOGLE_API_KEY": self.google_api_key,
                }.items()
                if not value
            ]
            if missing:
                raise ValueError(f"missing required production config: {', '.join(missing)}")
        if self.sandbox_backend not in {"local", "docker", "daytona"}:
            raise ValueError("sandbox_backend must be local, docker, or daytona")
        if self.tracing_backend not in {"jsonl", "langfuse"}:
            raise ValueError("tracing_backend must be jsonl or langfuse")


def load_config(path: str | Path | None = None, env: dict[str, str] | None = None) -> AppConfig:
    values: dict[str, Any] = {}
    if path:
        candidate = Path(path)
        if candidate.exists():
            values.update(json.loads(candidate.read_text()))
    source = env or os.environ
    models = values.get("models", {})
    limits = values.get("limits", {})
    config = AppConfig(
        environment=source.get("MAST_ENV", values.get("environment", "local")),
        github_token=source.get("GITHUB_TOKEN", values.get("github_token")),
        anthropic_api_key=source.get("ANTHROPIC_API_KEY", values.get("anthropic_api_key")),
        openai_api_key=source.get("OPENAI_API_KEY", values.get("openai_api_key")),
        google_api_key=source.get("GOOGLE_API_KEY", values.get("google_api_key")),
        langfuse_public_key=source.get("LANGFUSE_PUBLIC_KEY", values.get("langfuse_public_key")),
        langfuse_secret_key=source.get("LANGFUSE_SECRET_KEY", values.get("langfuse_secret_key")),
        sandbox_backend=source.get("MAST_SANDBOX_BACKEND", values.get("sandbox_backend", "local")),
        tracing_backend=source.get("MAST_TRACING_BACKEND", values.get("tracing_backend", "jsonl")),
        models=ModelConfig(
            architect=source.get("MAST_ARCHITECT_MODEL", models.get("architect", "claude-opus")),
            coder=source.get("MAST_CODER_MODEL", models.get("coder", "claude-sonnet")),
            reviewer=source.get("MAST_REVIEWER_MODEL", models.get("reviewer", "gpt-5")),
            tester=source.get("MAST_TESTER_MODEL", models.get("tester", "gemini-pro")),
        ),
        limits=RuntimeLimits(
            role_timeout_seconds=int(source.get("MAST_ROLE_TIMEOUT_SECONDS", limits.get("role_timeout_seconds", 900))),
            retry_count=int(source.get("MAST_RETRY_COUNT", limits.get("retry_count", 2))),
            max_review_loops=int(source.get("MAST_MAX_REVIEW_LOOPS", limits.get("max_review_loops", 3))),
            max_tester_reruns=int(source.get("MAST_MAX_TESTER_RERUNS", limits.get("max_tester_reruns", 1))),
            max_conflict_files=int(source.get("MAST_MAX_CONFLICT_FILES", limits.get("max_conflict_files", 2))),
            max_role_tokens=int(source.get("MAST_MAX_ROLE_TOKENS", limits.get("max_role_tokens", 200_000))),
        ),
    )
    config.validate()
    return config


def redact_secrets(text: str, config: AppConfig) -> str:
    redacted = text
    for value in (
        config.github_token,
        config.anthropic_api_key,
        config.openai_api_key,
        config.google_api_key,
        config.langfuse_public_key,
        config.langfuse_secret_key,
    ):
        if value:
            redacted = redacted.replace(value, "[REDACTED]")
    return redacted
