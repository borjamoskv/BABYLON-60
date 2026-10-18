from dataclasses import replace

from scripts.c5_cortex.poc_fl008_fail_closed import (
    AuthoritySnapshot,
    Decision,
    FailClosedCoordinator,
    SyntheticAuthority,
    SyntheticFencedSink,
    SyntheticIdentityProvider,
    _register_case,
    run_stress_simulation,
)


def test_missing_gates_never_reach_the_synthetic_effect() -> None:
    identities = SyntheticIdentityProvider()
    authority = SyntheticAuthority()
    sink = SyntheticFencedSink()
    schedule, token, grant, approval = _register_case("missing-gates", identities, authority, sink)
    coordinator_variants = (
        FailClosedCoordinator(None, authority, sink),
        FailClosedCoordinator(identities, None, sink),
        FailClosedCoordinator(identities, authority, None),
    )

    for coordinator in coordinator_variants:
        decision = coordinator.fire(schedule, token, grant, approval, 1)
        assert decision is Decision.DENIED_MISSING_GATE

    assert sink.effect_count == 0


def test_identity_scope_policy_and_checkpoint_drift_fail_closed() -> None:
    identities = SyntheticIdentityProvider()
    authority = SyntheticAuthority()
    sink = SyntheticFencedSink()
    coordinator = FailClosedCoordinator(identities, authority, sink)
    schedule, token, grant, approval = _register_case("scope", identities, authority, sink)

    assert coordinator.fire(schedule, "unknown-token", grant, approval, 1) is (Decision.DENIED_IDENTITY)
    assert (
        coordinator.fire(
            schedule,
            token,
            replace(grant, branch_id="other-branch"),
            approval,
            1,
        )
        is Decision.DENIED_SCOPE
    )
    assert coordinator.fire(schedule, token, grant, None, 1) is (Decision.DENIED_OPERATOR)

    authority.register(
        schedule.owner_subject,
        schedule.branch_id,
        AuthoritySnapshot(1, "policy-v2"),
    )
    assert coordinator.fire(schedule, token, grant, approval, 1) is (Decision.DENIED_STALE_POLICY)
    authority.register(
        schedule.owner_subject,
        schedule.branch_id,
        AuthoritySnapshot(1, "policy-v1"),
    )
    sink.advance_checkpoint(schedule.schedule_id, "checkpoint-moved", 2)
    assert coordinator.fire(schedule, token, grant, approval, 3) is (Decision.DENIED_PRECONDITION)
    assert sink.effect_count == 0


def test_replaying_a_committed_nonce_does_not_repeat_the_effect() -> None:
    identities = SyntheticIdentityProvider()
    authority = SyntheticAuthority()
    sink = SyntheticFencedSink()
    coordinator = FailClosedCoordinator(identities, authority, sink)
    schedule, token, grant, approval = _register_case("duplicate-nonce", identities, authority, sink)

    first = coordinator.fire(schedule, token, grant, approval, 1)
    replay = coordinator.fire(schedule, token, grant, approval, 2)

    assert first is Decision.COMMITTED
    assert replay is Decision.DENIED_REPLAY
    assert sink.effect_count == 1


def test_500_schedule_races_have_no_commit_after_revocation_ack() -> None:
    report = run_stress_simulation(iterations=500)

    assert report.mode == "SIMULATION_ONLY"
    assert report.schedules == 500
    assert report.warmup_commits == 1
    assert 0 <= report.race_commits <= report.schedules
    assert report.post_revoke_replays == report.schedules
    assert report.stale_commits_after_revoke_ack == 0
    assert report.runtime_certified is False
