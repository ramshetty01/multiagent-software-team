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

## CI credential-literal check

`python scripts/scan_secrets.py` checks tracked UTF-8 files for credential-like token
literals with boundaries and minimum lengths. It reports only file/line locations,
never matched values. This heuristic is not exhaustive: it does not inspect Git
history, binaries, split/encoded secrets or arbitrary provider credentials. Use a
provider-aware secret scanner and secret rotation procedures for release operations.

## Host Git operations

Automated Git worktree/commit/status operations disable hooks, filesystem-monitor
helpers and commit signing. Review diffs disable external diff and text-conversion
helpers. Child Git processes strip credential-shaped environment variable names and
Git environment overrides, disable interactive authentication and have a 120-second
per-command timeout. This protects specific helper execution paths, not a complete
hostile-repository sandbox. Custom clean/smudge filters, merge drivers, local Git
configuration, symlinks and filesystem access still require a trusted checkout or a
stronger disposable isolated Git execution design. A partial/timeout Git operation
may need operator recovery before retrying. Do not run arbitrary hostile repositories
on a credential-bearing host based solely on these checks.
