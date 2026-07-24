# [C5-REAL] BFT consensus ledger — votos Ed25519 reales, conexión INV_BFT_02, auditoría sin necrosis.
# INV_C5_04 (verificador mock = teatro de consenso), INV_C5_07 (SIGKILL en audit).
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Optional

import cbor2

from babylon60.core.crypto import canonicalize_cbor, hash_sha3_256, verify_ed25519
from babylon60.database import core as database_core

_UNDECODABLE = object()


@dataclass(frozen=True)
class StateMutation:
    agent_id: str
    payload: Dict[str, Any]
    timestamp: int
    signature: str
    causal_taint: str = "BFT_Consensus_Init"


class BFT_Ledger:
    """Ledger de consenso BFT (superficie síncrona: CLI/scripts, fuera de event loop).

    INV_C5_04: `_verify_signature` verifica Ed25519 REAL contra el registro
    `node_keys` (node_id → public_key_hex raw). Nodo no registrado o firma
    inválida = voto nulo. Sin registro → cero votos válidos (fail-closed).
    INV_BFT_02: la conexión sale de `babylon60.database.core` (WAL + busy_timeout
    + synchronous=FULL). INV_C5_07: la auditoría emite veredicto, nunca necrosis.
    """

    def __init__(self, db_path: str = "master_ledger.db", node_keys: Optional[Dict[str, str]] = None) -> None:
        self.conn: sqlite3.Connection = database_core.connect_sync(db_path, synchronous="FULL")
        self._node_keys: Dict[str, str] = dict(node_keys or {})
        self._init_tables()

    def _init_tables(self) -> None:
        self.conn.execute(
            "\n            CREATE TABLE IF NOT EXISTS state_log (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                mutation_hash TEXT UNIQUE NOT NULL,\n                agent_id TEXT NOT NULL,\n                payload BLOB NOT NULL,\n                ts INTEGER NOT NULL,\n                causal_taint TEXT NOT NULL DEFAULT 'untainted'\n            )\n            "
        )

    def invoke_subagent(self, mutation: StateMutation, f: int, swarm_signatures: Dict[str, str]) -> bool:
        required_votes = (2 * f) + 1
        mutation_hash = hash_sha3_256(canonicalize_cbor(mutation.payload))
        valid_votes = sum(
            1 for node_id, sig in swarm_signatures.items() if self._verify_signature(node_id, mutation_hash, sig)
        )
        if valid_votes < required_votes:
            raise PermissionError(f"BFT_CONSENSUS_FAILURE: {valid_votes}/{required_votes} votes. State compromised.")
        self.conn.execute(
            "INSERT OR IGNORE INTO state_log (mutation_hash, agent_id, payload, ts, causal_taint) VALUES (?, ?, ?, ?, ?)",
            (
                mutation_hash,
                mutation.agent_id,
                canonicalize_cbor(mutation.payload),
                mutation.timestamp,
                mutation.causal_taint,
            ),
        )
        return True

    def _verify_signature(self, node_id: str, data_hash: str, sig: str) -> bool:
        public_key_hex = self._node_keys.get(node_id)
        if public_key_hex is None:
            return False  # nodo no registrado: voto nulo (fail-closed, INV_C5_04)
        return verify_ed25519(public_key_hex, data_hash, sig)

    @staticmethod
    def _decode_payload(payload_bytes: Any) -> Any:
        if isinstance(payload_bytes, memoryview):
            payload_bytes = payload_bytes.tobytes()
        try:
            return cbor2.loads(payload_bytes)
        except (cbor2.CBORDecodeError, ValueError):
            pass
        try:
            raw = payload_bytes.decode("utf-8") if isinstance(payload_bytes, bytes) else payload_bytes
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            return _UNDECODABLE

    def audit_integrity(self) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, mutation_hash, payload FROM state_log")
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"[-] No state_log table found or database uninitialized: {e}")
            return False
        corrupted = 0
        for row_id, stored_hash, payload_bytes in rows:
            payload_data = self._decode_payload(payload_bytes)
            if payload_data is _UNDECODABLE:
                # INV_C5_07: lo indecodificable ES evidencia de corrupción — veredicto, no necrosis.
                print(f"[!] Row {row_id}: payload indecodificable — corrupción")
                corrupted += 1
                continue
            try:
                computed_hash = hash_sha3_256(canonicalize_cbor(payload_data))
            except (cbor2.CBOREncodeError, ValueError, TypeError):
                print(f"[!] Row {row_id}: payload no canonicalizable — corrupción")
                corrupted += 1
                continue
            if computed_hash != stored_hash:
                print(f"[!] Corruption detected in row {row_id}! Stored: {stored_hash}, Computed: {computed_hash}")
                corrupted += 1
        return corrupted == 0


if __name__ == "__main__":
    import sys

    db_path = "master_ledger.db"
    audit_mode = "--audit-mode" in sys.argv
    print(f"[*] [C5-REAL] BFT Ledger Audit: db_path={db_path}, audit_mode={audit_mode}")
    ledger = BFT_Ledger(db_path)
    if audit_mode:
        if ledger.audit_integrity():
            print("[+] Audit complete. Verified successfully.")
        else:
            print("[!] Audit failed. Corrupted entries found!")
            sys.exit(1)
