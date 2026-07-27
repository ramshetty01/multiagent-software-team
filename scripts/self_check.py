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
from tests.test_github import test_parse_issue_ref_accepts_url_and_short_form, test_save_issue_context_writes_normalized_artifact


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path

        test_board_handles_parallel_writes(Path(tmp))
        test_coder_scope_guard(Path(tmp))
        test_save_issue_context_writes_normalized_artifact(Path(tmp))
    test_schema_dag_and_status()
    test_architect_rejects_ambiguous_issue()
    test_merge_reviewer_metrics_and_reporting()
    test_parse_issue_ref_accepts_url_and_short_form()
    print("self-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
