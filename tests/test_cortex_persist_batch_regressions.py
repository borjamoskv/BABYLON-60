# ============================================================================
# BABYLON-60 v4.0 — Regression tests for audit findings B-1 / B-2 (2026-09-10)
# █ Verificación empírica del camino append_batch de CortexPersistLedger
# ============================================================================
"""
Regresiones del audit independiente 2026-09-10:

- B-1: un lote que mezcla duplicados de eventos YA comprometidos con eventos
  nuevos reanclaba prev_hash al hash del duplicado, rompiendo la cadena de
  forma permanente (verify_integrity() -> False) sin atacante alguno.
- B-2: un evento repetido DENTRO del mismo lote no se detectaba (las filas se
  insertan diferidas) y abortaba toda la transacción con IntegrityError.

Estos tests fallan contra la versión previa al fix y pasan con ella.
"""

import sqlite3
from pathlib import Path

import pytest

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent


def _ev(tag: str, n: int = 1) -> CortexEvent:
    return CortexEvent(event_type="AGENT_ACTION", payload={"tag": tag, "n": n}, cortex_taint=f"taint:{tag}")


def test_batch_mixed_committed_duplicate_preserves_chain(tmp_path: Path) -> None:
    """B-1: [nuevo, duplicado-comprometido, nuevo] no debe romper la cadena."""
    ledger = CortexPersistLedger(tmp_path / "b1.db")
    ev_a = _ev("A")
    ledger.append_event(ev_a)  # seq 1 (comprometido)

    res = ledger.append_batch([_ev("B"), ev_a, _ev("C")])

    assert [r["status"] for r in res] == ["C5_PERMANENT", "DUPLICATE_IGNORED", "C5_PERMANENT"]
    assert [r["seq"] for r in res] == [2, 1, 3]

    # La fila seq=3 debe encadenar con seq=2 (B), NO con seq=1 (A, el duplicado)
    conn = sqlite3.connect(tmp_path / "b1.db")
    rows = conn.execute("SELECT seq, prev_hash, entry_hash FROM cortex_ledger ORDER BY seq").fetchall()
    conn.close()
    by_seq = {seq: (ph, eh) for seq, ph, eh in rows}
    assert by_seq[3][0] == by_seq[2][1], "seq3.prev_hash debe ser seq2.entry_hash"

    assert ledger.verify_integrity() is True


def test_batch_intra_batch_duplicate_no_crash(tmp_path: Path) -> None:
    """B-2: [A, B, A, C] en un solo lote -> DUPLICATE_IGNORED, sin IntegrityError."""
    ledger = CortexPersistLedger(tmp_path / "b2.db")
    ev_a = _ev("A")

    res = ledger.append_batch([ev_a, _ev("B"), ev_a, _ev("C")])

    assert [r["status"] for r in res] == [
        "C5_PERMANENT",
        "C5_PERMANENT",
        "DUPLICATE_IGNORED",
        "C5_PERMANENT",
    ]
    assert res[2]["seq"] == res[0]["seq"] == 1
    assert ledger.verify_integrity() is True

    conn = sqlite3.connect(tmp_path / "b2.db")
    count = conn.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0]
    conn.close()
    assert count == 3  # solo A, B, C — el duplicado nunca se inserta


def test_batch_full_replay_is_idempotent(tmp_path: Path) -> None:
    """Re-ejecutar el MISMO lote completo: todo DUPLICATE_IGNORED y cadena íntegra."""
    ledger = CortexPersistLedger(tmp_path / "replay.db")
    batch = [_ev("X"), _ev("Y"), _ev("Z")]

    first = ledger.append_batch(batch)
    second = ledger.append_batch(batch)

    assert all(r["status"] == "C5_PERMANENT" for r in first)
    assert all(r["status"] == "DUPLICATE_IGNORED" for r in second)
    assert [r["entry_hash"] for r in first] == [r["entry_hash"] for r in second]
    assert ledger.verify_integrity() is True


def test_append_event_quickstart_api(tmp_path: Path) -> None:
    """Paridad con el quick-start del README: append_event + verify + merkle."""
    ledger = CortexPersistLedger(tmp_path / "qs.db")
    result = ledger.append_event(
        CortexEvent(
            event_type="AGENT_ACTION",
            payload={"action": "search", "query": "quarterly revenue"},
            cortex_taint="session:abc123",
        )
    )
    assert result["status"] == "C5_PERMANENT"
    assert result["seq"] == 1
    assert ledger.verify_integrity() is True
    assert len(ledger.get_merkle_root()) == 64


def test_batch_empty_and_taint_invariant(tmp_path: Path) -> None:
    """Lote vacío -> []; taint vacío dentro de lote -> ValueError (INV_BFT_03)."""
    ledger = CortexPersistLedger(tmp_path / "edge.db")
    assert ledger.append_batch([]) == []
    with pytest.raises(ValueError, match="INV_BFT_03"):
        ledger.append_batch([_ev("OK"), CortexEvent(event_type="X", payload={}, cortex_taint="")])
    assert ledger.verify_integrity() is True
