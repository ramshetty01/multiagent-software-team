# Operator Setup

## Local

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
scripts/self_check.py
```

Use `.env.example` as the secret template. Local dry runs can use
`MAST_SANDBOX_BACKEND=local` and `MAST_TRACING_BACKEND=jsonl`.

## Production

Required services:

- GitHub token with repository and PR permissions.
- Anthropic key for architect/coder calls.
- OpenAI key for reviewer calls.
- Google key for tester analysis.
- Langfuse credentials when tracing backend is `langfuse`.
- Docker or Daytona sandbox backend.

Operational runbooks are tracked in [operations.md](operations.md). Security
boundaries are tracked in [threat-model.md](threat-model.md).
