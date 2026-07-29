from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def write_text(self, run_id: str, name: str, content: str) -> str:
        path = self.root / run_id / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return str(path)

    def write_json(self, run_id: str, name: str, payload: dict[str, Any]) -> str:
        return self.write_text(run_id, name, json.dumps(payload, indent=2, sort_keys=True) + "\n")

