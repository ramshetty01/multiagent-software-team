# Benchmarks and Evaluation

This repository must not claim a production score until the run artifacts are
present. The current codebase contains the harness contracts and example
outputs; a real benchmark requires licensed SWE-bench Pro issue IDs, live model
credentials, isolated execution, and retained artifacts.

## Required Datasets

| Dataset | Purpose | Required before claim |
| --- | --- | --- |
| SWE-bench Pro 50-issue subset | Primary issue-to-PR pass@1 measurement | yes |
| Single-agent baseline on the same 50 issues | Cost and wall-clock comparison | yes |
| Injected-bug reviewer probe | Reviewer false-approval measurement | yes |
| Flake replay set | Tester flake classification checks | before production use |

The file `data/swebench-pro-50.txt` is intentionally validated as a 50-line
input list. Placeholder IDs are rejected by the evaluation loader and must be
replaced before reporting a score.

## Primary Metrics

| Metric | Formula | Source |
| --- | --- | --- |
| Multi-agent pass@1 | solved issues / 50 | `mast.eval.summarize` |
| Baseline pass@1 | baseline solved issues / 50 | `mast.eval.summarize` |
| Parallel speedup | baseline wall-clock seconds / multi-agent wall-clock seconds | `mast.eval.summarize` |
| Token delta | multi-agent tokens - baseline tokens | provider usage logs |
| Dollars per solved issue | total model spend / solved issues | role cost report |
| Reviewer false-approval rate | approved injected-bug probes / total probes | probe report |
| Handoff-failure histogram | classified failed handoffs by label | post-mortem report |

## Fair Baseline Rules

- Use the same issue list for multi-agent and single-agent runs.
- Start both runs from a clean clone of the same commit.
- Run both with the same test commands and timeout policy.
- Count all LLM calls, retries, reviewer loops, tester calls, and conflict
  resolution calls.
- Preserve failed-run artifacts instead of deleting them after retries.
- Do not include human fixes or manual cherry-picks in pass@1.

## Artifact Contract

Each scored run should retain these files:

| Artifact | Description |
| --- | --- |
| `board.jsonl` | append-only task-board messages |
| `eval.json` | per-issue pass/fail, wall-clock, and token summary |
| `costs.json` | cost grouped by role and model |
| `postmortem.md` | failed-handoff classification and histogram |
| `trace.jsonl` | Langfuse fallback trace export when hosted tracing is unavailable |
| `test.log` | tester command output for every failed issue |

## Required Ablations

The flagship report should include at least these comparisons:

- Single-agent Sonnet baseline versus four-coder multi-agent run.
- Two-coder versus four-coder parallelism.
- Deterministic merge-only runs versus LLM conflict-resolution runs.
- Reviewer model swap, with false-approval rate and cost delta.
- Tester rerun policy enabled versus disabled on known flaky failures.

## Reporting Standard

A published benchmark report must include:

- exact repo commit SHA
- issue IDs or licensed dataset reference
- model names and provider versions
- sandbox backend and runner image
- timeout policy
- failed issue table
- benchmark artifact archive checksum
- explicit limitations and known invalid runs

Until those artifacts exist, README language should say the repository has an
evaluation harness, not a measured SWE-bench Pro result.
