"""PoC sintético FL-008: revocación y despacho fail-closed.

Este módulo solo usa dobles en memoria. No importa el MCP ni el executor, no
abre sockets, no lee credenciales y no puede mutar recursos externos. Sus
atestaciones y aprobaciones no son criptográficas ni Touch ID; la simulación
no certifica un runtime.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from enum import Enum
from threading import Barrier, Lock


DISPATCH_ROLE = "cortex.dispatch"


class Decision(str, Enum):
    COMMITTED = "COMMITTED"
    DENIED_MISSING_GATE = "DENIED_MISSING_GATE"
    DENIED_IDENTITY = "DENIED_IDENTITY"
    DENIED_ROLE = "DENIED_ROLE"
    DENIED_SCOPE = "DENIED_SCOPE"
    DENIED_STALE_AUTHORITY = "DENIED_STALE_AUTHORITY"
    DENIED_STALE_POLICY = "DENIED_STALE_POLICY"
    DENIED_EXPIRED = "DENIED_EXPIRED"
    DENIED_OPERATOR = "DENIED_OPERATOR"
    DENIED_FENCE = "DENIED_FENCE"
    DENIED_PRECONDITION = "DENIED_PRECONDITION"
    DENIED_REPLAY = "DENIED_REPLAY"


@dataclass(frozen=True, slots=True)
class Schedule:
    schedule_id: str
    owner_subject: str
    branch_id: str
    checkpoint_id: str
    action_id: str


@dataclass(frozen=True, slots=True)
class SyntheticPrincipal:
    subject: str
    roles: frozenset[str]
    branches: frozenset[str]


@dataclass(frozen=True, slots=True)
class AuthoritySnapshot:
    epoch: int
    policy_revision: str


@dataclass(frozen=True, slots=True)
class SyntheticGrant:
    principal_subject: str
    schedule_id: str
    branch_id: str
    checkpoint_id: str
    action_id: str
    authority_epoch: int
    policy_revision: str
    nonce: str
    expires_at_tick: int


@dataclass(frozen=True, slots=True)
class SyntheticOperatorApproval:
    schedule_id: str
    action_id: str
    nonce: str
    expires_at_tick: int


@dataclass(frozen=True, slots=True)
class SinkEvent:
    event_id: str
    logical_tick: int
    sequence: int
    kind: str
    schedule_id: str | None
    branch_id: str
    decision: Decision | None


class SyntheticIdentityProvider:
    """Mapa de tokens ficticios; nunca valida una identidad real."""

    def __init__(self) -> None:
        self._tokens: dict[str, SyntheticPrincipal] = {}
        self._lock = Lock()

    def register(self, token: str, principal: SyntheticPrincipal) -> None:
        with self._lock:
            self._tokens[token] = principal

    def verify(self, token: str) -> SyntheticPrincipal | None:
        with self._lock:
            return self._tokens.get(token)


class SyntheticAuthority:
    """Estado de autoridad versionado en memoria para la simulación."""

    def __init__(self) -> None:
        self._snapshots: dict[tuple[str, str], AuthoritySnapshot] = {}
        self._lock = Lock()

    def register(
        self, subject: str, branch_id: str, snapshot: AuthoritySnapshot
    ) -> None:
        with self._lock:
            self._snapshots[(subject, branch_id)] = snapshot

    def current(self, subject: str, branch_id: str) -> AuthoritySnapshot | None:
        with self._lock:
            return self._snapshots.get((subject, branch_id))

    def advance_epoch(self, subject: str, branch_id: str, epoch: int) -> None:
        with self._lock:
            key = (subject, branch_id)
            current = self._snapshots.get(key)
            if current is None or epoch <= current.epoch:
                raise ValueError("la época debe aumentar de forma monótona")
            self._snapshots[key] = AuthoritySnapshot(epoch, current.policy_revision)


class SyntheticFencedSink:
    """Destino efímero que aplica fence, checkpoint y nonce bajo un lock."""

    def __init__(self) -> None:
        self._minimum_epochs: dict[str, int] = {}
        self._checkpoints: dict[str, str] = {}
        self._schedule_branches: dict[str, str] = {}
        self._consumed_nonces: set[str] = set()
        self._events: list[SinkEvent] = []
        self._sequence = 0
        self._logical_tick = 0
        self._lock = Lock()

    def register_schedule(self, schedule: Schedule, minimum_epoch: int) -> None:
        with self._lock:
            if schedule.schedule_id in self._checkpoints:
                raise ValueError("schedule_id duplicado")
            existing_epoch = self._minimum_epochs.get(schedule.branch_id)
            if existing_epoch is not None and existing_epoch != minimum_epoch:
                raise ValueError("épocas iniciales incompatibles en la rama")
            self._minimum_epochs[schedule.branch_id] = minimum_epoch
            self._checkpoints[schedule.schedule_id] = schedule.checkpoint_id
            self._schedule_branches[schedule.schedule_id] = schedule.branch_id

    def record_gate_denial(
        self, schedule: Schedule, decision: Decision, requested_tick: int
    ) -> None:
        with self._lock:
            self._record_locked(
                "GATE_DENIED", schedule.schedule_id, schedule.branch_id,
                decision, requested_tick,
            )

    def advance_checkpoint(
        self, schedule_id: str, checkpoint_id: str, requested_tick: int
    ) -> SinkEvent:
        with self._lock:
            branch_id = self._schedule_branches.get(schedule_id)
            if branch_id is None:
                raise KeyError("programación no registrada")
            self._checkpoints[schedule_id] = checkpoint_id
            return self._record_locked(
                "CHECKPOINT_MOVED", schedule_id, branch_id, None, requested_tick
            )

    def advance_fence(
        self, branch_id: str, new_epoch: int, requested_tick: int
    ) -> SinkEvent:
        with self._lock:
            current_epoch = self._minimum_epochs.get(branch_id)
            if current_epoch is None or new_epoch <= current_epoch:
                return self._record_locked(
                    "FENCE_REJECTED", None, branch_id,
                    Decision.DENIED_FENCE, requested_tick,
                )
            self._minimum_epochs[branch_id] = new_epoch
            return self._record_locked(
                "REVOKED_ACK", None, branch_id, None, requested_tick
            )

    def commit_atomically(
        self, schedule: Schedule, grant: SyntheticGrant, requested_tick: int
    ) -> Decision:
        with self._lock:
            if (
                self._schedule_branches.get(schedule.schedule_id) != schedule.branch_id
                or grant.schedule_id != schedule.schedule_id
                or grant.branch_id != schedule.branch_id
            ):
                return self._deny_locked(
                    schedule, Decision.DENIED_SCOPE, requested_tick
                )
            if self._minimum_epochs.get(schedule.branch_id) != grant.authority_epoch:
                return self._deny_locked(
                    schedule, Decision.DENIED_FENCE, requested_tick
                )
            if self._checkpoints.get(schedule.schedule_id) != grant.checkpoint_id:
                return self._deny_locked(
                    schedule, Decision.DENIED_PRECONDITION, requested_tick
                )
            if grant.nonce in self._consumed_nonces:
                return self._deny_locked(
                    schedule, Decision.DENIED_REPLAY, requested_tick
                )
            self._consumed_nonces.add(grant.nonce)
            self._record_locked(
                "EFFECT_COMMITTED", schedule.schedule_id, schedule.branch_id,
                Decision.COMMITTED, requested_tick,
            )
            return Decision.COMMITTED

    def events_for_branch(self, branch_id: str) -> tuple[SinkEvent, ...]:
        with self._lock:
            return tuple(event for event in self._events if event.branch_id == branch_id)

    @property
    def effect_count(self) -> int:
        with self._lock:
            return sum(event.kind == "EFFECT_COMMITTED" for event in self._events)

    def _deny_locked(
        self, schedule: Schedule, decision: Decision, requested_tick: int
    ) -> Decision:
        self._record_locked(
            "EFFECT_DENIED", schedule.schedule_id, schedule.branch_id,
            decision, requested_tick,
        )
        return decision

    def _record_locked(
        self,
        kind: str,
        schedule_id: str | None,
        branch_id: str,
        decision: Decision | None,
        requested_tick: int,
    ) -> SinkEvent:
        self._sequence += 1
        self._logical_tick = max(self._logical_tick + 1, requested_tick)
        event = SinkEvent(
            event_id=f"EV_{self._logical_tick}_{self._sequence}",
            logical_tick=self._logical_tick,
            sequence=self._sequence,
            kind=kind,
            schedule_id=schedule_id,
            branch_id=branch_id,
            decision=decision,
        )
        self._events.append(event)
        return event


class FailClosedCoordinator:
    """Coordinador PoC; requiere gates sintéticos explícitos para cada fire."""

    def __init__(
        self,
        identities: SyntheticIdentityProvider | None,
        authority: SyntheticAuthority | None,
        sink: SyntheticFencedSink | None,
    ) -> None:
        self._identities = identities
        self._authority = authority
        self._sink = sink

    def fire(
        self,
        schedule: Schedule,
        token: str,
        grant: SyntheticGrant,
        approval: SyntheticOperatorApproval | None,
        logical_tick: int,
    ) -> Decision:
        if self._identities is None or self._authority is None or self._sink is None:
            return self._deny(schedule, Decision.DENIED_MISSING_GATE, logical_tick)

        principal = self._identities.verify(token)
        if principal is None or principal.subject != schedule.owner_subject:
            return self._deny(schedule, Decision.DENIED_IDENTITY, logical_tick)
        if DISPATCH_ROLE not in principal.roles:
            return self._deny(schedule, Decision.DENIED_ROLE, logical_tick)
        if schedule.branch_id not in principal.branches:
            return self._deny(schedule, Decision.DENIED_SCOPE, logical_tick)
        if (
            grant.principal_subject != principal.subject
            or grant.schedule_id != schedule.schedule_id
            or grant.branch_id != schedule.branch_id
            or grant.checkpoint_id != schedule.checkpoint_id
            or grant.action_id != schedule.action_id
        ):
            return self._deny(schedule, Decision.DENIED_SCOPE, logical_tick)

        snapshot = self._authority.current(principal.subject, schedule.branch_id)
        if snapshot is None:
            return self._deny(schedule, Decision.DENIED_MISSING_GATE, logical_tick)
        if grant.authority_epoch != snapshot.epoch:
            return self._deny(
                schedule, Decision.DENIED_STALE_AUTHORITY, logical_tick
            )
        if grant.policy_revision != snapshot.policy_revision:
            return self._deny(schedule, Decision.DENIED_STALE_POLICY, logical_tick)
        if logical_tick >= grant.expires_at_tick:
            return self._deny(schedule, Decision.DENIED_EXPIRED, logical_tick)
        if (
            approval is None
            or approval.schedule_id != schedule.schedule_id
            or approval.action_id != schedule.action_id
            or approval.nonce != grant.nonce
            or logical_tick >= approval.expires_at_tick
        ):
            return self._deny(schedule, Decision.DENIED_OPERATOR, logical_tick)
        return self._sink.commit_atomically(schedule, grant, logical_tick)

    def _deny(
        self, schedule: Schedule, decision: Decision, logical_tick: int
    ) -> Decision:
        if self._sink is not None:
            self._sink.record_gate_denial(schedule, decision, logical_tick)
        return decision


@dataclass(frozen=True, slots=True)
class SimulationReport:
    mode: str
    schedules: int
    warmup_commits: int
    race_commits: int
    post_revoke_replays: int
    stale_commits_after_revoke_ack: int
    runtime_certified: bool


def run_stress_simulation(iterations: int = 500) -> SimulationReport:
    if iterations < 1:
        raise ValueError("iterations debe ser positivo")

    identities = SyntheticIdentityProvider()
    authority = SyntheticAuthority()
    sink = SyntheticFencedSink()
    coordinator = FailClosedCoordinator(identities, authority, sink)

    warmup_schedule, warmup_token, warmup_grant, warmup_approval = _register_case(
        "warmup", identities, authority, sink
    )
    warmup_result = coordinator.fire(
        warmup_schedule, warmup_token, warmup_grant, warmup_approval, 1
    )
    if warmup_result is not Decision.COMMITTED:
        raise AssertionError("warm-up sintético no produjo el commit esperado")
    authority.advance_epoch(
        warmup_schedule.owner_subject, warmup_schedule.branch_id, 2
    )
    warmup_ack = sink.advance_fence(warmup_schedule.branch_id, 2, 2)
    warmup_replay = coordinator.fire(
        warmup_schedule, warmup_token, warmup_grant, warmup_approval, 3
    )
    if warmup_replay is not Decision.DENIED_STALE_AUTHORITY:
        raise AssertionError("el warm-up permitió un replay tras revocar")

    race_commits = 0
    post_revoke_replays = 0
    stale_commits_after_ack = 0
    with ThreadPoolExecutor(max_workers=2) as pool:
        for index in range(iterations):
            suffix = f"race-{index}"
            schedule, token, grant, approval = _register_case(
                suffix, identities, authority, sink
            )
            barrier = Barrier(3)
            fire_future = pool.submit(
                _fire_after_barrier,
                barrier,
                coordinator,
                schedule,
                token,
                grant,
                approval,
            )
            revoke_future = pool.submit(
                _revoke_after_barrier,
                barrier,
                authority,
                sink,
                schedule,
            )
            barrier.wait(timeout=5)
            decision = fire_future.result(timeout=5)
            revoke_ack = revoke_future.result(timeout=5)
            branch_events = sink.events_for_branch(schedule.branch_id)
            commits = tuple(
                event for event in branch_events if event.kind == "EFFECT_COMMITTED"
            )
            if any(event.sequence >= revoke_ack.sequence for event in commits):
                stale_commits_after_ack += 1
            if decision is Decision.COMMITTED:
                race_commits += 1
                if len(commits) != 1 or commits[0].sequence >= revoke_ack.sequence:
                    raise AssertionError("commit posterior al acuse de revocación")
            elif commits:
                raise AssertionError("el sink mutó tras rechazar el despacho")

            replay = coordinator.fire(
                schedule, token, grant, approval, 10 + index
            )
            post_revoke_replays += 1
            if replay is not Decision.DENIED_STALE_AUTHORITY:
                raise AssertionError("replay obsoleto aceptado tras el acuse")
            if any(
                event.kind == "EFFECT_COMMITTED"
                and event.sequence >= revoke_ack.sequence
                for event in sink.events_for_branch(schedule.branch_id)
            ):
                stale_commits_after_ack += 1

    if warmup_ack.sequence <= 0 or stale_commits_after_ack != 0:
        raise AssertionError("invariante de fence sintético incumplida")
    return SimulationReport(
        mode="SIMULATION_ONLY",
        schedules=iterations,
        warmup_commits=1,
        race_commits=race_commits,
        post_revoke_replays=post_revoke_replays,
        stale_commits_after_revoke_ack=stale_commits_after_ack,
        runtime_certified=False,
    )


def _register_case(
    suffix: str,
    identities: SyntheticIdentityProvider,
    authority: SyntheticAuthority,
    sink: SyntheticFencedSink,
) -> tuple[Schedule, str, SyntheticGrant, SyntheticOperatorApproval]:
    subject = f"synthetic-subject-{suffix}"
    branch_id = f"synthetic-branch-{suffix}"
    schedule = Schedule(
        schedule_id=f"synthetic-schedule-{suffix}",
        owner_subject=subject,
        branch_id=branch_id,
        checkpoint_id=f"checkpoint-{suffix}-1",
        action_id=f"action-{suffix}",
    )
    token = f"synthetic-token-{suffix}"
    identities.register(
        token,
        SyntheticPrincipal(
            subject=subject,
            roles=frozenset({DISPATCH_ROLE}),
            branches=frozenset({branch_id}),
        ),
    )
    authority.register(subject, branch_id, AuthoritySnapshot(1, "policy-v1"))
    sink.register_schedule(schedule, minimum_epoch=1)
    grant = SyntheticGrant(
        principal_subject=subject,
        schedule_id=schedule.schedule_id,
        branch_id=branch_id,
        checkpoint_id=schedule.checkpoint_id,
        action_id=schedule.action_id,
        authority_epoch=1,
        policy_revision="policy-v1",
        nonce=f"nonce-{suffix}",
        expires_at_tick=10_000,
    )
    approval = SyntheticOperatorApproval(
        schedule_id=schedule.schedule_id,
        action_id=schedule.action_id,
        nonce=grant.nonce,
        expires_at_tick=10_000,
    )
    return schedule, token, grant, approval


def _fire_after_barrier(
    barrier: Barrier,
    coordinator: FailClosedCoordinator,
    schedule: Schedule,
    token: str,
    grant: SyntheticGrant,
    approval: SyntheticOperatorApproval,
) -> Decision:
    barrier.wait(timeout=5)
    return coordinator.fire(schedule, token, grant, approval, 4)


def _revoke_after_barrier(
    barrier: Barrier,
    authority: SyntheticAuthority,
    sink: SyntheticFencedSink,
    schedule: Schedule,
) -> SinkEvent:
    barrier.wait(timeout=5)
    new_epoch = 2
    authority.advance_epoch(schedule.owner_subject, schedule.branch_id, new_epoch)
    return sink.advance_fence(schedule.branch_id, new_epoch, 5)


def main() -> int:
    report = run_stress_simulation()
    print(json.dumps(asdict(report), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
