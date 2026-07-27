# [C5-REAL] Exergy-Maximized
"""Unit tests for SovereignOutbox using cortex_outbox_queue."""

import time
import pytest
from pathlib import Path

from babylon60.delivery.outbox import SovereignOutbox


@pytest.fixture
def outbox_db(tmp_path: Path) -> Path:
    """Fixture to provide a temporary database path for testing."""
    return tmp_path / "test_outbox.db"


def test_outbox_lifecycle(outbox_db: Path):
    """Test full outbox enqueue-claim-complete-fail cycle."""
    with SovereignOutbox(outbox_db) as outbox:
        # Check initial stats
        stats = outbox.stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0

        # Enqueue first task with taint
        task_id_1 = outbox.enqueue(
            agent_id="agent_alpha",
            payload=b"test_payload_1",
            taint="taint:agent_alpha:s1:123456:h1",
        )
        assert task_id_1 > 0

        # Enqueue second task without taint
        task_id_2 = outbox.enqueue(
            agent_id="agent_beta",
            payload=b"test_payload_2",
        )
        assert task_id_2 > task_id_1

        # Check stats after enqueuing
        stats = outbox.stats()
        assert stats["total"] == 2
        assert stats["pending"] == 2
        assert stats["claimed"] == 0

        # Claim the pending tasks
        claimed = outbox.fetch_pending(batch_size=10)
        assert len(claimed) == 2

        # Verify first claimed task
        assert claimed[0][0] == task_id_1
        assert claimed[0][1] == "agent_alpha"
        assert claimed[0][2] == b"test_payload_1"
        assert claimed[0][3] == "taint:agent_alpha:s1:123456:h1"

        # Verify second claimed task
        assert claimed[1][0] == task_id_2
        assert claimed[1][1] == "agent_beta"
        assert claimed[1][2] == b"test_payload_2"
        assert claimed[1][3] is None

        # Check stats after claiming
        stats = outbox.stats()
        assert stats["pending"] == 0
        assert stats["claimed"] == 2

        # Complete the first task
        assert outbox.complete(task_id_1) is True

        # Fail the second task
        assert outbox.fail(task_id_2, "Simulated execution failure") is True

        # Check stats after completion/failure
        stats = outbox.stats()
        assert stats["pending"] == 0
        assert stats["claimed"] == 0
        assert stats["completed"] == 1
        assert stats["failed"] == 1


def test_requeue_stale_tasks(outbox_db: Path):
    """Test that claimed tasks older than timeout can be requeued."""
    with SovereignOutbox(outbox_db) as outbox:
        # Enqueue and claim a task
        task_id = outbox.enqueue("agent_stale", b"payload")
        claimed = outbox.fetch_pending(batch_size=1)
        assert len(claimed) == 1

        # Requeue stale with timeout_sec = -1 to force all claimed tasks to be stale
        requeued_count = outbox.requeue_stale(timeout_sec=-1.0)
        assert requeued_count == 1

        # Verify stats show it is pending again
        stats = outbox.stats()
        assert stats["pending"] == 1
        assert stats["claimed"] == 0


def test_purge_completed_tasks(outbox_db: Path):
    """Test purging of completed tasks."""
    with SovereignOutbox(outbox_db) as outbox:
        task_id = outbox.enqueue("agent_purge", b"payload")
        outbox.fetch_pending(batch_size=1)
        outbox.complete(task_id)

        # Purge with older_than_sec = -1 to force delete immediately
        purged = outbox.purge_completed(older_than_sec=-1.0)
        assert purged == 1

        stats = outbox.stats()
        assert stats["total"] == 0


def test_wal_mode_active(outbox_db: Path):
    """Test that outbox connection establishes WAL journal mode."""
    with SovereignOutbox(outbox_db) as outbox:
        assert outbox.journal_mode().lower() == "wal"
