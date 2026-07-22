"""
C5-REAL Agent Memory Store with BFT SQLite Ledger and Chroma Vector Store.
"""

import hashlib
import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "../../db/memory.db")
DEFAULT_CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../../db/chroma_memory")


class AgentMemory:
    def __init__(
        self, db_path: str = DEFAULT_DB_PATH, chroma_path: str = DEFAULT_CHROMA_PATH
    ) -> None:
        is_test = (
            "PYTEST_CURRENT_TEST" in os.environ
            or os.environ.get("CORTEX_TEST_MODE") == "1"
        )
        if is_test and db_path == DEFAULT_DB_PATH:
            db_path = ":memory:"

        self.conn = sqlite3.connect(db_path, isolation_level=None)
        # Habilitar WAL para concurrencia BFT segura (R10)
        if db_path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=10000;")
        self._init_table()

        self.chroma_client: Any = None
        self.collection: Any = None

        try:
            import chromadb
            from chromadb.config import Settings

            try:
                import posthog  # type: ignore[import-not-found]  # pyright: ignore[reportMissingImports]
                posthog.disabled = True

                def _silent_capture(*args: Any, **kwargs: Any) -> None:
                    pass

                setattr(posthog, "capture", _silent_capture)
                if hasattr(posthog, "Posthog"):
                    setattr(posthog.Posthog, "capture", _silent_capture)
            except Exception:
                pass

            try:
                import chromadb.telemetry.product.posthog

                def _silent_product_capture(self: Any, event: Any = None) -> None:
                    pass

                setattr(
                    chromadb.telemetry.product.posthog.Posthog,
                    "capture",
                    _silent_product_capture,
                )
            except Exception:
                pass

            chroma_settings = Settings(anonymized_telemetry=False)

            if (
                "PYTEST_CURRENT_TEST" in os.environ
                or os.environ.get("CORTEX_TEST_MODE") == "1"
            ):
                self.chroma_client = chromadb.EphemeralClient(settings=chroma_settings)
            else:
                self.chroma_client = chromadb.PersistentClient(
                    path=chroma_path, settings=chroma_settings
                )
            self.collection = self.chroma_client.get_or_create_collection(
                name="agent_memory"
            )
        except (ImportError, Exception):
            self.chroma_client = None
            self.collection = None

    def _init_table(self) -> None:
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY,
            issue_id INTEGER,
            agent_role TEXT,
            action TEXT,
            result TEXT,
            prev_hash TEXT UNIQUE,
            cortex_taint TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Trigger para garantizar inmutabilidad (Ω11)
        self.conn.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_update_decisions
        BEFORE UPDATE ON decisions
        BEGIN
            SELECT RAISE(ABORT, 'CORTEX_LEDGER_ERROR: Updates are strictly forbidden in C5-REAL ledger.');
        END;
        """)

        self.conn.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_delete_decisions
        BEFORE DELETE ON decisions
        BEGIN
            SELECT RAISE(ABORT, 'CORTEX_LEDGER_ERROR: Deletions are strictly forbidden in C5-REAL ledger.');
        END;
        """)

    def _get_last_hash(self) -> str:
        cursor = self.conn.execute(
            "SELECT cortex_taint FROM decisions ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return (
            str(row[0])
            if row
            else "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000"
        )

    def log(self, issue_id: int, agent_role: str, action: str, result: str) -> str:
        for attempt in range(5):
            try:
                self.conn.execute("BEGIN IMMEDIATE")
                prev_hash = self._get_last_hash()

                timestamp_iso = datetime.now(timezone.utc).isoformat()

                raw_payload = f"{prev_hash}|{issue_id}|{agent_role}|{action}|{result}|{timestamp_iso}".encode(
                    "utf-8"
                )
                cortex_taint = f"CORTEX-TAINT:borjamoskv:swarm_ledger:{timestamp_iso}:{hashlib.sha3_256(raw_payload).hexdigest()}"

                self.conn.execute(
                    "INSERT INTO decisions (issue_id, agent_role, action, result, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?)",
                    (issue_id, agent_role, action, result, prev_hash, cortex_taint),
                )

                if self.collection is not None:
                    doc_content = f"Issue: {issue_id}. Role: {agent_role}. Action: {action}. Result: {result}."
                    try:
                        self.collection.add(
                            documents=[doc_content],
                            metadatas=[
                                {
                                    "issue_id": issue_id,
                                    "agent_role": agent_role,
                                    "cortex_taint": cortex_taint,
                                    "timestamp": timestamp_iso,
                                }
                            ],
                            ids=[cortex_taint],
                        )
                    except (AttributeError, ValueError, RuntimeError, OSError, TypeError, KeyError):
                        pass

                self.conn.execute("COMMIT")
                return cortex_taint
            except sqlite3.OperationalError as e:
                try:
                    self.conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                if "locked" in str(e).lower() and attempt < 4:
                    time.sleep(0.05 * (2 ** attempt))
                    continue
                raise
            except Exception:
                try:
                    self.conn.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        raise RuntimeError("AgentMemory log failed after 5 retry attempts due to database lock")

    def query_similar(self, issue_text: str) -> list[Any]:
        if self.collection is None:
            return []
        try:
            results = self.collection.query(query_texts=[issue_text], n_results=10)
            docs = results.get("documents")
            if docs and isinstance(docs, list) and len(docs) > 0 and isinstance(docs[0], list):
                return list(docs[0])
            return []
        except (AttributeError, ValueError, RuntimeError, OSError, TypeError, KeyError):
            return []
