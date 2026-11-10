# ADR 0004: Constrain automated host Git helpers

Status: accepted for the local prototype.

The Docker test runner does not isolate the host Git operations used to prepare,
commit and inspect worktrees. A regression reproduced a pre-commit hook writing a
marker on the host and an external diff helper replacing review evidence.

Disable hooks, fsmonitor, signing and diff/textconv helpers in the shared Git wrapper.
Use a credential-stripped noninteractive environment and per-command timeout. These
settings are command-local, so user Git configuration is not changed. Regression tests
use temporary repositories and harmless marker scripts.

This deliberately does not claim a full hostile-repository boundary: custom filter and
merge drivers, local configuration, paths and crash recovery remain unresolved. A later
production design should move Git operations into a disposable isolated environment
with narrowly scoped filesystem and credential access.
