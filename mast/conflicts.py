from __future__ import annotations

import json
from pathlib import Path

from .messages import Message
from .models import ModelProvider, ModelRequest, complete_with_retry
from .runner import LocalRunner


def conflict_prompt(files: dict[str, str]) -> str:
    return (
        "Resolve these git conflict files. Return JSON as "
        '{"files":{"path":"complete resolved file content"}} only.\n\n'
        + json.dumps(files, indent=2, sort_keys=True)
    )


def resolve_conflicts(
    run_id: str,
    repo: str | Path,
    files: list[str],
    provider: ModelProvider,
    validate_command: list[str] | None = None,
    model: str = "claude-sonnet",
) -> Message:
    root = Path(repo)
    payload = {name: (root / name).read_text(errors="replace") for name in files}
    response = complete_with_retry(provider, ModelRequest(run_id, "merge", model, conflict_prompt(payload), payload))
    data = json.loads(response.text)
    replacements = data.get("files", {})
    if sorted(replacements) != sorted(files):
        raise ValueError("resolver must return exactly the conflicted files")
    for name, content in replacements.items():
        (root / name).write_text(content)
    validation = None
    if validate_command:
        validation = LocalRunner().run(validate_command, root)
        if validation.returncode != 0:
            raise ValueError(validation.stderr or validation.stdout or "conflict validation failed")
    return Message(
        type="approved",
        run_id=run_id,
        role="merge",
        tags=["conflict_resolved"],
        payload={"files": files, "validation": validation.stdout if validation else ""},
    )

