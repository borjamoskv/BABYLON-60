import sqlite3
import uuid
from pathlib import Path

LEXICON_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "babylon60.lexicon")


class BFTLexicon:
    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            self.db_path = Path(__file__).parent.parent.parent / "cortex_lexicon.db"
        else:
            self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        with self._get_conn() as conn:
            conn.execute(
                "\n                CREATE TABLE IF NOT EXISTS lexicon_nodes (\n                    concept_hash TEXT PRIMARY KEY,\n                    canonical_name TEXT NOT NULL\n                )\n            "
            )
            conn.execute(
                "\n                CREATE TABLE IF NOT EXISTS lexicon_edges (\n                    source_hash TEXT,\n                    relation_type TEXT,\n                    target_hash TEXT,\n                    PRIMARY KEY (source_hash, relation_type, target_hash)\n                )\n            "
            )

    def _get_conn(self) -> sqlite3.Connection:
        from babylon60.database.core import connect_sync

        return connect_sync(self.db_path, synchronous="NORMAL")

    def get_concept_hash(self, canonical_name: str) -> str:
        return str(uuid.uuid5(LEXICON_NAMESPACE, canonical_name))

    def resolve_hash(self, concept_hash: str) -> str | None:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT canonical_name FROM lexicon_nodes WHERE concept_hash = ?", (concept_hash,))
            row = cur.fetchone()
            return row[0] if row else None

    def trace_edges(self, concept_hash: str) -> list[tuple[str, str]]:
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT relation_type, target_hash FROM lexicon_edges WHERE source_hash = ?", (concept_hash,)
            )
            return [(row[0], row[1]) for row in cur.fetchall()]
