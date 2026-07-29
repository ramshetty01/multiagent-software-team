# Threat Model

The system reads GitHub issues, checks out repository code, runs commands, and
sends selected context to model providers. The target repository and issue text
must be treated as untrusted input.

## Assets

- provider API keys
- GitHub token
- target repository write permissions
- task-board history
- run artifacts and logs
- sandbox credentials
- benchmark results

## Trust Boundaries

| Boundary | Risk |
| --- | --- |
| GitHub issue to architect prompt | prompt injection and malicious instructions |
| Target repository to coder/tester sandbox | arbitrary code execution |
| Sandbox to host | secret exfiltration and filesystem escape |
| Model output to patch application | hallucinated or out-of-scope edits |
| Reviewer decision to PR creation | false approval of vulnerable code |
| Artifact logs to humans/providers | accidental secret disclosure |

## Primary Threats

### Prompt Injection

Issue text, comments, source files, test logs, and README content can contain
instructions that try to override role policy. Agents must treat repository
content as data. Role prompts should restate authority order and reject requests
to expose secrets, alter scope, disable tests, or approve their own changes.

### Untrusted Code Execution

Coder and tester commands may execute attacker-controlled scripts. Production
runs must use Docker or Daytona isolation. The local runner is for development
only and is not a security boundary.

### Secret Exfiltration

Provider keys and GitHub tokens must not be mounted into coder or tester
sandboxes unless strictly required. Logs and artifacts must pass redaction
before being stored or sent to another role.

### Out-of-Scope Patches

Coders can accidentally or maliciously touch files outside the architect's
contract. Scope validation must run before `diff_ready`, review routing, and PR
creation.

### Reviewer False Approval

The reviewer must only see the merged diff and must not approve changes it
authored. Injected-bug probes are required to measure false-approval rate.

### Benchmark Tampering

Benchmark issue IDs, pass/fail labels, and post-mortem classifications must be
stored as immutable artifacts. Manual fixes invalidate pass@1 for that issue.

## Required Controls

- repository allowlist
- command allowlist
- sandbox without default host secret mounts
- network restrictions for test execution where practical
- append-only task board
- role-tagged tracing and cost accounting
- artifact redaction
- self-approval guard
- scope guard before patch acceptance
- idempotent PR creation

## Incident Response

1. Stop all workers for the affected run.
2. Revoke exposed provider or GitHub credentials.
3. Preserve board, trace, artifact, and sandbox metadata.
4. Identify the first unsafe boundary crossing.
5. Patch the control and add a regression test.
6. Mark the run invalid in benchmark reports.

## Known Limitations

- The local runner is unsafe for hostile repositories.
- Starter Kubernetes manifests need cluster-specific policy hardening.
- Prompt-injection defenses reduce risk but do not prove model compliance.
- The JSONL task board is append-only but not tamper-proof against host access.
