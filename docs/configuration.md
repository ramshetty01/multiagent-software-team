# Configuration

Local runs work without provider secrets:

```sh
python3 -m mast.cli run --issue owner/repo#1 --config config/local.json
```

Minimum local config:

```json
{
  "environment": "local",
  "sandbox_backend": "local",
  "tracing_backend": "jsonl"
}
```

Production runs require GitHub and model provider credentials through
environment variables. Copy `.env.example` and fill values in your secret
manager; do not commit real secrets.

