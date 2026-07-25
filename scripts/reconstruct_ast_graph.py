#!/usr/bin/env python3
import ast
import datetime
import sqlite3
import uuid
from pathlib import Path

# C5-REAL Invariants: WAL mode, causal_taint, Lamport ordering, UUIDv5
DB_PATH = Path("cib_ast_graph.db")

def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ast_nodes (
            id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            node_type TEXT NOT NULL,
            name TEXT NOT NULL,
            lineno INTEGER,
            causal_taint TEXT NOT NULL,
            lamport_t INTEGER NOT NULL UNIQUE
        )
    ''')

def _get_next_lamport(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(lamport_t) FROM ast_nodes").fetchone()
    return (row[0] or 0) + 1

def reconstruct_graph() -> None:
    target_dir = Path("babylon60")
    if not target_dir.exists():
        raise RuntimeError("INV_C5_07: babylon60 directory not found. Loud failure.")

    conn = sqlite3.connect(str(DB_PATH), isolation_level=None, timeout=5.0)
    _init_db(conn)

    # Begin traversal
    for py_file in target_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
        except SyntaxError:
            continue
            
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        causal_taint = f"borjamoskv/{now}/ast_reconstruction"
        
        nodes_to_insert = []
        current_lamport = _get_next_lamport(conn)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # UUIDv5 idempotency key (INV_BFT_04)
                node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"ast:{py_file}:{node.name}:{node.lineno}"))
                nodes_to_insert.append((
                    node_id,
                    str(py_file),
                    type(node).__name__,
                    node.name,
                    node.lineno,
                    causal_taint,
                    current_lamport
                ))
                current_lamport += 1

        if nodes_to_insert:
            conn.executemany('''
                INSERT OR IGNORE INTO ast_nodes 
                (id, file_path, node_type, name, lineno, causal_taint, lamport_t)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', nodes_to_insert)
            
    # Force WAL Checkpoint to physical disk
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()

if __name__ == "__main__":
    reconstruct_graph()
