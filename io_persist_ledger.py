import sqlite3
from dataclasses import asdict

from core_graph_ledger import GraphLedger, StateNode


class LedgerPersist:
    def __init__(self, db_path: str) -> None:
        assert isinstance(db_path, str) and len(db_path) > 0, "Fail-fast: db_path must be non-empty str"
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            "\n            CREATE TABLE IF NOT EXISTS dag_nodes (\n                node_id    TEXT PRIMARY KEY,\n                parent_id  TEXT NOT NULL,\n                claim      TEXT NOT NULL,\n                payload_hash TEXT NOT NULL\n            )\n        "
        )
        self.conn.commit()

    def io_persist_ledger(self, ledger: GraphLedger) -> int:
        cursor = self.conn.cursor()
        inserted = 0
        for crdt_entry in ledger.crdt.to_dict().values():
            node_data = crdt_entry["value"]
            node = StateNode(**node_data)
            cursor.execute(
                "INSERT OR IGNORE INTO dag_nodes (node_id, parent_id, claim, payload_hash) VALUES (?, ?, ?, ?)",
                (node.node_id, node.parent_id, node.claim_summary, node.payload_hash),
            )
            inserted += cursor.rowcount
        self.conn.commit()
        return inserted

    def io_load_ledger(self) -> GraphLedger:
        cursor = self.conn.execute("SELECT node_id, parent_id, claim, payload_hash FROM dag_nodes")
        rows = cursor.fetchall()
        ledger = GraphLedger()
        if not rows:
            return ledger
        row_map: dict[str, tuple[str, str, str, str]] = {}
        for node_id, parent_id, claim, payload_hash in rows:
            row_map[node_id] = (node_id, parent_id, claim, payload_hash)
        inserted: set[str] = set()
        progress = True
        while progress and len(inserted) < len(row_map):
            progress = False
            for node_id, (nid, parent_id, claim, payload_hash) in row_map.items():
                if node_id in inserted:
                    continue
                if parent_id == ledger.genesis_id or parent_id in inserted:
                    node = StateNode(node_id=nid, parent_id=parent_id, claim_summary=claim, payload_hash=payload_hash)
                    ledger.crdt.set(nid, asdict(node), ledger._clock())
                    inserted.add(nid)
                    progress = True
        if len(inserted) != len(row_map):
            orphans = set(row_map.keys()) - inserted
            raise ValueError(
                f"Fail-fast: {len(orphans)} orphan nodes detected in DB, DAG integrity violated: {orphans}"
            )
        return ledger

    def io_node_count(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM dag_nodes")
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self.conn.close()
