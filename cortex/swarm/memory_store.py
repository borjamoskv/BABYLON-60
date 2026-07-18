import os
import sqlite3
from typing import Dict, Any

class AgentMemory:
    """Memoria persistente BFT (SQLite WAL) para agentes soberanos."""
    
    def __init__(self, db_path: str = "agent_memory.db") -> None:
        self.conn = sqlite3.connect(db_path, isolation_level=None)
        # Habilitar WAL para concurrencia BFT segura (R10)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")
        self._init_table()
    
    def _init_table(self) -> None:
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY,
            issue_id INTEGER,
            agent_role TEXT,
            action TEXT,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
    
    def log(self, issue_id: int, agent_role: str, action: str, result: str) -> None:
        self.conn.execute(
            "INSERT INTO decisions (issue_id, agent_role, action, result) VALUES (?, ?, ?, ?)",
            (issue_id, agent_role, action, result)
        )
        # Auto-commit en modo isolation_level=None
    
    def query_similar(self, issue_text: str) -> list[Any]:
        # TODO: C5-REAL ChromaDB Vector Search embedding lookup
        cursor = self.conn.execute("SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 10")
        return cursor.fetchall()
