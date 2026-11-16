"""Independent S3 controls: owned SQLite, deterministic tasks, inert consumers."""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from babylon60.bft import bounty_pipeline_orchestrator as pipeline_module
from babylon60.bft.master_ledger_queue import MasterLedgerQueue
from babylon60.bft import master_ledger_queue as queue_module
from babylon60.core.moskv_kernel import Moskv1Kernel
from babylon60.core.moskv_kernel import dbcore

ROOT = Path(__file__).absolute().parents[5]
spec = importlib.util.spec_from_file_location(
    "independent_lot12_dag", ROOT / "02_EDIN_SWARMS/agents_archi/orchestrator/kda_dag_swarm.py"
)
assert spec and spec.loader
dag = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dag
spec.loader.exec_module(dag)


@pytest.fixture(autouse=True)
def confined(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    def blocked_kill(*args):
        raise AssertionError("No signal to any process in independent fixtures")

    monkeypatch.setattr("babylon60.core.moskv_kernel.os.kill", blocked_kill)


@pytest.mark.asyncio
async def test_auxiliary_queue_counts_accepted_items_and_late_rejections(tmp_path):
    """Public producers, concurrent close callers, independently queried bytes."""
    for round_index in range(5):  # two warmup rounds, three checked rounds
        path = tmp_path / f"drain-{round_index}.sqlite"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE submitted (id INTEGER PRIMARY KEY, body BLOB)")
        queue = MasterLedgerQueue(str(path))
        queue.queue = asyncio.Queue(maxsize=4096)
        await queue.initialize()
        accepted = set()

        async def produce(offset):
            for ordinal in range(300):
                number = offset + ordinal
                await queue.submit_transaction("INSERT INTO submitted VALUES (?, ?)", (number, b"fixture\x00"))
                accepted.add(number)
                if ordinal % 17 == 0:
                    await asyncio.sleep(0)

        await asyncio.gather(*(produce(offset) for offset in (0, 1000, 2000)))
        await asyncio.wait_for(asyncio.gather(queue.shutdown(), queue.shutdown(), queue.shutdown()), 8)
        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT id,body FROM submitted").fetchall()
        assert {row[0] for row in rows} == accepted
        assert all(row[1] == b"fixture\x00" for row in rows)
        assert not queue.failed_transactions
        assert queue.db is None
        await asyncio.wait_for(queue.queue.join(), 1)
        with pytest.raises(RuntimeError):
            await queue.submit_transaction("INSERT INTO submitted VALUES (99999, NULL)")


@pytest.mark.asyncio
async def test_auxiliary_failed_batch_preserves_exact_admitted_backlog(tmp_path):
    path = tmp_path / "accounting.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE submitted (id INTEGER PRIMARY KEY)")
    queue = MasterLedgerQueue(str(path))
    queue.queue = asyncio.Queue(maxsize=1000)
    await queue.initialize()
    payloads = [("INSERT INTO submitted VALUES (?)", (i,)) for i in range(700)]
    # A single atomic first batch must roll back, later accepted items must be retained.
    payloads[120] = ("THIS IS DELIBERATELY INVALID SQL", ())
    for query, parameters in payloads:
        await queue.submit_transaction(query, parameters)
    with pytest.raises(RuntimeError, match="did not confirm persistence"):
        await asyncio.wait_for(queue.shutdown(), 5)
    assert list(queue.failed_transactions) == payloads
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM submitted").fetchone() == (0,)
    assert queue.queue.empty()
    await asyncio.wait_for(queue.queue.join(), 1)
    with pytest.raises(RuntimeError, match="did not confirm persistence"):
        await queue.shutdown()


@pytest.mark.asyncio
async def test_auxiliary_close_during_initialize_cannot_reopen_admission(tmp_path, monkeypatch):
    queue = MasterLedgerQueue(str(tmp_path / "initializing.sqlite"))
    original_connect = queue_module.database_core.connect
    connected, release = asyncio.Event(), asyncio.Event()

    async def paused_connect(*args, **kwargs):
        connection = await original_connect(*args, **kwargs)
        connected.set()
        await release.wait()
        return connection

    monkeypatch.setattr(queue_module.database_core, "connect", paused_connect)
    initializing = asyncio.create_task(queue.initialize())
    await asyncio.wait_for(connected.wait(), 2)
    closing = asyncio.create_task(queue.shutdown())
    await asyncio.sleep(0)
    release.set()
    try:
        await asyncio.wait_for(asyncio.gather(initializing, closing, return_exceptions=True), 2)
        with pytest.raises(RuntimeError):
            await queue.submit_transaction("SELECT 1")
        assert queue.db is None
    finally:
        writer = queue._writer_task
        if writer and not writer.done():
            writer.cancel()
            await asyncio.gather(writer, return_exceptions=True)
        if queue.db is not None:
            await queue.db.close()


@pytest.mark.asyncio
async def test_many_kernel_writers_recompute_every_persisted_hash(tmp_path):
    """Four stale ingestion snapshots enter real concurrent SQLite transactions."""
    path = tmp_path / "kernel.sqlite"
    kernels = [Moskv1Kernel(str(path)) for _ in range(4)]
    expected = set()
    for i, kernel in enumerate(kernels):
        for j in range(30):
            expected.add(await kernel.ingest_entropy({"writer": i, "step": j, "unicode": "á"}))

    async def drain(kernel):
        kernel.stop()
        await kernel.bft_state_loop()
        await kernel._write_queue.join()

    await asyncio.wait_for(asyncio.gather(*(drain(kernel) for kernel in kernels)), 15)
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT claim_id,payload,prev_hash,current_hash,lamport_t FROM master_ledger ORDER BY lamport_t"
        ).fetchall()
    assert {row[0] for row in rows} == expected
    assert len(rows) == len(expected) == 120
    previous = "0" * 64
    ticks = []
    for _, payload, predecessor, digest, tick in rows:
        assert predecessor == previous
        encoded = f"{predecessor}:{json.dumps(json.loads(payload), sort_keys=True)}:{tick}".encode()
        assert hashlib.sha3_256(encoded).hexdigest() == digest
        previous = digest
        ticks.append(tick)
    assert ticks == sorted(set(ticks))


@pytest.mark.asyncio
async def test_kernel_cancelled_processing_is_not_reported_as_normal_completion(tmp_path, monkeypatch):
    path = tmp_path / "cancelled-processing.sqlite"
    kernel = Moskv1Kernel(str(path))
    accepted = await kernel.ingest_entropy({"owned": "uncommitted claim"})
    entered = asyncio.Event()
    original_connect = dbcore.connect

    async def paused_connect(*args, **kwargs):
        connection = await original_connect(*args, **kwargs)
        original_execute = connection.execute

        async def execute(query, *params, **options):
            if query == "BEGIN IMMEDIATE":
                entered.set()
                await asyncio.Event().wait()
            return await original_execute(query, *params, **options)

        connection.execute = execute
        return connection

    monkeypatch.setattr(dbcore, "connect", paused_connect)
    processing = asyncio.create_task(kernel.bft_state_loop())
    await asyncio.wait_for(entered.wait(), 2)
    processing.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(processing, 2)
    with sqlite3.connect(path) as connection:
        assert not connection.execute("SELECT claim_id FROM master_ledger WHERE claim_id=?", (accepted,)).fetchall()


def pipeline_fixture(rejection_at):
    """Only compute/control flow is real; ledger/attester and dispatch are inert."""
    instance = object.__new__(pipeline_module.BountyPipelineOrchestrator)
    relevant = {
        pipeline_module.BountyDomain.DOMAIN_EVM,
        pipeline_module.BountyDomain.DOMAIN_NATIVE,
        pipeline_module.BountyDomain.DOMAIN_AI,
    }
    seen = []
    item = SimpleNamespace(
        risk_score=0.8, contract_address="fixture", advisory_id="fixture",
        findings=["test"], vulnerability_class=SimpleNamespace(value="test"),
        affected_subsystems=["test"], taint_level="TEST", to_dict=lambda: {},
    )
    ffi = SimpleNamespace(
        read=lambda: None, is_native=False, is_halted=lambda: False,
        manifest=SimpleNamespace(epoch_id=0, seq=0),
    )
    instance.dispatcher = SimpleNamespace(
        drain_domain=lambda d: [b"inert"] if d in relevant else [],
        get_queue_depths=lambda: {}, ffi_writer=ffi,
    )
    worker = SimpleNamespace(process_advisories=lambda _: [item])
    instance.defi_scraper = instance.webkit_connector = instance.ai_sentinel = worker
    instance.attester = SimpleNamespace(
        generate_receipt=lambda **kwargs: SimpleNamespace(domain=kwargs["domain"], to_dict=lambda: {})
    )
    def enqueue(receipt):
        seen.append(receipt.domain)
        return len(seen) != rejection_at
    instance.cold_ledger = SimpleNamespace(enqueue_receipt=enqueue)
    return instance, seen


@pytest.mark.asyncio
@pytest.mark.parametrize("rejection_at", [1, 2, 3])
async def test_pipeline_rejects_partial_cycle_without_returning_report(rejection_at):
    instance, seen = pipeline_fixture(rejection_at)
    with pytest.raises(RuntimeError, match="persistence is not confirmed"):
        await instance.execute_cycle()
    assert len(seen) == rejection_at


@pytest.mark.asyncio
async def test_pipeline_positive_cycle_reports_only_admission():
    instance, seen = pipeline_fixture(None)
    report = await instance.execute_cycle()
    assert len(seen) == len(report.claim_receipts) == 3
    assert report.to_dict()["receipt_persistence_status"] == "QUEUED_NOT_CONFIRMED"


@pytest.mark.asyncio
async def test_dag_competing_scheduler_cannot_enter_during_cancellation_cleanup(tmp_path):
    for iteration in range(5):
        path = str(tmp_path / f"exclusion-{iteration}.lock")
        scheduler = dag.KahnDagSwarmScheduler(3)
        entered = asyncio.Event()
        cleanup_entered = asyncio.Event()
        release = asyncio.Event()
        second_started = []
        async def delayed_cleanup(_memory):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleanup_entered.set()
                await release.wait()
        async def fail(_memory):
            await entered.wait()
            raise ValueError("independent trigger")
        scheduler.add_node(dag.SwarmDagNode("live", [], delayed_cleanup))
        scheduler.add_node(dag.SwarmDagNode("failure", [], fail))
        call = asyncio.create_task(scheduler.execute_dag(dag.KdaSwarmMemory(), path))
        await asyncio.wait_for(cleanup_entered.wait(), 2)
        other = dag.KahnDagSwarmScheduler(1)
        other.add_node(dag.SwarmDagNode("second", [], lambda _: second_started.append(True)))
        with pytest.raises(RuntimeError, match="Lock activo"):
            await other.execute_dag(dag.KdaSwarmMemory(), path)
        assert not second_started
        call.cancel()
        call.cancel()
        assert Path(path).exists()
        release.set()
        with pytest.raises((ValueError, asyncio.CancelledError)):
            await asyncio.wait_for(call, 2)
        await other.execute_dag(dag.KdaSwarmMemory(), path)
        assert second_started == [True]
        assert not Path(path).exists()
