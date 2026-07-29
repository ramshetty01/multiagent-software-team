from __future__ import annotations

from mast.probes import ProbeResult, false_approval_rate, injected_bug_probe
from mast.reviewer import Reviewer


def test_false_approval_rate_counts_approved_probes():
    assert false_approval_rate([ProbeResult("a", True), ProbeResult("b", False)]) == 0.5


def test_injected_bug_probe_uses_reviewer_decision():
    assert injected_bug_probe(Reviewer(), "r1", "TODO: broken").approved is False

