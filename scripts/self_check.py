#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_board import test_board_handles_parallel_writes
from tests.test_flow import (
    test_architect_rejects_ambiguous_issue,
    test_coder_scope_guard,
    test_merge_reviewer_metrics_and_reporting,
    test_schema_dag_and_status,
)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path

        test_board_handles_parallel_writes(Path(tmp))
        test_coder_scope_guard(Path(tmp))
    test_schema_dag_and_status()
    test_architect_rejects_ambiguous_issue()
    test_merge_reviewer_metrics_and_reporting()
    print("self-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
