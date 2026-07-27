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
from tests.test_config import test_load_config_from_file_and_env, test_production_config_requires_provider_keys, test_redact_secrets
from tests.test_models import test_complete_with_retry_surfaces_structured_failure, test_fake_provider_returns_token_usage, test_roles_use_shared_provider_interface
from tests.test_anthropic import test_anthropic_provider_maps_messages_response
from tests.test_prompts import test_coder_can_draft_patch_from_declared_files, test_parse_architect_json_validates_subtasks
from tests.test_openai_provider import test_openai_provider_maps_responses_output
from tests.test_reviewer import test_parse_review_json_requires_structured_feedback, test_reviewer_returns_structured_model_feedback
from tests.test_gemini import test_gemini_provider_maps_generate_content_response
from tests.test_tester import test_parse_test_failure_json_rejects_unknown_label, test_tester_classifies_failure_without_editing
from tests.test_orchestrator import test_orchestrator_resumes_completed_nodes
from tests.test_claims import test_claim_subtask_is_atomic_under_parallel_workers, test_expired_lease_can_be_reclaimed
from tests.test_supervisor import test_supervisor_limits_parallel_workers_and_records_lifecycle, test_supervisor_reports_worker_failure
from tests.test_worktree import test_branch_and_worktree_names_are_deterministic, test_worktree_manager_prepares_and_commits
from tests.test_patch_loop import test_coder_patch_loop_applies_diff_and_commits
from tests.test_scope import test_scope_accepts_exact_globs_and_directories, test_scope_allows_generated_lockfiles_only_when_configured


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path

        test_board_handles_parallel_writes(Path(tmp))
        test_coder_scope_guard(Path(tmp))
        test_save_issue_context_writes_normalized_artifact(Path(tmp))
        test_load_config_from_file_and_env(Path(tmp))
        test_coder_can_draft_patch_from_declared_files(Path(tmp))
        test_tester_classifies_failure_without_editing(Path(tmp))
        test_orchestrator_resumes_completed_nodes(Path(tmp))
        test_claim_subtask_is_atomic_under_parallel_workers(Path(tmp))
        test_expired_lease_can_be_reclaimed(Path(tmp))
        test_supervisor_limits_parallel_workers_and_records_lifecycle(Path(tmp))
        test_supervisor_reports_worker_failure(Path(tmp))
        test_branch_and_worktree_names_are_deterministic(Path(tmp))
        test_worktree_manager_prepares_and_commits(Path(tmp))
        test_coder_patch_loop_applies_diff_and_commits(Path(tmp))
    test_schema_dag_and_status()
    test_architect_rejects_ambiguous_issue()
    test_merge_reviewer_metrics_and_reporting()
    test_parse_issue_ref_accepts_url_and_short_form()
    test_production_config_requires_provider_keys()
    test_redact_secrets()
    test_fake_provider_returns_token_usage()
    test_complete_with_retry_surfaces_structured_failure()
    test_roles_use_shared_provider_interface()
    test_anthropic_provider_maps_messages_response()
    test_parse_architect_json_validates_subtasks()
    test_openai_provider_maps_responses_output()
    test_parse_review_json_requires_structured_feedback()
    test_reviewer_returns_structured_model_feedback()
    test_gemini_provider_maps_generate_content_response()
    test_parse_test_failure_json_rejects_unknown_label()
    test_scope_accepts_exact_globs_and_directories()
    test_scope_allows_generated_lockfiles_only_when_configured()
    print("self-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
