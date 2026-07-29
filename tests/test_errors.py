from __future__ import annotations

import json

from mast.errors import error_json


def test_error_json_is_stable():
    assert json.loads(error_json("bad", "thing")) == {"error": "bad", "message": "thing"}

