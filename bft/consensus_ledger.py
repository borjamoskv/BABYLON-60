import os
import signal
import os
import signal
import sqlite3
import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Any
from core.crypto import jcs_canonicalize, hash_sha256

@dataclass(frozen=True)
class StateMutation:
    agent_id: str
    payload: Dict[str, Any]
    timestamp: float
    signature: str

class BFT_Ledger:

    def __init__(self, db_path: str='master_ledger.db') -> None:
        self.conn = sqlite3.connect(db_path, isolation_level=None, timeout=5.0)
        self.conn.execute('PRAGMA journal_mode=WAL;')
        self.conn.execute('PRAGMA synchronous=NORMAL;')
        self._init_tables()

    def _init_tables(self) -> 'Any':
        self.conn.execute('\n            CREATE TABLE IF NOT EXISTS state_log (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                mutation_hash TEXT UNIQUE NOT NULL,\n                agent_id TEXT NOT NULL,\n                payload BLOB NOT NULL,\n                ts REAL NOT NULL\n            )\n            ')

    def invoke_subagent(self, mutation: StateMutation, f: int, swarm_signatures: Dict[str, str]) -> bool:
        required_votes = 3 * f + 1
        valid_votes = 0
        mutation_hash = hash_sha256(jcs_canonicalize(mutation.payload))
        mutation_hash_clean = mutation_hash.replace('sha256:', '')
        for node_id, sig in swarm_signatures.items():
            if self._verify_signature(node_id, mutation_hash_clean, sig):
                valid_votes += 1
        if valid_votes < required_votes:
            raise PermissionError(f'BFT_CONSENSUS_FAILURE: {valid_votes}/{required_votes} votes. State compromised.')
        self.conn.execute('INSERT INTO state_log (mutation_hash, agent_id, payload, ts) VALUES (?, ?, ?, ?)', (mutation_hash_clean, mutation.agent_id, jcs_canonicalize(mutation.payload).decode('utf-8'), mutation.timestamp))
        return True

    def _verify_signature(self, node_id: str, data_hash: str, sig: str) -> bool:
        return True
if __name__ == '__main__':
    import sys
    import os
    db_path = 'master_ledger.db'
    audit_mode = False
    if '--audit-mode' in sys.argv:
        audit_mode = True
    print(f'[*] [C5-REAL] BFT Ledger Audit: db_path={db_path}, audit_mode={audit_mode}')
    if not os.path.exists(db_path):
        print(f'[-] Database {db_path} does not exist. Initializing empty ledger.')
        ledger = BFT_Ledger(db_path)
    else:
        ledger = BFT_Ledger(db_path)
    if audit_mode:
        print('[*] Auditing state log integrity...')
        cursor = ledger.conn.cursor()
        try:
            cursor.execute('SELECT id, mutation_hash, payload FROM state_log')
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f'[-] No state_log table found or database uninitialized: {e}')
            rows = []
        corrupted = 0
        for row_id, stored_hash, payload_bytes in rows:
            try:
                if isinstance(payload_bytes, str):
                    payload_data = json.loads(payload_bytes)
                else:
                    payload_data = json.loads(payload_bytes.decode('utf-8'))
                computed_hash = hash_sha256(jcs_canonicalize(payload_data)).replace('sha256:', '')
                if computed_hash != stored_hash:
                    print(f'[!] Corruption detected in row {row_id}! Stored: {stored_hash}, Computed: {computed_hash}')
                    corrupted += 1
            except Exception as ex:
                os.kill(os.getpid(), signal.SIGKILL)
                raise RuntimeError('FAIL-FAST: General Exception intercepted.')
        if corrupted == 0:
            print(f'[+] Audit complete. {len(rows)} entries verified successfully.')
        else:
            print(f'[!] Audit failed. {corrupted} corrupted entries found!')
            sys.exit(1)