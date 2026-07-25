import logging
from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass
from typing import Any
import cbor2
import uuid
NAMESPACE_UUID = uuid.UUID('9897d6fd-d6a7-4fe9-86bc-f0c312886d5d')
from babylon60.core.crypto import canonicalize_cbor, hash_sha3_256, verify_ed25519
from babylon60.database import core as database_core
_UNDECODABLE = object()

@dataclass(frozen=True)
class StateMutation:
    agent_id: str
    payload: dict[str, Any]
    timestamp: int
    signature: str
    causal_taint: str = 'BFT_Consensus_Init'

class BFT_Ledger:

    def __init__(self, db_path: str='master_ledger.db', node_keys: dict[str, str] | None=None) -> None:
        self.conn: sqlite3.Connection = database_core.connect_sync(db_path, synchronous='FULL')
        self._node_keys: dict[str, str] = dict(node_keys or {})
        self._init_tables()

    def _init_tables(self) -> None:
        self.conn.execute("\n            CREATE TABLE IF NOT EXISTS state_log (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                idempotency_key TEXT UNIQUE NOT NULL,\n                mutation_hash TEXT NOT NULL,\n                agent_id TEXT NOT NULL,\n                payload BLOB NOT NULL,\n                ts INTEGER NOT NULL,\n                causal_taint TEXT NOT NULL DEFAULT 'untainted'\n            )\n            ")

    def invoke_subagent(self, mutation: StateMutation, f: int, swarm_signatures: dict[str, str]) -> bool:
        required_votes = 2 * f + 1
        mutation_hash = hash_sha3_256(canonicalize_cbor(mutation.payload))
        valid_votes = sum((1 for node_id, sig in swarm_signatures.items() if self._verify_signature(node_id, mutation_hash, sig)))
        if valid_votes < required_votes:
            raise PermissionError(f'BFT_CONSENSUS_FAILURE: {valid_votes}/{required_votes} votes. State compromised.')
        payload_bytes = canonicalize_cbor(mutation.payload)
        idempotent_str = f'{mutation.agent_id}\x1f{mutation.timestamp}\x1f{mutation_hash}'
        idempotency_key = str(uuid.uuid5(NAMESPACE_UUID, idempotent_str))
        try:
            self.conn.execute('BEGIN IMMEDIATE')
            self.conn.execute('INSERT OR IGNORE INTO state_log (idempotency_key, mutation_hash, agent_id, payload, ts, causal_taint) VALUES (?, ?, ?, ?, ?, ?)', (idempotency_key, mutation_hash, mutation.agent_id, payload_bytes, mutation.timestamp, mutation.causal_taint))
            self.conn.execute('COMMIT')
        except sqlite3.Error:
            self.conn.execute('ROLLBACK')
            raise
        return True

    def _verify_signature(self, node_id: str, data_hash: str, sig: str) -> bool:
        public_key_hex = self._node_keys.get(node_id)
        if public_key_hex is None:
            return False
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
            raw = payload_bytes.decode('utf-8') if isinstance(payload_bytes, bytes) else payload_bytes
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            return _UNDECODABLE

    def audit_integrity(self) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('SELECT id, mutation_hash, payload FROM state_log')
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            logging.info(f'[-] No state_log table found or database uninitialized: {e}')
            return False
        corrupted = 0
        for row_id, stored_hash, payload_bytes in rows:
            payload_data = self._decode_payload(payload_bytes)
            if payload_data is _UNDECODABLE:
                logging.info(f'[!] Row {row_id}: payload indecodificable — corrupción')
                corrupted += 1
                continue
            try:
                computed_hash = hash_sha3_256(canonicalize_cbor(payload_data))
            except (cbor2.CBOREncodeError, ValueError, TypeError):
                logging.info(f'[!] Row {row_id}: payload no canonicalizable — corrupción')
                corrupted += 1
                continue
            if computed_hash != stored_hash:
                logging.info(f'[!] Corruption detected in row {row_id}! Stored: {stored_hash}, Computed: {computed_hash}')
                corrupted += 1
        return corrupted == 0
if __name__ == '__main__':
    import sys
    db_path = 'master_ledger.db'
    audit_mode = '--audit-mode' in sys.argv
    logging.info(f'[*] [C5-REAL] BFT Ledger Audit: db_path={db_path}, audit_mode={audit_mode}')
    ledger = BFT_Ledger(db_path)
    if audit_mode:
        if ledger.audit_integrity():
            logging.info('[+] Audit complete. Verified successfully.')
        else:
            logging.info('[!] Audit failed. Corrupted entries found!')
            sys.exit(1)