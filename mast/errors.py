from __future__ import annotations

import json


def error_json(code: str, message: str) -> str:
    return json.dumps({"error": code, "message": message}, sort_keys=True)

