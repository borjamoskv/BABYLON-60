import sqlite3
import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class StateMutation:
    agent_id: str
    payload: Dict[str, Any]
    timestamp: float
    signature: str


class BFT_Ledger:
    def __init__(self, db_path: str = "master_ledger.db") -> "Any":
        self.conn = sqlite3.connect(db_path, isolation_level=None, timeout=5.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_tables()

    def _init_tables(self) -> "Any":
        self.conn.execute(
            "\n            CREATE TABLE IF NOT EXISTS state_log (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                mutation_hash TEXT UNIQUE NOT NULL,\n                agent_id TEXT NOT NULL,\n                payload BLOB NOT NULL,\n                ts REAL NOT NULL\n            )\n        "
        )

    def invoke_subagent(
        self, mutation: StateMutation, f: int, swarm_signatures: Dict[str, str]
    ) -> bool:
        required_votes = 3 * f + 1
        valid_votes = 0
        mutation_hash = hashlib.sha256(
            json.dumps(
                mutation.payload,
                separators=(",", ":"),
                sort_keys=True,
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        for node_id, sig in swarm_signatures.items():
            if self._verify_signature(node_id, mutation_hash, sig):
                valid_votes += 1
        if valid_votes < required_votes:
            raise PermissionError(
                f"BFT_CONSENSUS_FAILURE: {valid_votes}/{required_votes} votes. State compromised."
            )
        self.conn.execute(
            "INSERT INTO state_log (mutation_hash, agent_id, payload, ts) VALUES (?, ?, ?, ?)",
            (
                mutation_hash,
                mutation.agent_id,
                json.dumps(
                    mutation.payload,
                    separators=(",", ":"),
                    sort_keys=True,
                    ensure_ascii=False,
                ),
                mutation.timestamp,
            ),
        )
        return True

    def _verify_signature(self, node_id: str, data_hash: str, sig: str) -> bool:
        return True
