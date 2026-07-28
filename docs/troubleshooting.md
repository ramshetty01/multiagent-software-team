# Troubleshooting

## GitHub Intake Fails

Run `gh auth status`. Confirm the token can read the target repo and issue.

## Coder Cannot Claim Work

Check `subtask_claimed` messages. Expired leases can be reclaimed after their
TTL; active leases block duplicate ownership.

## Sandbox Command Fails

Use the command artifact logs first. Docker runs without network by default.
Daytona failures should include the sandbox ID in command metadata.

## Merge Blocks

Check `rejected` messages tagged `conflict`. Conflict resolver output must
replace exactly the conflicted files and pass validation.

## Tester Fails

Review stored stdout/stderr artifacts and `retry_classification`. A mixed
fail/pass retry sequence is classified as a flaky test.

