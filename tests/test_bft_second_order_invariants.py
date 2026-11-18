"""Adversarial test suite for BFT Second-Order Invariants (BFT-1 to BFT-6 / O-BFT-1 to O-BFT-5)."""

from __future__ import annotations

import asyncio
import math
import sqlite3
from pathlib import Path

import pytest

from babylon60.bft.bayesian_swarm import BayesianSwarm, BFTByzantineError
from babylon60.kernel.bft_consensus import (
    BFTEquivocationError,
    evaluate_bft_quorum,
    evaluate_thermodynamic_invariants,
)
from babylon60.kernel.bft_db_async import persist_bft_event
from babylon60.kernel.bft_falsification import run_falsification_siege
from babylon60.kernel.bft_sqlite import BFTSQLite


def test_o_bft_1_byzantine_single_node_cannot_veto_quorum_and_sybil_nan_rejected() -> None:
    """O-BFT-1 (BFT-1): In N=4 (f=1), 1 Byzantine agent assigning p=0 cannot veto 3 honest agents; Sybil/NaN/0-weight blocked."""
    committee = ["A1", "A2", "A3", "A4"]
    swarm = BayesianSwarm(agents=committee)

    # 1. Single Byzantine node A4 tries to veto H_HONEST with p=0.0 while A1, A2, A3 (2f+1 = 3) back H_HONEST
    opinions = {
        "A1": {"H_HONEST": 0.98, "H_MALICIOUS": 0.02},
        "A2": {"H_HONEST": 0.97, "H_MALICIOUS": 0.03},
        "A3": {"H_HONEST": 0.99, "H_MALICIOUS": 0.01},
        "A4": {"H_HONEST": 0.0, "H_MALICIOUS": 1.0},
    }
    pooled = swarm.logarithmic_opinion_pool(opinions)
    assert pooled["H_HONEST"] > 0.50
    assert pooled["H_HONEST"] > pooled["H_MALICIOUS"]
    assert math.isclose(sum(pooled.values()), 1.0, rel_tol=1e-9)

    # 2. If >= f+1 (2 out of 4) active agents assign p=0.0, then hard veto applies legitimately
    opinions_two_zeros = {
        "A1": {"H_HONEST": 0.0, "H_ALT": 1.0},
        "A2": {"H_HONEST": 0.0, "H_ALT": 1.0},
        "A3": {"H_HONEST": 0.99, "H_ALT": 0.01},
        "A4": {"H_HONEST": 0.99, "H_ALT": 0.01},
    }
    pooled_vetoed = swarm.logarithmic_opinion_pool(opinions_two_zeros)
    assert pooled_vetoed["H_HONEST"] == 0.0
    assert pooled_vetoed["H_ALT"] == 1.0

    # 3. Zero-weight agent cannot veto even in small committee (N=2 active)
    small_swarm = BayesianSwarm(agents=["A1", "A2", "A3"])
    zero_weight_opinions = {
        "A1": {"H_SAFE": 0.9, "H_OTHER": 0.1},
        "A2": {"H_SAFE": 0.8, "H_OTHER": 0.2},
        "A3": {"H_SAFE": 0.0, "H_OTHER": 1.0},
    }
    res_zw = small_swarm.logarithmic_opinion_pool(
        zero_weight_opinions,
        weights={"A1": 0.5, "A2": 0.5, "A3": 0.0},
    )
    assert res_zw["H_SAFE"] > 0.80

    # 4. Sybil agent not in committee must be rejected
    with pytest.raises(BFTByzantineError, match="Sybil"):
        swarm.logarithmic_opinion_pool({**opinions, "SYBIL_INTRUDER": {"H_HONEST": 0.0, "H_MALICIOUS": 1.0}})

    # 5. NaN / Inf probabilities or weights must be rejected
    with pytest.raises(ValueError, match="NaN or Inf"):
        swarm.logarithmic_opinion_pool({**opinions, "A4": {"H_HONEST": float("nan"), "H_MALICIOUS": 0.5}})


def test_o_bft_2_monotonic_epochs_and_equivocation_detection() -> None:
    """O-BFT-2 (BFT-5): Stale epochs and same-epoch equivocation must fail closed."""
    swarm = BayesianSwarm(agents=["A1", "A2", "A3", "A4"])
    opinions_e2 = {
        "A1": {"H1": 0.9, "H2": 0.1},
        "A2": {"H1": 0.9, "H2": 0.1},
        "A3": {"H1": 0.9, "H2": 0.1},
        "A4": {"H1": 0.9, "H2": 0.1},
    }
    opinions_e1_stale = {
        "A1": {"H1": 0.1, "H2": 0.9},
        "A2": {"H1": 0.1, "H2": 0.9},
        "A3": {"H1": 0.1, "H2": 0.9},
        "A4": {"H1": 0.1, "H2": 0.9},
    }

    async def _run() -> None:
        res2 = await swarm.async_pool_and_update(opinions_e2, epoch=2)
        assert res2["H1"] > 0.85
        assert swarm.current_epoch == 2

        # Stale epoch 1 arriving late must not overwrite epoch 2 beliefs
        with pytest.raises(BFTByzantineError, match="Stale BFT epoch"):
            await swarm.async_pool_and_update(opinions_e1_stale, epoch=1)

        assert swarm.get_beliefs()["H1"] > 0.85

        # Idempotent replay of exact same opinions in epoch 2 is allowed
        await swarm.async_pool_and_update(opinions_e2, epoch=2)

        # Conflicting opinion from A4 in same epoch 2 is equivocation -> rejected
        equivocated = dict(opinions_e2)
        equivocated["A4"] = {"H1": 0.2, "H2": 0.8}
        with pytest.raises(BFTByzantineError, match="Equivocation"):
            await swarm.async_pool_and_update(equivocated, epoch=2)

    asyncio.run(_run())
    # Multi-loop resilience: calling asyncio.run a second time on same instance must work cleanly
    asyncio.run(swarm.async_pool_and_update(opinions_e2, epoch=3))
    assert swarm.current_epoch == 3


def test_o_bft_3_bft_sqlite_materialized_cursor_and_siege(tmp_path: Path) -> None:
    """O-BFT-3 (BFT-2 & BFT-6): BFTSQLite cursor remains readable after connection closes and siege persists all rows."""
    db_file = tmp_path / "bft_cursor_test.db"
    db = BFTSQLite(str(db_file))
    db.execute_with_backoff("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
    ins = db.execute_with_backoff("INSERT INTO items (name) VALUES (?)", ("alpha",))
    assert ins.rowcount == 1
    assert ins.lastrowid == 1

    db.executemany_with_backoff("INSERT INTO items (name) VALUES (?)", [("beta",), ("gamma",)])

    cur = db.execute_with_backoff("SELECT id, name FROM items ORDER BY id ASC")
    first = cur.fetchone()
    assert first is not None and first["name"] == "alpha"
    rest = cur.fetchall()
    assert [r["name"] for r in rest] == ["beta", "gamma"]

    siege_db = tmp_path / "siege.db"
    report = run_falsification_siege(num_threads=12, db_path=str(siege_db))
    assert report == {"expected": 12, "persisted": 12}


def test_o_bft_4_async_persistence_prevents_split_brain_and_epoch_collision(tmp_path: Path) -> None:
    """O-BFT-4 (BFT-3): persist_bft_event rejects duplicate/regressing lamport_t and mismatched prev_hash."""
    db_path = str(tmp_path / "async_bft.db")

    async def _scenario() -> None:
        h1 = await persist_bft_event(db_path, "evt_1", '{"step":1}', 1, "C5_TAINT")
        assert len(h1) == 64

        # Same lamport_t (epoch collision) must fail closed
        with pytest.raises(ValueError, match="Epoch Collision"):
            await persist_bft_event(db_path, "evt_fork", '{"step":99}', 1, "C5_TAINT", prev_hash=h1)

        # Wrong prev_hash (Split-Brain attempt) at lamport_t=2 must fail closed
        with pytest.raises(ValueError, match="Split-Brain"):
            await persist_bft_event(db_path, "evt_bad_prev", '{"step":2}', 2, "C5_TAINT", prev_hash="f" * 64)

        # Valid chained event at lamport_t=2 succeeds
        h2 = await persist_bft_event(db_path, "evt_2", '{"step":2}', 2, "C5_TAINT", prev_hash=h1)
        assert len(h2) == 64 and h2 != h1

    asyncio.run(_scenario())

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT id, lamport_t FROM events ORDER BY lamport_t ASC").fetchall()
    assert rows == [("evt_1", 1), ("evt_2", 2)]


def test_o_bft_5_consensus_quorum_equivocation_and_ast_audit() -> None:
    """O-BFT-5 (BFT-4): evaluate_bft_quorum and evaluate_thermodynamic_invariants enforce 2f+1 and AST safety."""
    committee = ["N1", "N2", "N3", "N4"]
    ledger: dict[tuple[int, str], str] = {}

    # 3 out of 4 honest nodes vote for digest_A -> quorum reached
    res = evaluate_bft_quorum(
        votes={"N1": "digest_A", "N2": "digest_A", "N3": "digest_A", "N4": "digest_B"},
        committee=committee,
        f=1,
        epoch=1,
        vote_ledger=ledger,
    )
    assert res["quorum_reached"] is True
    assert res["winning_digest"] == "digest_A"

    # Node N4 attempts to equivocate in epoch 1 with a different digest
    with pytest.raises(BFTEquivocationError, match="Equivocation"):
        evaluate_bft_quorum(
            votes={"N4": "digest_C"},
            committee=committee,
            f=1,
            epoch=1,
            vote_ledger=ledger,
        )

    # Dangerous AST primitive (eval) or path-traversal dependency must be rejected
    bad_ast = evaluate_thermodynamic_invariants(
        {"type": "Call", "func": "eval", "args": ["__import__('os')"]},
        ["../evil_pkg"],
    )
    assert bad_ast["is_valid"] is False
    assert bad_ast["action"] == "THERMODYNAMIC_OVERRIDE"

    clean_ast = evaluate_thermodynamic_invariants(
        {"type": "Module", "body": [{"type": "Assign", "name": "x", "value": 42}]},
        ["pytest>=8.0", "cryptography"],
        votes={"N1": "digest_A", "N2": "digest_A", "N3": "digest_A"},
        committee=committee,
        f=1,
    )
    assert clean_ast["is_valid"] is True
    assert clean_ast["action"] == "PROCEED"
