# Demo issue

## Title

Add a dry-run health endpoint to the sample service

## Body

The repository contains a small service module. Add a read-only `/healthz` endpoint
that returns status metadata without changing write paths.

Acceptance criteria:

- Implement the endpoint in `src/service.py`.
- Add or update tests in `tests/test_service.py`.
- Do not modify deployment manifests.
- Return a stable JSON object with `status` and `version`.
