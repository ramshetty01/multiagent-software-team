# ADR 0003: Sandbox Backend Abstraction

## Status

Accepted.

## Context

Coder and tester commands execute untrusted repository code.

## Decision

Expose a runner interface with local, Docker, and Daytona implementations.

## Consequences

The local runner is not a security boundary. Production runs should use Docker
or Daytona with an explicit command allowlist and repo allowlist.

