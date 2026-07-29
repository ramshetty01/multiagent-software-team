from __future__ import annotations

import json
import shutil
import time
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

    def cleanup_older_than(self, days: int, dry_run: bool = True) -> list[str]:
        cutoff = time.time() - (days * 86400)
        candidates = [path for path in self.root.iterdir() if path.is_dir() and path.stat().st_mtime < cutoff] if self.root.exists() else []
        removed = [str(path) for path in candidates]
        if not dry_run:
            for path in candidates:
                shutil.rmtree(path)
        return removed
