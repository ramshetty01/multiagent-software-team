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
from tests.test_docker_runner import test_docker_runner_mounts_tester_readonly, test_runner_factory_selects_local_and_docker
from tests.test_daytona_runner import test_daytona_runner_reuses_and_closes_sandbox, test_runner_factory_selects_daytona
from tests.test_security import test_redact_artifact_hides_config_secrets, test_validate_command_blocks_obvious_danger, test_validate_repo_allowlist
from tests.test_merge_git import test_merge_branches_creates_staging_branch
from tests.test_conflicts import test_resolve_conflicts_writes_only_conflicted_files
from tests.test_feedback import test_route_review_feedback_to_owning_subtask
from tests.test_artifacts import test_artifact_store_writes_json, test_tester_failure_links_artifacts
from tests.test_failures import test_classify_retries_detects_flake, test_likely_owner_uses_trace_paths
from tests.test_pr import test_pr_creation_is_idempotent, test_pr_creation_requires_test_pass
from tests.test_tracing import test_langfuse_trace_log_writes_fallback_and_client, test_trace_log_factory_selects_backends
from tests.test_costs import test_call_cost_uses_model_pricing, test_cost_report_groups_by_role
from tests.test_eval_harness import test_load_issue_list_requires_50, test_run_eval_writes_summary
from tests.test_baseline import test_single_agent_baseline_records_tokens
from tests.test_probes import test_false_approval_rate_counts_approved_probes, test_injected_bug_probe_uses_reviewer_decision
from tests.test_final_report import test_final_report_combines_metrics
from tests.test_deploy_files import test_kubernetes_manifests_exist
from tests.test_ci_files import test_ci_workflow_runs_self_check
from tests.test_docs_index import test_readme_links_operator_docs
from tests.test_preflight import test_preflight_ok_requires_all_checks, test_run_preflight_returns_named_checks
from tests.test_providers import test_provider_factory_requires_prod_keys, test_provider_factory_uses_fake_in_local
from tests.test_status import test_run_status_summarizes_terminal_state
from tests.test_schema_export import test_export_schema_lists_message_types
from tests.test_artifact_cleanup import test_artifact_cleanup_supports_dry_run
from tests.test_cleanup import test_cleanup_plan_lists_mast_branches_and_worktrees
from tests.test_eval_validation import test_validate_issue_ids_rejects_placeholders
from tests.test_locks import test_run_lock_blocks_duplicate_holder
from tests.test_errors import test_error_json_is_stable
from tests.test_container_files import test_container_files_define_cli_entrypoint
from tests.test_governance_docs import test_governance_docs_exist
from tests.test_architecture_docs import test_diagrams_and_adrs_exist
from tests.test_validation import test_message_validation_runs_for_subtasks, test_subtask_payload_validation_rejects_missing_files
from tests.test_prompt_registry import test_model_request_carries_prompt_metadata, test_prompt_registry_exposes_versions


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
        test_docker_runner_mounts_tester_readonly(Path(tmp))
        test_daytona_runner_reuses_and_closes_sandbox(Path(tmp))
        test_validate_repo_allowlist(Path(tmp))
        test_merge_branches_creates_staging_branch(Path(tmp))
        test_resolve_conflicts_writes_only_conflicted_files(Path(tmp))
        test_route_review_feedback_to_owning_subtask(Path(tmp))
        test_artifact_store_writes_json(Path(tmp))
        test_tester_failure_links_artifacts(Path(tmp))
        test_pr_creation_requires_test_pass(Path(tmp))
        test_pr_creation_is_idempotent(Path(tmp))
        test_langfuse_trace_log_writes_fallback_and_client(Path(tmp))
        test_trace_log_factory_selects_backends(Path(tmp))
        test_cost_report_groups_by_role(Path(tmp))
        test_load_issue_list_requires_50(Path(tmp))
        test_run_eval_writes_summary(Path(tmp))
        test_single_agent_baseline_records_tokens(Path(tmp))
        test_final_report_combines_metrics(Path(tmp))
        test_run_status_summarizes_terminal_state(Path(tmp))
        test_artifact_cleanup_supports_dry_run(Path(tmp))
        test_cleanup_plan_lists_mast_branches_and_worktrees(Path(tmp))
        test_run_lock_blocks_duplicate_holder(Path(tmp))
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
    test_runner_factory_selects_local_and_docker()
    test_runner_factory_selects_daytona()
    test_validate_command_blocks_obvious_danger()
    test_redact_artifact_hides_config_secrets()
    test_classify_retries_detects_flake()
    test_likely_owner_uses_trace_paths()
    test_call_cost_uses_model_pricing()
    test_false_approval_rate_counts_approved_probes()
    test_injected_bug_probe_uses_reviewer_decision()
    test_kubernetes_manifests_exist()
    test_ci_workflow_runs_self_check()
    test_readme_links_operator_docs()
    test_preflight_ok_requires_all_checks()
    test_run_preflight_returns_named_checks()
    test_provider_factory_uses_fake_in_local()
    test_provider_factory_requires_prod_keys()
    test_export_schema_lists_message_types()
    test_validate_issue_ids_rejects_placeholders()
    test_error_json_is_stable()
    test_container_files_define_cli_entrypoint()
    test_governance_docs_exist()
    test_diagrams_and_adrs_exist()
    test_subtask_payload_validation_rejects_missing_files()
    test_message_validation_runs_for_subtasks()
    test_prompt_registry_exposes_versions()
    test_model_request_carries_prompt_metadata()
    print("self-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
