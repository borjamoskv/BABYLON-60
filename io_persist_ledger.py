# io_persist_ledger.py
# Execution Protocol: SQLite WAL persistence layer for the DAG GraphLedger
# Prefix: io_ (disk I/O operations, non-pure)

import sqlite3
from typing import Optional
from core_graph_ledger import GraphLedger, StateNode


class LedgerPersist:
    """
    SQLite WAL persistence adapter for GraphLedger.
    Writes are atomic (single transaction per batch).
    Reads reconstruct the full in-memory DAG from disk.
    """
    def __init__(self, db_path: str) -> None:
        assert isinstance(db_path, str) and len(db_path) > 0, "Fail-fast: db_path must be non-empty str"
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._init_schema()

    def _init_schema(self) -> None:
        """Pre: conn open -> Exec: CREATE TABLE IF NOT EXISTS -> Post: schema ready."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dag_nodes (
                node_id    TEXT PRIMARY KEY,
                parent_id  TEXT NOT NULL,
                claim      TEXT NOT NULL,
                payload_hash TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def io_persist_ledger(self, ledger: GraphLedger) -> int:
        """
        Pre: ledger with N nodes in memory
        Exec: INSERT OR IGNORE each node into SQLite (idempotent)
        Post: returns count of newly persisted nodes
        """
        cursor = self.conn.cursor()
        inserted = 0
        for node in ledger.nodes.values():
            cursor.execute(
                "INSERT OR IGNORE INTO dag_nodes (node_id, parent_id, claim, payload_hash) VALUES (?, ?, ?, ?)",
                (node.node_id, node.parent_id, node.claim_summary, node.payload_hash)
            )
            inserted += cursor.rowcount
        self.conn.commit()
        return inserted

    def io_load_ledger(self) -> GraphLedger:
        """
        Pre: SQLite DB with dag_nodes table
        Exec: SELECT all rows, reconstruct GraphLedger in topological order
        Post: returns fully populated GraphLedger || raise ValueError on broken chain
        """
        cursor = self.conn.execute("SELECT node_id, parent_id, claim, payload_hash FROM dag_nodes")
        rows = cursor.fetchall()

        ledger = GraphLedger()
        if not rows:
            return ledger

        # Index rows by node_id for topological reconstruction
        row_map: dict[str, tuple[str, str, str, str]] = {}
        for node_id, parent_id, claim, payload_hash in rows:
            row_map[node_id] = (node_id, parent_id, claim, payload_hash)

        # Topological insertion: process nodes whose parent is genesis or already inserted
        inserted: set[str] = set()
        progress = True
        while progress and len(inserted) < len(row_map):
            progress = False
            for node_id, (nid, parent_id, claim, payload_hash) in row_map.items():
                if node_id in inserted:
                    continue
                if parent_id == ledger.genesis_id or parent_id in inserted:
                    node = StateNode(
                        node_id=nid,
                        parent_id=parent_id,
                        claim_summary=claim,
                        payload_hash=payload_hash
                    )
                    ledger.nodes[nid] = node
                    inserted.add(nid)
                    progress = True

        if len(inserted) != len(row_map):
            orphans = set(row_map.keys()) - inserted
            raise ValueError(f"Fail-fast: {len(orphans)} orphan nodes detected in DB, DAG integrity violated: {orphans}")

        return ledger

    def io_node_count(self) -> int:
        """Pre: conn open -> Exec: COUNT(*) -> Post: int."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM dag_nodes")
        return cursor.fetchone()[0]

    def close(self) -> None:
        self.conn.close()
