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


## Graph execution

`--execute` requires production provider settings and `sandbox_backend: docker`.
The graph passes configured models/providers to each role and uses Docker for coder
checks and final tests. `MAST_SANDBOX_IMAGE` / `sandbox_image` selects a prebuilt image
with target test dependencies. Network access is disabled inside command containers.
Daytona graph execution is withheld until repository synchronization is implemented.
Local mode remains a demo, explicitly labelled `demo_completed`.
