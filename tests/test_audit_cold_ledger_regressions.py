"""Isolated SQLite regressions for audit H04/H05; no attestation execution."""

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from babylon60.bft.bounty_claim_attester import BountyClaimReceipt
from babylon60.bft.bounty_cold_ledger import BountyColdLedger
from babylon60.kernel.bft_sqlite import BFTDatabaseError, BFTSQLite


def _receipt() -> BountyClaimReceipt:
    return BountyClaimReceipt(
        claim_id="isolated-audit-receipt",
        advisory_id="test-only",
        domain="DOMAIN_AI",
        finding_summary="isolated persistence regression",
        risk_score=0.5,
        payload_hash="test-payload",
        timestamp_utc="2026-10-23T00:00:00Z",
        hardware_anchor="TEST-NOT-ATTESTED",
        attestation_merkle_root="test-root",
    )


def test_bft_connections_require_full_sync(tmp_path: Path) -> None:
    database = BFTSQLite(str(tmp_path / "ledger.db"))
    for _ in range(2):
        with database._connection() as conn:
            assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2


@pytest.mark.parametrize("failure", ["locked", "missing_table"])
def test_failed_batch_remains_pending_and_failure_reaches_caller(tmp_path: Path, failure: str) -> None:
    path = tmp_path / "ledger.db"
    ledger = BountyColdLedger(str(path))
    ledger._sqlite.max_retries = 0
    receipt = _receipt()
    blocker = sqlite3.connect(path)
    try:
        if failure == "locked":
            blocker.execute("BEGIN IMMEDIATE")
        else:
            blocker.execute("DROP TABLE bounty_claims")
            blocker.commit()
        assert ledger.enqueue_receipt(receipt)
        ledger.start()
        assert ledger._worker_thread is not None
        ledger._worker_thread.join(timeout=10)
        assert not ledger._worker_thread.is_alive()
        assert ledger.failed_receipts == (receipt,)
        assert ledger._queue.unfinished_tasks == 1
        for action in (ledger.stop, ledger.start, lambda: ledger.enqueue_receipt(receipt)):
            with pytest.raises(BFTDatabaseError, match="remain pending"):
                action()
    finally:
        blocker.rollback()
        blocker.close()


def test_successful_batch_is_committed_before_completion(tmp_path: Path) -> None:
    path = tmp_path / "ledger.db"
    ledger = BountyColdLedger(str(path))
    receipt = _receipt()
    ledger.enqueue_receipt(receipt)
    ledger.start()
    ledger.stop()
    assert ledger.failed_receipts == ()
    assert ledger._queue.unfinished_tasks == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT claim_id FROM bounty_claims").fetchall() == [(receipt.claim_id,)]


def test_stopped_ledger_rejects_receipts_and_repeated_stop_is_idle(tmp_path: Path) -> None:
    path = tmp_path / "closed.db"
    ledger = BountyColdLedger(str(path))
    ledger.start()
    ledger.stop()
    assert ledger.enqueue_receipt(_receipt()) is False
    ledger.stop()
    assert ledger._queue.empty()
    assert ledger._queue.unfinished_tasks == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM bounty_claims").fetchone() == (0,)


def test_stop_drains_receipts_accepted_before_start(tmp_path: Path) -> None:
    path = tmp_path / "prestart.db"
    ledger = BountyColdLedger(str(path))
    assert ledger.enqueue_receipt(_receipt())
    ledger.stop(timeout=0.5)
    assert ledger._queue.unfinished_tasks == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT claim_id FROM bounty_claims").fetchall() == [(_receipt().claim_id,)]


def test_shutdown_seals_admission_before_sentinel_and_serializes_stoppers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    warmup = BountyColdLedger(str(tmp_path / "warmup.db"))
    warmup.start()
    for _ in range(16):
        assert warmup.enqueue_receipt(_receipt())
    warmup.stop()

    path = tmp_path / "concurrent.db"
    ledger = BountyColdLedger(str(path))
    entered, release, sentinel = threading.Event(), threading.Event(), threading.Event()
    original_write = ledger._sqlite.executemany_with_backoff
    original_put = ledger._queue.put

    def blocked_write(query: str, rows: list[tuple[object, ...]]) -> None:
        entered.set()
        assert release.wait(3)
        original_write(query, rows)

    def observe_sentinel(item: BountyClaimReceipt | None, block: bool = True, timeout: float | None = None) -> None:
        if item is None:
            sentinel.set()
        original_put(item, block=block, timeout=timeout)

    monkeypatch.setattr(ledger._sqlite, "executemany_with_backoff", blocked_write)
    monkeypatch.setattr(ledger._queue, "put", observe_sentinel)
    assert ledger.enqueue_receipt(_receipt())
    ledger.start()
    assert entered.wait(3)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(ledger.stop, 3.0)
        try:
            assert sentinel.wait(3)
            second = pool.submit(ledger.stop, 3.0)
            for _ in range(128):
                assert ledger.enqueue_receipt(_receipt()) is False
        finally:
            release.set()
        first.result(timeout=3)
        second.result(timeout=3)
    assert ledger._queue.empty() and ledger._queue.unfinished_tasks == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM bounty_claims").fetchone() == (1,)
    with pytest.raises(RuntimeError, match="closed"):
        ledger.start()
