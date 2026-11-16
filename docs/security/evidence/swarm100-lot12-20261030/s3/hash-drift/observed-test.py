"""Lot 12 S3: temporary SQLite, in-memory consumers and controlled tasks only."""
from __future__ import annotations

import asyncio
import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import aiosqlite

import pytest

from babylon60.bft import bounty_pipeline_orchestrator as bounty
from babylon60.bft.master_ledger_queue import MasterLedgerQueue
from babylon60.core.moskv_kernel import Moskv1Kernel

ROOT = Path(__file__).resolve().parents[1]
DAG_PATH = ROOT / "02_EDIN_SWARMS/agents_archi/orchestrator/kda_dag_swarm.py"
spec = importlib.util.spec_from_file_location("lot12_s3_dag", DAG_PATH)
assert spec and spec.loader
dag = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dag
spec.loader.exec_module(dag)


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    def no_kill(*_args: object) -> None:
        raise AssertionError("No process termination allowed in regression fixtures")
    monkeypatch.setattr("babylon60.core.moskv_kernel.os.kill", no_kill)


@pytest.mark.asyncio
async def test_c0434_shutdown_drains_already_accepted(tmp_path: Path) -> None:
    path = tmp_path / "aux.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE entries (id INTEGER PRIMARY KEY)")
    queue = MasterLedgerQueue(str(path))
    await queue.initialize()
    for i in range(40):
        await queue.submit_transaction("INSERT INTO entries VALUES (?)", (i,))
    await asyncio.wait_for(queue.shutdown(), 3)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM entries").fetchone()[0] == 40
    assert queue.queue.empty()


def pipeline(domain: object, accepted: bool = False) -> tuple[bounty.BountyPipelineOrchestrator, list[object]]:
    obj: Any = object.__new__(bounty.BountyPipelineOrchestrator)
    result = SimpleNamespace(risk_score=0.99, contract_address="fixture-contract", advisory_id="fixture-advisory",
                             findings=["synthetic"], vulnerability_class=SimpleNamespace(value="synthetic"),
                             affected_subsystems=["fixture"], taint_level="TEST", to_dict=lambda: {"synthetic": True})
    receipts: list[object] = []
    obj.transducer = SimpleNamespace()
    ffi = SimpleNamespace(read=lambda: None, is_native=False, is_halted=lambda: False,
                          manifest=SimpleNamespace(epoch_id=1, seq=2))
    obj.dispatcher = SimpleNamespace(drain_domain=lambda d: [b"fixture"] if d == domain else [],
                                    get_queue_depths=lambda: {}, ffi_writer=ffi)
    worker = SimpleNamespace(process_advisories=lambda _: [result])
    obj.defi_scraper = obj.webkit_connector = obj.ai_sentinel = worker
    receipt = SimpleNamespace(claim_id="synthetic-receipt", to_dict=lambda: {"claim_id": "synthetic-receipt"})
    obj.attester = SimpleNamespace(generate_receipt=lambda **_: receipt)
    def enqueue(value: object) -> bool:
        receipts.append(value)
        return accepted
    obj.cold_ledger = SimpleNamespace(enqueue_receipt=enqueue)
    return obj, receipts


@pytest.mark.asyncio
@pytest.mark.parametrize("domain", [bounty.BountyDomain.DOMAIN_EVM, bounty.BountyDomain.DOMAIN_NATIVE, bounty.BountyDomain.DOMAIN_AI])
async def test_c0358_rejected_enqueue_propagates(domain: object) -> None:
    obj, attempts = pipeline(domain)
    with pytest.raises(RuntimeError, match="reject"):
        await obj.execute_cycle()
    assert len(attempts) == 1


@pytest.mark.asyncio
async def test_c0208_queued_claims_use_committed_predecessor(tmp_path: Path) -> None:
    kernel = Moskv1Kernel(str(tmp_path / "claims.sqlite"))
    tracking = [await kernel.ingest_entropy({"fixture": n}) for n in range(2)]
    for _ in tracking:
        claim = kernel._write_queue.get_nowait()
        await kernel._process_claim(claim)
        kernel._write_queue.task_done()
    with sqlite3.connect(kernel.db_path) as conn:
        rows = conn.execute("SELECT claim_id,prev_hash,current_hash FROM master_ledger ORDER BY lamport_t").fetchall()
    assert [r[0] for r in rows] == tracking
    assert rows[0][1] == "0" * 64
    assert rows[1][1] == rows[0][2]


@pytest.mark.asyncio
async def test_c0509_failed_dag_awaits_sibling_before_unlock(tmp_path: Path) -> None:
    scheduler = dag.KahnDagSwarmScheduler(2)
    memory = dag.KdaSwarmMemory()
    lock_path = tmp_path / "dag.lock"
    started = asyncio.Event()
    ended = asyncio.Event()
    lock_at_cleanup: list[bool] = []
    siblings: list[asyncio.Task[object]] = []
    async def sibling(_memory: object) -> None:
        current = asyncio.current_task()
        assert current
        siblings.append(current)
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            lock_at_cleanup.append(lock_path.exists())
            ended.set()
    async def fail(_memory: object) -> None:
        await started.wait()
        raise RuntimeError("fixture failure")
    scheduler.add_node(dag.SwarmDagNode("sibling", [], sibling))
    scheduler.add_node(dag.SwarmDagNode("fail", [], fail))
    try:
        with pytest.raises(RuntimeError, match="fixture failure"):
            await asyncio.wait_for(scheduler.execute_dag(memory, str(lock_path)), 3)
        assert ended.is_set(), "Sibling remains alive after lock release"
        assert lock_at_cleanup == [True]
        assert not lock_path.exists()
    finally:
        for task in siblings:
            task.cancel()
        await asyncio.gather(*siblings, return_exceptions=True)


@pytest.mark.asyncio
async def test_queue_failure_rolls_back_and_shutdown_reports_it(tmp_path: Path) -> None:
    path = tmp_path / "failed.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE entries (id INTEGER PRIMARY KEY)")
    queue = MasterLedgerQueue(str(path))
    await queue.initialize()
    await queue.submit_transaction("INSERT INTO entries VALUES (?)", (1,))
    await queue.submit_transaction("INVALID SQL", ())
    await queue.submit_transaction("INSERT INTO entries VALUES (?)", (2,))
    with pytest.raises(RuntimeError, match="shutdown did not confirm persistence"):
        await asyncio.wait_for(queue.shutdown(), 3)
    assert len(queue.failed_transactions) == 3
    assert queue.db is None
    await asyncio.wait_for(queue.queue.join(), 1)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM entries").fetchone()[0] == 0
    with pytest.raises(RuntimeError, match="Zombie Writer Prevention"):
        await queue.submit_transaction("SELECT 1")


@pytest.mark.asyncio
async def test_queue_full_and_cancelled_shutdown_caller(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "backlog.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE entries (id INTEGER PRIMARY KEY)")
    queue = MasterLedgerQueue(str(path))
    queue.queue = asyncio.Queue(maxsize=3)
    await queue.initialize()
    assert queue.db
    original = queue.db.execute
    started, release = asyncio.Event(), asyncio.Event()
    async def blocked_execute(sql: str, *args: object, **kwargs: object) -> object:
        if sql == "BEGIN IMMEDIATE" and not started.is_set():
            started.set()
            await release.wait()
        return await original(sql, *args, **kwargs)
    monkeypatch.setattr(queue.db, "execute", blocked_execute)
    await queue.submit_transaction("INSERT INTO entries VALUES (?)", (0,))
    await started.wait()
    for i in range(1, 4):
        await queue.submit_transaction("INSERT INTO entries VALUES (?)", (i,))
    with pytest.raises(asyncio.QueueFull):
        await queue.submit_transaction("INSERT INTO entries VALUES (?)", (9,))
    caller = asyncio.create_task(queue.shutdown())
    await asyncio.sleep(0)
    with pytest.raises(RuntimeError, match="not accepting"):
        await queue.submit_transaction("SELECT 1")
    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await caller
    release.set()
    await asyncio.wait_for(queue.shutdown(), 3)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT id FROM entries ORDER BY id").fetchall() == [(0,), (1,), (2,), (3,)]
    await asyncio.wait_for(queue.queue.join(), 1)


@pytest.mark.asyncio
async def test_queue_lifecycle_rejects_unstarted_closed_and_duplicate_init(tmp_path: Path) -> None:
    queue = MasterLedgerQueue(str(tmp_path / "lifecycle.sqlite"))
    with pytest.raises(RuntimeError, match="not accepting"):
        await queue.submit_transaction("SELECT 1")
    await queue.initialize()
    with pytest.raises(RuntimeError, match="already initialized"):
        await queue.initialize()
    await asyncio.gather(queue.shutdown(), queue.shutdown())
    with pytest.raises(RuntimeError):
        await queue.submit_transaction("SELECT 1")
    with pytest.raises(RuntimeError, match="closed"):
        await queue.initialize()


@pytest.mark.asyncio
async def test_queue_repeated_bursts_preserve_every_accepted_row(tmp_path: Path) -> None:
    for iteration in range(8):  # Three warmup rounds, five checked bursts.
        path = tmp_path / f"burst-{iteration}.sqlite"
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE entries (id INTEGER PRIMARY KEY)")
        queue = MasterLedgerQueue(str(path))
        await queue.initialize()
        for i in range(1000):
            await queue.submit_transaction("INSERT INTO entries VALUES (?)", (i,))
        await asyncio.wait_for(queue.shutdown(), 5)
        with sqlite3.connect(path) as conn:
            assert conn.execute("SELECT count(*),sum(id) FROM entries").fetchone() == (1000, 499500)


@pytest.mark.asyncio
@pytest.mark.parametrize("domain", [bounty.BountyDomain.DOMAIN_EVM, bounty.BountyDomain.DOMAIN_NATIVE, bounty.BountyDomain.DOMAIN_AI])
async def test_pipeline_success_reports_admission_only(domain: object) -> None:
    obj, attempts = pipeline(domain, accepted=True)
    report = await obj.execute_cycle()
    assert len(report.claim_receipts) == len(attempts) == 1
    assert report.to_dict()["receipt_persistence_status"] == "QUEUED_NOT_CONFIRMED"


@pytest.mark.asyncio
async def test_pipeline_worker_exception_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    obj, _ = pipeline(bounty.BountyDomain.DOMAIN_EVM)
    def failed(_receipt: object) -> bool:
        raise OSError("synthetic persistence failure")
    monkeypatch.setattr(obj.cold_ledger, "enqueue_receipt", failed)
    with pytest.raises(OSError, match="synthetic persistence failure"):
        await obj.execute_cycle()


@pytest.mark.asyncio
async def test_kernel_concurrent_instances_and_restart_keep_chain(tmp_path: Path) -> None:
    path = tmp_path / "multi.sqlite"
    kernels = [Moskv1Kernel(str(path)), Moskv1Kernel(str(path))]
    accepted: list[str] = []
    for n in range(6):
        accepted.extend(await asyncio.gather(*(k.ingest_entropy({"source": i, "n": n}) for i, k in enumerate(kernels))))
    assert len(set(accepted)) == 12
    async def drain(kernel: Moskv1Kernel) -> None:
        while not kernel._write_queue.empty():
            claim = kernel._write_queue.get_nowait()
            await kernel._process_claim(claim)
            kernel._write_queue.task_done()
    await asyncio.gather(*(drain(k) for k in kernels))
    restarted = Moskv1Kernel(str(path))
    accepted.append(await restarted.ingest_entropy({"restarted": True}))
    await drain(restarted)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT claim_id,prev_hash,current_hash,lamport_t FROM master_ledger ORDER BY lamport_t").fetchall()
    assert {r[0] for r in rows} == set(accepted)
    prev = "0" * 64
    for row in rows:
        assert row[1] == prev
        prev = row[2]
    assert len({r[3] for r in rows}) == 13


@pytest.mark.asyncio
async def test_kernel_replay_missing_id_conflict_and_payload_snapshot(tmp_path: Path) -> None:
    kernel = Moskv1Kernel(str(tmp_path / "replay.sqlite"))
    payload = {"values": [1]}
    await kernel.ingest_entropy(payload)
    claim = kernel._write_queue.get_nowait()
    payload["values"].append(2)
    assert claim.payload == {"values": [1]}
    with pytest.raises(ValueError, match="absent"):
        await kernel._verify_idempotency_collision(claim)
    await kernel._process_claim(claim)
    await kernel._process_claim(claim)
    claim.payload = {"different": True}
    with pytest.raises(ValueError, match="different payload"):
        await kernel._process_claim(claim)
    with sqlite3.connect(kernel.db_path) as conn:
        assert conn.execute("SELECT count(*) FROM master_ledger").fetchone()[0] == 1
    kernel._write_queue.task_done()


@pytest.mark.asyncio
async def test_kernel_stop_drains_and_rejects_new_or_invalid_claims(tmp_path: Path) -> None:
    kernel = Moskv1Kernel(str(tmp_path / "stop.sqlite"))
    with pytest.raises(ValueError, match="confidence"):
        await kernel.ingest_entropy({"bad": True}, confidence="C1")
    accepted = [await kernel.ingest_entropy({"n": n}) for n in range(20)]
    kernel.stop()
    with pytest.raises(RuntimeError, match="not accepted"):
        await kernel.ingest_entropy({"late": True})
    await asyncio.wait_for(kernel.bft_state_loop(), 3)
    await asyncio.wait_for(kernel._write_queue.join(), 1)
    with sqlite3.connect(kernel.db_path) as conn:
        assert conn.execute("SELECT count(*) FROM master_ledger").fetchone()[0] == len(accepted)


@pytest.mark.asyncio
async def test_dag_repeated_cancellation_does_not_release_during_cleanup(tmp_path: Path) -> None:
    scheduler = dag.KahnDagSwarmScheduler(1)
    lock_path = tmp_path / "cancel.lock"
    started, cleaning, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    async def stubborn(_memory: object) -> None:
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaning.set()
            await release.wait()
            assert lock_path.exists()
    scheduler.add_node(dag.SwarmDagNode("work", [], stubborn))
    caller = asyncio.create_task(scheduler.execute_dag(dag.KdaSwarmMemory(), str(lock_path)))
    await started.wait()
    caller.cancel()
    await cleaning.wait()
    caller.cancel()
    await asyncio.sleep(0)
    assert lock_path.exists()
    assert not caller.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(caller, 3)
    assert not lock_path.exists()


@pytest.mark.asyncio
async def test_dag_warmup_failures_leave_no_siblings(tmp_path: Path) -> None:
    for iteration in range(8):
        scheduler = dag.KahnDagSwarmScheduler(8)
        started = asyncio.Event()
        finished: list[str] = []
        path = tmp_path / f"warm-{iteration}.lock"
        async def pending(_memory: object) -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                assert path.exists()
                finished.append("done")
        async def broken(_memory: object) -> None:
            await started.wait()
            raise ValueError("fixture failure")
        for i in range(7):
            scheduler.add_node(dag.SwarmDagNode(str(i), [], pending))
        scheduler.add_node(dag.SwarmDagNode("broken", [], broken))
        with pytest.raises(ValueError, match="fixture failure"):
            await scheduler.execute_dag(dag.KdaSwarmMemory(), str(path))
        assert len(finished) == 7
        assert not path.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel_initializing", [False, True])
async def test_queue_close_or_cancel_during_initialization_cannot_reopen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cancel_initializing: bool
) -> None:
    from babylon60.bft import master_ledger_queue as module
    original = module.database_core.connect
    connected, release = asyncio.Event(), asyncio.Event()
    connections: list[aiosqlite.Connection] = []
    async def paused_connect(*args: Any, **kwargs: Any) -> aiosqlite.Connection:
        connection = await original(*args, **kwargs)
        connections.append(connection)
        connected.set()
        await release.wait()
        return connection
    monkeypatch.setattr(module.database_core, "connect", paused_connect)
    queue = MasterLedgerQueue(str(tmp_path / "init.sqlite"))
    initializing = asyncio.create_task(queue.initialize())
    await asyncio.wait_for(connected.wait(), 2)
    with pytest.raises(RuntimeError, match="already initialized"):
        await queue.initialize()
    if cancel_initializing:
        initializing.cancel()
        with pytest.raises(asyncio.CancelledError):
            await initializing
    closing = asyncio.create_task(queue.shutdown())
    await asyncio.sleep(0)
    release.set()
    await asyncio.wait_for(asyncio.gather(initializing, closing, return_exceptions=True), 2)
    assert queue.db is None
    assert queue._writer_task is None
    with pytest.raises(RuntimeError, match="not accepting"):
        await queue.submit_transaction("SELECT 1")
    # The real fixture connection created before cancellation has been closed.
    with pytest.raises(ValueError, match="no active connection"):
        await connections[0].execute("SELECT 1")


@pytest.mark.asyncio
async def test_kernel_cancelled_claim_processing_propagates_cancellation(tmp_path: Path) -> None:
    kernel = Moskv1Kernel(str(tmp_path / "cancel-claim.sqlite"))
    await kernel.ingest_entropy({"fixture": "cancelled"})
    extracted = asyncio.Event()
    async def paused_insert(_claim: object) -> None:
        extracted.set()
        await asyncio.Event().wait()
    kernel._insert_claim_db = paused_insert
    processing = asyncio.create_task(kernel.bft_state_loop())
    await asyncio.wait_for(extracted.wait(), 2)
    processing.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(processing, 2)
    with sqlite3.connect(kernel.db_path) as conn:
        assert conn.execute("SELECT count(*) FROM master_ledger").fetchone()[0] == 0
