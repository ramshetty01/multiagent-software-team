# ADR 0001: File-Backed Task Board

## Status

Accepted for local and small-scale runs.

## Context

The system needs resumable handoffs between architect, coders, merge,
reviewer, tester, and PR creation.

## Decision

Use append-only JSONL with file locks for the first implementation.

## Consequences

This keeps local operation simple and debuggable. It is not sufficient for
multi-node Kubernetes deployments; Redis/Postgres should replace it when
distributed workers run across machines.

