# GitHub Issues

## 1. Phase 1: Add file-backed task board and typed messages

Labels: `phase:1`, `task-board`

Goal: create the durable coordination spine for every agent handoff.

Scope:
- Define message types: `plan_request`, `subtask`, `diff_ready`, `review_needed`, `review_feedback`, `test_needed`, `approved`, `rejected`, `replan_needed`, `test_passed`, `test_failed`.
- Store messages in append-only JSONL.
- Make concurrent writes atomic.
- Add basic read/query helpers by run ID, role, tag, and subtask ID.

Acceptance criteria:
- Parallel writers cannot corrupt the board.
- A crashed worker can resume from board state.
- Message validation rejects unknown types and missing required fields.
- One runnable self-check covers concurrent append/read.

## 2. Phase 1: Add run and subtask schema

Labels: `phase:1`, `schema`

Goal: represent runs, subtasks, ownership, and handoff state consistently.

Scope:
- Define run ID, issue URL, role, model, subtask ID, parent IDs, status, timestamps, and token fields.
- Define subtask interface contracts: files touched, public functions, expected test impact.
- Keep schema serializable to JSON.

Acceptance criteria:
- Invalid status transitions are rejected.
- Subtasks can form a DAG.
- Schema docs include one complete example run.

## 3. Phase 2: Add issue intake and architect planning role

Labels: `phase:2`, `architect`

Goal: turn a GitHub issue into a decomposed implementation plan.

Scope:
- Fetch issue title, body, and comments.
- Prompt architect model to produce a subtask DAG.
- Require explicit interfaces for every subtask.
- Reject or flag ambiguous issues with `replan_needed`.

Acceptance criteria:
- Given an issue URL, the architect writes one plan to the task board.
- Ambiguous input produces a clear rejection instead of fake subtasks.
- Plan output validates against the schema.

## 4. Phase 2: Add orchestration CLI

Labels: `phase:2`, `orchestration`

Goal: provide one command that starts a run.

Scope:
- Add CLI arguments for issue URL, repo path, parallelism, and run ID.
- Initialize task board state.
- Start the architect step.
- Print run status and board path.

Acceptance criteria:
- `run --issue URL --parallelism 4` creates a run.
- Re-running with the same run ID resumes instead of duplicating state.

## 5. Phase 3: Add coder worker and worktree isolation

Labels: `phase:3`, `coder`

Goal: let each coder claim exactly one subtask and work in its own git worktree.

Scope:
- Claim unassigned subtasks atomically.
- Create one branch and worktree per coder.
- Run local tests for the assigned area.
- Emit `diff_ready` with patch and test deltas.

Acceptance criteria:
- Two coders cannot claim the same subtask.
- Each coder writes only in its assigned worktree.
- Diff metadata includes branch, patch path, and test command output.

## 6. Phase 3: Add declared-scope guard for coder changes

Labels: `phase:3`, `safety`

Goal: stop coder branches from silently editing files outside the architect plan.

Scope:
- Compare changed files against the subtask contract.
- Allow docs/tests if explicitly declared.
- Emit `replan_needed` when scope expands.

Acceptance criteria:
- Out-of-scope edits fail the coder handoff.
- The task board records the offending files.
- In-scope edits pass without extra prompts.

## 7. Phase 3: Add sandbox runner abstraction

Labels: `phase:3`, `sandbox`

Goal: run coder and tester commands behind an isolation boundary.

Scope:
- Add a minimal command runner interface.
- Implement local process execution first.
- Keep Daytona as a pluggable backend later.
- Capture stdout, stderr, exit code, and duration.

Acceptance criteria:
- Coder and tester use the same runner interface.
- Failed commands preserve logs as artifacts.
- Backend choice is configured per run.

## 8. Phase 4: Add deterministic merge coordinator

Labels: `phase:4`, `merge`

Goal: merge completed coder branches into one staging branch.

Scope:
- Wait until all subtasks are done or blocked.
- Three-way merge non-overlapping branches.
- Detect file-level overlap.
- Never drop conflicts silently.

Acceptance criteria:
- Non-overlapping branches merge without LLM calls.
- File overlap creates a conflict record.
- Staging branch contains every accepted coder change.

## 9. Phase 4: Add conflict logging and LLM conflict resolver hook

Labels: `phase:4`, `merge`

Goal: make merge conflicts auditable and optionally resolvable.

Scope:
- Log conflict files, branches, and attempted resolution.
- Add a resolver interface.
- Route only file-level overlap to the LLM resolver.

Acceptance criteria:
- Every conflict appears in the post-mortem data.
- Resolver output is applied only after validation.
- Unresolved conflicts block review.

## 10. Phase 5: Add reviewer role and self-approval guard

Labels: `phase:5`, `reviewer`

Goal: review the merged diff honestly.

Scope:
- Send only merged diff context to reviewer.
- Emit `approved` or `review_feedback`.
- Prevent approval if reviewer authored or proposed the diff.
- Route feedback to owning subtasks.

Acceptance criteria:
- Reviewer cannot approve its own changes.
- Feedback includes file paths and requested edits.
- Approved diff moves to tester.

## 11. Phase 6: Add isolated tester role

Labels: `phase:6`, `tester`

Goal: verify the staging branch in a clean environment.

Scope:
- Create a fresh test sandbox/worktree.
- Run the repo test command.
- Capture logs and stack traces.
- Emit `test_passed` or `test_failed`.

Acceptance criteria:
- Tester never modifies source files.
- Failures include artifacts and likely owning subtask.
- Passing tests trigger PR creation readiness.

## 12. Phase 7: Add Langfuse-style spans and token accounting

Labels: `phase:7`, `observability`

Goal: make cost and handoffs measurable.

Scope:
- Add spans for every role boundary.
- Track role, model, payload size, input tokens, output tokens, and run ID.
- Compute per-subtask token amplification.
- Export per-run JSON metrics.

Acceptance criteria:
- Every message has a trace/span ID.
- Total tokens can be grouped by role and subtask.
- `$ per solved issue` can be computed from exported metrics.

## 13. Phase 8: Add SWE-bench Pro evaluation and baseline

Labels: `phase:8`, `evaluation`

Goal: compare multi-agent runs against a single-agent baseline.

Scope:
- Define the fixed 50-issue subset.
- Run multi-agent pass@1.
- Run one Sonnet single-agent baseline on the same issues.
- Compare wall-clock, pass@1, and token cost.

Acceptance criteria:
- Results are reproducible from a saved issue list.
- Output includes pass@1 and cost per solved issue.
- Baseline uses the same issue set.

## 14. Phase 9: Add post-mortem report and handoff-failure histogram

Labels: `phase:9`, `reporting`

Goal: publish operational insight from every run.

Scope:
- Classify failed issues as plan too vague, merge conflict, reviewer false-approve, tester flake, or other.
- Generate a handoff-failure histogram.
- Include token amplification and speedup summaries.

Acceptance criteria:
- Every failed issue has one primary handoff failure label.
- Report includes histogram data and Markdown output.
- The final report links to run artifacts.

