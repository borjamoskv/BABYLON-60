# [C5-REAL] ITERA-2 — Falsación de INV_BFT_02 (database.core), INV_C5_04 (votos reales),
# INV_C5_07 (cero necrosis en audit/queue) e INV_C5_03 (arco de atestación SHA3-256).
# Génesis: AUDITORIA_CENTURIA CENT-03/06/10/14 + NEW-E + ETHOS §3.
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from babylon60.core.crypto import Ed25519Signer, canonicalize_cbor, hash_sha3_256
from babylon60.database import core as dbcore


# ── INV_BFT_02: el módulo fantasma ahora es físico y aplica los pragmas ────────


@pytest.mark.asyncio
async def test_database_core_async_pragmas(tmp_path: Path) -> None:
    db = await dbcore.connect(tmp_path / "a.db")
    try:
        for pragma, expected in (("journal_mode", "wal"), ("busy_timeout", 5000), ("synchronous", 2)):
            cursor = await db.execute(f"PRAGMA {pragma}")
            row = await cursor.fetchone()
            assert row is not None and row[0] == expected, f"PRAGMA {pragma}: {row}"
    finally:
        await db.close()


def test_database_core_sync_pragmas(tmp_path: Path) -> None:
    conn = dbcore.connect_sync(tmp_path / "s.db", synchronous="NORMAL")
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 1
    finally:
        conn.close()


def test_database_core_rechaza_durabilidad_ilegal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="INV_BFT_02"):
        dbcore.connect_sync(tmp_path / "x.db", synchronous="OFF")


# ── INV_C5_04: el contador de votos BFT verifica firmas Ed25519 REALES ─────────


def _quorum_fixture(tmp_path: Path, n: int = 4):  # type: ignore
    from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation

    signers = {f"node_{i}": Ed25519Signer() for i in range(n)}
    node_keys = {nid: s.public_key_hex for nid, s in signers.items()}
    ledger = BFT_Ledger(str(tmp_path / "consensus.db"), node_keys=node_keys)
    mutation = StateMutation(agent_id="legion", payload={"op": "advance", "n": 60}, timestamp=1000.0, signature="")
    m_hash = hash_sha3_256(canonicalize_cbor(mutation.payload))
    return ledger, mutation, m_hash, signers


def test_consensus_quorum_con_firmas_reales(tmp_path: Path) -> None:
    ledger, mutation, m_hash, signers = _quorum_fixture(tmp_path)
    sigs = {nid: s.sign(m_hash) for nid, s in signers.items()}
    assert ledger.invoke_subagent(mutation, f=1, swarm_signatures=sigs) is True  # 4 == 3f+1
    assert ledger.audit_integrity() is True


def test_consensus_rechaza_voto_forjado_xfail(tmp_path: Path) -> None:
    """RED contra el verificador mock (return True): un voto forjado alcanzaba quórum."""
    ledger, mutation, m_hash, signers = _quorum_fixture(tmp_path)
    sigs = {nid: s.sign(m_hash) for nid, s in signers.items()}
    intruso = Ed25519Signer()  # clave NO registrada firma el mismo hash
    sigs["node_2"] = intruso.sign(m_hash)
    sigs["node_3"] = intruso.sign(m_hash)
    with pytest.raises(PermissionError, match="BFT_CONSENSUS_FAILURE"):
        ledger.invoke_subagent(mutation, f=1, swarm_signatures=sigs)  # 2 < 3


def test_consensus_fail_closed_sin_registro_de_claves(tmp_path: Path) -> None:
    from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation

    ledger = BFT_Ledger(str(tmp_path / "c2.db"))  # sin node_keys
    mutation = StateMutation(agent_id="x", payload={"a": 1}, timestamp=1.0, signature="")
    m_hash = hash_sha3_256(canonicalize_cbor(mutation.payload))
    with pytest.raises(PermissionError, match="BFT_CONSENSUS_FAILURE"):
        ledger.invoke_subagent(mutation, f=0, swarm_signatures={"ghost": Ed25519Signer().sign(m_hash)})


# ── INV_C5_07: payload indecodificable = corrupción reportada, no necrosis ─────


def test_audit_integrity_indecodificable_es_corrupcion(tmp_path: Path) -> None:
    """RED contra el código viejo: cbor+json fallan → os.kill(SIGKILL) mataba el proceso."""
    from babylon60.bft.consensus_ledger import BFT_Ledger

    ledger = BFT_Ledger(str(tmp_path / "audit.db"))
    ledger.conn.execute(
        "INSERT INTO state_log (mutation_hash, agent_id, payload, ts, causal_taint) VALUES (?, ?, ?, ?, ?)",
        ("deadbeef" * 8, "atacante", b"\xff\xfe\xfd garbage no-cbor no-json", 1.0, "test_corruption"),
    )
    assert ledger.audit_integrity() is False  # y el proceso sigue vivo


# ── INV_C5_07 + NEW-E: el queue auxiliar falla ruidoso y previene zombis ───────


@pytest.mark.asyncio
async def test_master_ledger_queue_zombie_prevention(tmp_path: Path) -> None:
    """RED contra el código viejo: el crash del writer ejecutaba SIGKILL en el done-callback."""
    from babylon60.bft.master_ledger_queue import MasterLedgerQueue

    queue = MasterLedgerQueue(str(tmp_path / "q.db"))
    await queue.initialize()
    await queue.submit_transaction("ESTO NO ES SQL VALIDO;;", ())
    await asyncio.sleep(0.2)  # el writer colapsa ruidosamente
    with pytest.raises(RuntimeError, match="Zombie Writer Prevention"):
        await queue.submit_transaction("SELECT 1;", ())
    await queue.shutdown()


@pytest.mark.asyncio
async def test_master_ledger_queue_durabilidad_full(tmp_path: Path) -> None:
    from babylon60.bft.master_ledger_queue import MasterLedgerQueue

    queue = MasterLedgerQueue(str(tmp_path / "q2.db"))
    await queue.initialize()
    try:
        assert queue.db is not None
        async with queue.db.execute("PRAGMA synchronous") as cursor:
            row = await cursor.fetchone()
            assert row is not None and row[0] == 2  # FULL — NEW-E colapsado
    finally:
        await queue.shutdown()


# ── INV_C5_03: el par attest/verify converge en SHA3-256 ───────────────────────


def _load_cli(name: str, filename: str):  # type: ignore
    path = Path(__file__).resolve().parent.parent / "babylon60" / "cli" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_attest_pair_sha3_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    attest = _load_cli("attest_cc", "attest_character_count.py")
    llm_attest = _load_cli("llm_attest", "llm_attest.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["attest_character_count.py", "babylon", "b"])
    attest.main()
    report = llm_attest.verify_receipt(str(tmp_path / "receipt.json"))
    assert report["status"] == "verified"
    assert report["hash_primitive"] == "sha3-256"
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["payload_hash"].startswith("sha3-256:")  # cero sha256 en el arco nuevo


def test_llm_attest_acepta_legacy_sha256_marcado(tmp_path: Path) -> None:
    """Recibos históricos sha256: siguen verificando, pero el reporte los marca legacy."""
    import base64
    import hashlib

    from nacl.signing import SigningKey

    llm_attest = _load_cli("llm_attest2", "llm_attest.py")
    payload = {"word": "legacy", "n": 1}
    canonical = llm_attest.jcs_canonicalize(payload)
    payload_hash = f"sha256:{hashlib.sha256(canonical).hexdigest()}"
    sk = SigningKey.generate()
    sig = base64.urlsafe_b64encode(sk.sign(payload_hash.encode()).signature).decode().rstrip("=")
    pub = base64.urlsafe_b64encode(sk.verify_key.encode()).decode().rstrip("=")
    receipt = {
        "receipt_id": "rec_legacy",
        "schema": "https://schema.babylon60.dev/v0.2/character-attestation",
        "payload": payload,
        "payload_hash": payload_hash,
        "signature": {"algorithm": "Ed25519", "key_id": f"did:key:{pub}", "value": sig},
    }
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(receipt))
    report = llm_attest.verify_receipt(str(path))
    assert report["status"] == "verified"
    assert report["hash_primitive"] == "sha256-legacy"
