# Security Policy

This project may execute commands from untrusted repositories. Treat target
repositories as hostile.

## Reporting

Open a private security advisory or contact the repository owner. Do not open a
public issue for exploitable sandbox, secret, or command-execution problems.

## Supported Surface

- command allowlist
- repository allowlist
- Docker and Daytona runner boundaries
- secret redaction in logs and artifacts
- prompt-injection guidance in [docs/threat-model.md](docs/threat-model.md)

## Non-Goals

The default local runner is not a security boundary.
