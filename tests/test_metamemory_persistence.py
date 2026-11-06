"""Durable outcome history must survive a fresh monitor and ledger instance."""

from pathlib import Path

import pytest

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger
from babylon60.memory.metamemory import MetamemoryMonitor


def test_outcome_history_survives_fresh_monitor_and_ledger(tmp_path: Path) -> None:
    database = tmp_path / "cortex.db"
    first = MetamemoryMonitor(ledger=CortexPersistLedger(database))
    first.record_outcome("verify-results", False, context="python", attempt_id="attempt-1")

    second = MetamemoryMonitor(ledger=CortexPersistLedger(database))

    assert second.get_feeling_of_knowing("verify-results", context="python") == pytest.approx(0.75)
    assert second.get_feeling_of_knowing("verify-results", context="rust") == pytest.approx(0.85)


def test_duplicate_outcomes_do_not_double_count_and_conflicts_fail(tmp_path: Path) -> None:
    ledger = CortexPersistLedger(tmp_path / "retry.db")
    monitor = MetamemoryMonitor(ledger=ledger)
    monitor.record_outcome("verify", False, attempt_id="same")
    monitor.record_outcome("verify", False, attempt_id="same")
    assert monitor.get_feeling_of_knowing("verify") == pytest.approx(0.75)
    with pytest.raises(ValueError, match="attempt_id"):
        monitor.record_outcome("verify", True, attempt_id="same")
    assert len(ledger.query_events(event_type="METAMEMORY_OUTCOME")) == 1
    assert ledger.verify_integrity()


def test_previous_in_memory_api_stays_available_without_disk() -> None:
    monitor = MetamemoryMonitor()
    monitor.record_outcome("verify", False)
    assert monitor.get_feeling_of_knowing("verify") == pytest.approx(0.75)
    assert monitor.get_feeling_of_knowing("verify", context="other") == pytest.approx(0.85)
    assert MetamemoryMonitor().get_feeling_of_knowing("verify") == pytest.approx(0.85)
