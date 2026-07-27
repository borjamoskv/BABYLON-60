import pytest
import datetime

from babylon60.swarm.trust_registry import TrustRegistry, AgentTrustProfile, WeightedProposal

def test_trust_profile_creation():
    registry = TrustRegistry()
    profile = registry.get_profile("agent-1")
    assert profile.agent_id == "agent-1"
    assert profile.prior == 0.5
    assert profile.successes == 0

def test_register_feedback_success():
    registry = TrustRegistry()
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    registry.register_feedback("agent-1", success=True, now=now)

    profile = registry.get_profile("agent-1")
    assert profile.successes == 1
    assert profile.failures == 0
    assert profile.last_success_ts == now

def test_register_feedback_failure_with_taint():
    registry = TrustRegistry()
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    registry.register_feedback("agent-1", success=False, is_taint=True, taint_severity=0.5, now=now)

    profile = registry.get_profile("agent-1")
    assert profile.successes == 0
    assert profile.failures == 1
    assert profile.taint_events == 1
    assert profile.taint_severity_sum == 0.5
    assert profile.last_incident_ts == now

def test_compute_trust_score():
    registry = TrustRegistry()
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    registry.register_feedback("agent-1", success=True, now=now)

    profile = registry.get_profile("agent-1")
    score = registry.compute_trust_score(profile, now=now)
    # With laplace smoothing: successes=1, prior=0.5 -> alpha=1.0, beta=1.0
    # reliability = (1.0 + 1) / (2.0 + 1) = 2.0 / 3.0 ~ 0.666
    # score = 0.5 + (0.666 - 0.5) - 0 - 0 + 0 = 0.666
    assert 0.66 < score < 0.67

def test_rank_proposals():
    registry = TrustRegistry()
    registry.register_feedback("agent-good", success=True)
    registry.register_feedback("agent-bad", success=False, is_taint=True, taint_severity=1.0)

    proposals = [
        WeightedProposal(agent_id="agent-bad", proposal_id="p1", action="test", domain="test", raw_confidence=0.9),
        WeightedProposal(agent_id="agent-good", proposal_id="p2", action="test", domain="test", raw_confidence=0.9)
    ]

    ranked = registry.rank_proposals(proposals)
    assert len(ranked) == 2
    assert ranked[0].agent_id == "agent-good"
    assert ranked[1].agent_id == "agent-bad"
    assert ranked[0].final_score > ranked[1].final_score

def test_collapse_conflict():
    registry = TrustRegistry()
    registry.register_feedback("agent-1", success=True)

    proposals = [
        WeightedProposal(agent_id="agent-1", proposal_id="p1", action="test", domain="test", raw_confidence=0.9)
    ]

    winner, diagnostic = registry.collapse_conflict(proposals)
    assert winner is not None
    assert winner.agent_id == "agent-1"
