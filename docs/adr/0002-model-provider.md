# ADR 0002: Shared Model Provider Interface

## Status

Accepted.

## Context

Each role uses a different model provider, but role logic should not depend on
SDK-specific response shapes.

## Decision

Route model calls through `ModelProvider`, `ModelRequest`, and `ModelResponse`.

## Consequences

Provider adapters stay thin. Prompt/versioning and structured output validation
must live above provider adapters.

