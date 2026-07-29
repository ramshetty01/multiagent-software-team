from __future__ import annotations


def test_agent_package_exports_existing_role_api():
    from mast.agents import CoderWorker, Reviewer, Tester, plan_from_issue, resolve_test_command
    from mast.coder import CoderWorker as CompatCoderWorker

    assert CoderWorker is CompatCoderWorker
    assert Reviewer
    assert Tester
    assert plan_from_issue
    assert resolve_test_command
