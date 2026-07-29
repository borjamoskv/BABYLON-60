"""
C5-REAL: Artist Cortex Engine
Orchestrates aesthetic embeddings and thermodynamic artifact metrics using sqlite-vec.
"""

import sqlite3
import struct

# Taint Engine and Ledger dependencies might be injected here per BABYLON-60 architecture
# For structural isolation, we define the causal logic locally.


class ArtistCortexEngine:
    def __init__(self, db_path: str = "artist_cortex.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes connection and loads sqlite-vec."""
        self.conn = sqlite3.connect(self.db_path)
        if hasattr(self.conn, "enable_load_extension"):
            self.conn.enable_load_extension(True)
        try:
            # Requires sqlite-vec to be installed on the system paths
            import sqlite_vec

            sqlite_vec.load(self.conn)
        except ImportError:
            # Fallback or strict error depending on env
            pass
        self.conn.row_factory = sqlite3.Row

    def apply_migrations(self, sql_paths: list[str]):
        """Executes the foundational C5-REAL migrations."""
        cursor = self.conn.cursor()
        for path in sql_paths:
            with open(path, encoding="utf-8") as f:
                cursor.executescript(f.read())
        self.conn.commit()

    def calculate_thermodynamics(
        self, t0_ms: int, t1_ms: int, input_entropy: float, model_confidence: float
    ) -> dict[str, float]:
        """
        Calculates Exergy metrics based on execution friction and output confidence.
        """
        friction_ms = t1_ms - t0_ms
        # Heuristic causal mappings
        originality_raw = min(1.0, max(0.0, input_entropy * 1.2))
        attention_yield = min(1.0, max(0.0, model_confidence * 0.9))

        return {
            "friction_ms": friction_ms,
            "originality_raw": originality_raw,
            "attention_yield": attention_yield,
        }

    def serialize_embedding(self, vector: list[float]) -> bytes:
        """Serializes a float array to sqlite-vec binary format."""
        return struct.pack(f"{len(vector)}f", *vector)

    def insert_artifact(
        self,
        session_id: int,
        artifact_key: str,
        artifact_type: str,
        content: str,
        aesthetic_hash: str,
        t0_ms: int,
        t1_ms: int,
        input_entropy: float,
        model_confidence: float,
        vector_1536: list[float],
    ) -> int:
        """
        Inserts an artifact, triggers metric computation, and writes to the vec0 store.
        """
        metrics = self.calculate_thermodynamics(t0_ms, t1_ms, input_entropy, model_confidence)

        cursor = self.conn.cursor()

        # 1. Insert Artifact
        cursor.execute(
            """
            INSERT INTO cortex_artifacts (
                session_id, artifact_key, artifact_type, content,
                originality_raw, friction_ms, attention_yield, aesthetic_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                artifact_key,
                artifact_type,
                content,
                metrics["originality_raw"],
                metrics["friction_ms"],
                metrics["attention_yield"],
                aesthetic_hash,
            ),
        )

        artifact_id = cursor.lastrowid

        # 2. Insert Embedding Mapping
        embedding_key = f"emb_{artifact_key}"
        cursor.execute(
            """
            INSERT INTO cortex_embedding_map (
                artifact_id, embedding_key, model_name, dims
            ) VALUES (?, ?, ?, ?)
        """,
            (artifact_id, embedding_key, "default-1536", len(vector_1536)),
        )

        # 3. Write to sqlite-vec vec0 Virtual Table
        binary_emb = self.serialize_embedding(vector_1536)
        cursor.execute(
            """
            INSERT INTO cortex_embeddings (rowid, embedding)
            VALUES (?, ?)
        """,
            (artifact_id, binary_emb),
        )

        self.conn.commit()
        return artifact_id

    def suntsitu_prune(
        self, attention_threshold: float = 0.2, originality_threshold: float = 0.1
    ) -> int:
        """
        M5 Thermodynamic Expulsion (Suntsitu)
        Purges low-exergy or rejected artifacts from the system to maintain thermodynamic vacuum.
        Enforces structural isomorphism (VEC-0) by manually cleaning the vec0 virtual table
        as it does not support Foreign Key ON DELETE CASCADE.
        """
        cursor = self.conn.cursor()

        # Identify low-exergy artifacts
        cursor.execute(
            """
            SELECT id FROM cortex_artifacts
            WHERE attention_yield < ? OR originality_raw < ?
        """,
            (attention_threshold, originality_threshold),
        )

        rows = cursor.fetchall()
        if not rows:
            return 0

        artifact_ids = [row["id"] for row in rows]
        placeholders = ",".join("?" for _ in artifact_ids)

        # 1. Purge from vec0 (VEC-0 integrity invariant)
        cursor.execute(
            f"DELETE FROM cortex_embeddings WHERE rowid IN ({placeholders})", artifact_ids
        )

        # 2. Purge from embedding map
        cursor.execute(
            f"DELETE FROM cortex_embedding_map WHERE artifact_id IN ({placeholders})", artifact_ids
        )

        # 3. Purge from artifacts
        cursor.execute(f"DELETE FROM cortex_artifacts WHERE id IN ({placeholders})", artifact_ids)

        self.conn.commit()
        return len(artifact_ids)

    def close(self):
        self.conn.close()
