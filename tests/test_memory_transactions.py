"""Atomicity and serialization with real SQLite WAL connections and fault triggers."""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import pytest

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger
from babylon60.memory.governance import (
    GovernanceViolationError,
    MemoryGovernanceEngine,
    MemoryStatus,
    SignatureVerificationError,
    TenantIsolationError,
    TrustLevel,
)


class ObservedEngine(MemoryGovernanceEngine):
    """Use SQLite's trace hook for scheduling; storage and transactions stay real."""

    observe: Callable[[str], None] | None = None

    def _get_connection(self) -> sqlite3.Connection:
        conn = super()._get_connection()
        if self.observe is not None:
            conn.set_trace_callback(self.observe)
        return conn


class SqlGate:
    def __init__(self, fragment: str, *, pause: bool = True) -> None:
        self.fragment = fragment
        self.reached = threading.Event()
        self.release = threading.Event()
        self.timed_out = False
        if not pause:
            self.release.set()

    def __call__(self, sql: str) -> None:
        if self.fragment in sql and not self.reached.is_set():
            self.reached.set()
            self.timed_out = not self.release.wait(10)

    def wait(self) -> None:
        assert self.reached.wait(5), f"SQL not reached: {self.fragment}"


def open_engine(path: Path) -> ObservedEngine:
    engine = ObservedEngine(path)
    for tenant in ("alpha", "beta", "gamma"):
        engine.register_principal_key(tenant, "root", b"test-key-0123456789abcdef")
    return engine


@pytest.fixture
def engine(tmp_path: Path) -> ObservedEngine:
    return open_engine(tmp_path / "memory.db")


def add(engine: MemoryGovernanceEngine, **kwargs: Any) -> Any:
    return engine.add_record(tenant_id="alpha", principal="root", content="memory", **kwargs)


def snapshot(path: Path) -> dict[str, list[tuple[object, ...]]]:
    tables = (
        "cortex_ledger",
        "sqlite_sequence",
        "cortex_memory_records",
        "cortex_memory_blobs",
        "cortex_memory_edges",
        "cortex_tenant_grants",
        "cortex_disbelief_proofs",
    )
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("BEGIN")
        return {table: conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall() for table in tables}


def execute(path: Path, sql: str) -> None:
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(sql)


@pytest.mark.parametrize("existing_memory", [False, True])
def test_rejects_separate_ledger_before_mutating_memory(tmp_path: Path, existing_memory: bool) -> None:
    path = tmp_path / "memory.db"
    ledger = CortexPersistLedger(tmp_path / "other.db")
    before = None
    if existing_memory:
        add(open_engine(path))
        before = snapshot(path)
    with pytest.raises(GovernanceViolationError, match="same database"):
        MemoryGovernanceEngine(path, ledger=ledger)
    assert ledger.query_events() == []
    if existing_memory:
        assert snapshot(path) == before
    else:
        assert not path.exists()


def test_injected_ledger_accepts_alias_of_same_database(tmp_path: Path) -> None:
    path = tmp_path / "memory.db"
    ledger = CortexPersistLedger(path)
    alias = tmp_path / "alias.db"
    alias.symlink_to(path)
    engine = MemoryGovernanceEngine(alias, ledger=ledger)
    engine.register_principal_key("alpha", "root", b"test-key-0123456789abcdef")
    record = add(engine)
    assert record.tx_lamport_t == 1
    payload = ledger.query_events()[0]["payload"]
    assert isinstance(payload, dict)
    assert payload["record_id"] == record.record_id
    assert ledger.verify_integrity()


@pytest.mark.parametrize(
    "stage, trigger",
    [
        ("ledger", "AFTER INSERT ON cortex_ledger"),
        ("supersession", "AFTER UPDATE ON cortex_memory_records"),
        ("record", "AFTER INSERT ON cortex_memory_records"),
        ("blob", "AFTER INSERT ON cortex_memory_blobs"),
        ("supersedes", "AFTER INSERT ON cortex_memory_edges WHEN NEW.edge_kind = 'SUPERSEDES'"),
        ("parent", "AFTER INSERT ON cortex_memory_edges WHEN NEW.edge_kind = 'DERIVES_FROM'"),
        ("dependency", "AFTER INSERT ON cortex_memory_edges WHEN NEW.edge_kind = 'DEPENDS_ON'"),
    ],
)
def test_add_failure_rolls_back_every_table_and_tick(engine: ObservedEngine, stage: str, trigger: str) -> None:
    previous = add(engine, subject_key="configuration")
    child = add(engine, parents=[previous.record_id])
    premise = add(engine)
    before = snapshot(engine.db_path)
    candidate = str(uuid4())
    execute(engine.db_path, f"CREATE TRIGGER inject_failure {trigger} BEGIN SELECT RAISE(ABORT, 'fault:{stage}'); END")
    kwargs = dict(
        record_id=candidate,
        subject_key="configuration",
        parents=[premise.record_id],
        depends_on=[premise.record_id],
        trust_level=TrustLevel.SOVEREIGN,
    )
    with pytest.raises(sqlite3.IntegrityError, match=f"fault:{stage}"):
        add(engine, **kwargs)
    assert snapshot(engine.db_path) == before
    assert engine.get_record(child.record_id, tenant_id="alpha").status == MemoryStatus.ACTIVE
    execute(engine.db_path, "DROP TRIGGER inject_failure")
    record = add(engine, **kwargs)
    assert record.tx_lamport_t == premise.tx_lamport_t + 1
    assert engine.ledger.verify_integrity()
    reopened = open_engine(engine.db_path)
    assert reopened.get_record(candidate, tenant_id="alpha") == record
    assert reopened.get_record(child.record_id, tenant_id="alpha", include_inactive=True).status == MemoryStatus.STALE


def test_projection_failure_is_inside_the_write_transaction(engine: ObservedEngine) -> None:
    before = snapshot(engine.db_path)
    execute(
        engine.db_path,
        """CREATE TRIGGER corrupt_signature AFTER INSERT ON cortex_memory_records
        BEGIN UPDATE cortex_memory_records SET signature = 'corrupt' WHERE record_id = NEW.record_id; END""",
    )
    with pytest.raises(SignatureVerificationError, match="Signature tampering"):
        add(engine)
    assert snapshot(engine.db_path) == before
    execute(engine.db_path, "DROP TRIGGER corrupt_signature")
    assert add(engine).tx_lamport_t == 1


@pytest.mark.parametrize("edge", ["parents", "depends_on"])
def test_cross_tenant_derivation_requires_specific_grant_and_revocation_removes_it(
    engine: ObservedEngine,
    edge: str,
) -> None:
    root = add(engine)
    before = snapshot(engine.db_path)

    def derive(tenant: str = "beta") -> Any:
        return engine.add_record(
            tenant_id=tenant,
            principal="root",
            content="derived",
            parents=[root.record_id] if edge == "parents" else (),
            depends_on=[root.record_id] if edge == "depends_on" else (),
        )

    with pytest.raises(TenantIsolationError):
        derive()
    assert snapshot(engine.db_path) == before
    engine.grant_cross_tenant_read(
        owner_tenant="alpha", grantee_tenant="beta", record_id=root.record_id, principal="root"
    )
    before = snapshot(engine.db_path)
    with pytest.raises(TenantIsolationError):
        derive("gamma")
    assert snapshot(engine.db_path) == before
    derived = derive()
    leaf = engine.add_record(tenant_id="beta", principal="root", content="leaf", depends_on=[derived.record_id])
    receipt = engine.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")
    revoked = receipt["revoked_dependents"]
    assert isinstance(revoked, list)
    assert set(revoked) == {derived.record_id, leaf.record_id}
    state = snapshot(engine.db_path)
    assert state["cortex_memory_blobs"] == state["cortex_tenant_grants"] == []
    for record in (derived, leaf):
        view = engine.get_record(record.record_id, tenant_id="beta", include_inactive=True)
        assert view.status == MemoryStatus.REVOKED_DEPENDENCY
        assert view.content is None
    with pytest.raises(TenantIsolationError):
        engine.get_record(root.record_id, tenant_id="beta", include_inactive=True)
    with pytest.raises(GovernanceViolationError):
        derive()
    assert snapshot(engine.db_path) == state
    assert engine.ledger.verify_integrity()


def test_revocation_failure_restores_blobs_grants_status_and_receipt(engine: ObservedEngine) -> None:
    root = add(engine)
    add(engine, depends_on=[root.record_id])
    engine.grant_cross_tenant_read(
        owner_tenant="alpha", grantee_tenant="beta", record_id=root.record_id, principal="root"
    )
    before = snapshot(engine.db_path)
    execute(
        engine.db_path,
        """CREATE TRIGGER fail_revoke AFTER DELETE ON cortex_tenant_grants
        BEGIN SELECT RAISE(ABORT, 'revocation failure'); END""",
    )
    with pytest.raises(sqlite3.IntegrityError, match="revocation failure"):
        engine.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")
    assert snapshot(engine.db_path) == before
    assert engine.get_record(root.record_id, tenant_id="beta").content == "memory"
    execute(engine.db_path, "DROP TRIGGER fail_revoke")
    receipt = engine.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")
    assert receipt["lamport_t"] == 3
    assert engine.ledger.verify_integrity()


@pytest.mark.parametrize("fail", [False, True])
def test_other_connections_cannot_see_partial_add(engine: ObservedEngine, fail: bool) -> None:
    previous = add(engine, subject_key="setting")
    reader = open_engine(engine.db_path)
    before = snapshot(engine.db_path)
    if fail:
        execute(
            engine.db_path,
            """CREATE TRIGGER fail_blob BEFORE INSERT ON cortex_memory_blobs
            BEGIN SELECT RAISE(ABORT, 'blob failure'); END""",
        )
    gate = SqlGate("INSERT INTO cortex_memory_blobs")
    engine.observe = gate
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(add, engine, subject_key="setting")
        try:
            gate.wait()  # Ledger, supersession and record writes have executed.
            assert snapshot(engine.db_path) == before
            assert reader.get_record(previous.record_id, tenant_id="alpha").status == MemoryStatus.ACTIVE
        finally:
            gate.release.set()
        if fail:
            with pytest.raises(sqlite3.IntegrityError):
                future.result(timeout=10)
            assert snapshot(engine.db_path) == before
        else:
            committed = future.result(timeout=10)
            assert reader.get_record(committed.record_id, tenant_id="alpha") == committed
    assert not gate.timed_out


@pytest.mark.parametrize("first", ["add", "revoke"])
@pytest.mark.parametrize("edge", ["parents", "depends_on"])
@pytest.mark.parametrize("cross_tenant", [False, True])
def test_derivation_and_revocation_serialize_under_contention(
    engine: ObservedEngine,
    first: str,
    edge: str,
    cross_tenant: bool,
) -> None:
    root = add(engine)
    tenant = "beta" if cross_tenant else "alpha"
    if cross_tenant:
        engine.grant_cross_tenant_read(
            owner_tenant="alpha", grantee_tenant=tenant, record_id=root.record_id, principal="root"
        )
    other = open_engine(engine.db_path)
    before = snapshot(engine.db_path)
    gate = SqlGate("INSERT INTO cortex_ledger")
    contended = SqlGate("BEGIN IMMEDIATE", pause=False)
    engine.observe, other.observe = gate, contended
    candidate = str(uuid4())

    def derive(target):
        return target.add_record(
            record_id=candidate, tenant_id=tenant, principal="root", content="derived", **{edge: [root.record_id]}
        )

    def revoke(target):
        return target.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")

    operations = (derive, revoke) if first == "add" else (revoke, derive)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first_result = pool.submit(operations[0], engine)
        try:
            gate.wait()
            second_result = pool.submit(operations[1], other)
            contended.wait()
            assert snapshot(engine.db_path) == before
        finally:
            gate.release.set()
        first_result.result(timeout=10)
        if first == "revoke":
            with pytest.raises(GovernanceViolationError):
                second_result.result(timeout=10)
            with pytest.raises(KeyError):
                other.get_record(candidate, tenant_id=tenant, include_inactive=True)
        else:
            receipt = second_result.result(timeout=10)
            assert receipt["revoked_dependents"] == [candidate]
            view = other.get_record(candidate, tenant_id=tenant, include_inactive=True)
            assert view.status == MemoryStatus.REVOKED_DEPENDENCY
            assert view.content is None
    state = snapshot(engine.db_path)
    assert state["cortex_memory_blobs"] == state["cortex_tenant_grants"] == []
    assert len(state["cortex_ledger"]) == (3 if first == "add" else 2)
    assert not gate.timed_out
    assert engine.ledger.verify_integrity()


def test_read_uses_one_snapshot_while_revocation_commits(engine: ObservedEngine) -> None:
    root = add(engine)
    engine.grant_cross_tenant_read(
        owner_tenant="alpha", grantee_tenant="beta", record_id=root.record_id, principal="root"
    )
    revoker = open_engine(engine.db_path)
    gate = SqlGate("SELECT 1 FROM cortex_tenant_grants")
    engine.observe = gate
    with ThreadPoolExecutor(max_workers=1) as pool:
        read = pool.submit(engine.get_record, root.record_id, tenant_id="beta")
        try:
            gate.wait()  # The record query has already established the read snapshot.
            revoker.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")
        finally:
            gate.release.set()
        assert read.result(timeout=10) == root
    with pytest.raises(TenantIsolationError):
        engine.get_record(root.record_id, tenant_id="beta", include_inactive=True)
    assert not gate.timed_out


def test_concurrent_duplicate_uuid_has_one_record_and_one_event(engine: ObservedEngine) -> None:
    other = open_engine(engine.db_path)
    barrier = threading.Barrier(2)
    candidate = str(uuid4())

    def insert(target):
        barrier.wait(timeout=5)
        try:
            return add(target, record_id=candidate)
        except GovernanceViolationError as exc:
            assert "Duplicate record_id" in str(exc)
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(insert, target) for target in (engine, other)]
        results = [future.result(timeout=10) for future in futures]
    assert sum(result is not None for result in results) == 1
    state = snapshot(engine.db_path)
    assert len(state["cortex_ledger"]) == len(state["cortex_memory_records"]) == len(state["cortex_memory_blobs"]) == 1
    assert add(engine).tx_lamport_t == 2
    assert engine.ledger.verify_integrity()


def test_policy_epoch_is_bound_once_even_when_write_waits(engine: ObservedEngine) -> None:
    gate = SqlGate("BEGIN IMMEDIATE")
    engine.observe = gate
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(add, engine)
        try:
            gate.wait()
            engine.advance_policy_epoch(2)
        finally:
            gate.release.set()
        record = pending.result(timeout=10)
    assert record.policy_epoch == 1
    payload = engine.ledger.query_events()[0]["payload"]
    assert isinstance(payload, dict)
    assert payload["policy_epoch"] == record.policy_epoch
    assert engine.get_record(record.record_id, tenant_id="alpha") == record
    assert add(engine).policy_epoch == 2
    assert not gate.timed_out


def test_add_revoke_stress_with_warmup(engine: ObservedEngine) -> None:
    """Two warmup rounds then 32 races of two writers against revocation."""
    writers = [open_engine(engine.db_path) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for iteration in range(2 + 32):
            root = add(engine)
            engine.grant_cross_tenant_read(
                owner_tenant="alpha", grantee_tenant="beta", record_id=root.record_id, principal="root"
            )
            start = threading.Barrier(3)

            def derive(writer, edge):
                start.wait(timeout=5)
                try:
                    return writer.add_record(
                        tenant_id="beta", principal="root", content=f"race {iteration}", **{edge: [root.record_id]}
                    )
                except GovernanceViolationError:
                    return None  # Revocation acquired the writer lock first.

            def revoke():
                start.wait(timeout=5)
                return engine.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")

            pending = [pool.submit(derive, writer, edge) for writer, edge in zip(writers, ("parents", "depends_on"))]
            revocation = pool.submit(revoke)
            inserted = [result for future in pending if (result := future.result(timeout=10)) is not None]
            receipt = revocation.result(timeout=10)
            assert set(receipt["revoked_dependents"]) == {record.record_id for record in inserted}
            for record in inserted:
                view = engine.get_record(record.record_id, tenant_id="beta", include_inactive=True)
                assert view.status == MemoryStatus.REVOKED_DEPENDENCY
                assert view.content is None
    state = snapshot(engine.db_path)
    assert state["cortex_memory_blobs"] == state["cortex_tenant_grants"] == []
    assert len(state["cortex_ledger"]) == len(state["cortex_memory_records"]) + 34
    assert engine.ledger.verify_integrity()


def test_revocation_closes_chain_beyond_legacy_depth_limit(engine: ObservedEngine) -> None:
    root = add(engine)
    parent = root
    for _ in range(1025):
        parent = add(engine, depends_on=[parent.record_id])
    receipt = engine.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")
    assert receipt["total_invalidated"] == 1026
    leaf = engine.get_record(parent.record_id, tenant_id="alpha", include_inactive=True)
    assert leaf.status == MemoryStatus.REVOKED_DEPENDENCY
    assert leaf.content is None
    assert snapshot(engine.db_path)["cortex_memory_blobs"] == []
    assert engine.ledger.verify_integrity()


def test_commit_failure_rolls_back_verified_record_and_ledger(engine: ObservedEngine) -> None:
    before = snapshot(engine.db_path)
    execute(
        engine.db_path,
        """CREATE TABLE deferred_guard (
        record_id TEXT REFERENCES cortex_memory_records(record_id) DEFERRABLE INITIALLY DEFERRED)""",
    )
    execute(
        engine.db_path,
        """CREATE TRIGGER fail_at_commit AFTER INSERT ON cortex_memory_blobs
        BEGIN INSERT INTO deferred_guard VALUES ('missing-record'); END""",
    )
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        add(engine)
    assert snapshot(engine.db_path) == before
    with closing(sqlite3.connect(engine.db_path)) as conn:
        assert conn.execute("SELECT * FROM deferred_guard").fetchall() == []
    execute(engine.db_path, "DROP TRIGGER fail_at_commit")
    assert add(engine).tx_lamport_t == 1


@pytest.mark.parametrize("operation", ["add", "revoke"])
def test_replacing_ledger_cannot_reintroduce_split_transactions(engine: ObservedEngine, operation: str) -> None:
    root = add(engine)
    before = snapshot(engine.db_path)
    engine.ledger = CortexPersistLedger(engine.db_path.parent / "replacement.db")
    with pytest.raises(ValueError, match="same database"):
        if operation == "add":
            add(engine)
        else:
            engine.revoke_record(record_id=root.record_id, tenant_id="alpha", principal="root")
    assert snapshot(engine.db_path) == before
    assert engine.ledger.query_events() == []
