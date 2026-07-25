import sqlite3
import uuid
from pathlib import Path

LEXICON_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "babylon60.lexicon")


def get_lexicon_db_path() -> Path:
    return Path(__file__).parent.parent / "cortex_lexicon.db"


def init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(
            "\n        CREATE TABLE IF NOT EXISTS lexicon_nodes (\n            concept_hash TEXT PRIMARY KEY,\n            canonical_name TEXT NOT NULL,\n            lamport_t int NOT NULL,\n            causal_taint TEXT NOT NULL\n        )\n        "
        )
        conn.execute(
            "\n        CREATE TABLE IF NOT EXISTS lexicon_edges (\n            edge_hash TEXT PRIMARY KEY,\n            source_hash TEXT NOT NULL,\n            target_hash TEXT NOT NULL,\n            relation_type TEXT NOT NULL,\n            lamport_t int NOT NULL,\n            causal_taint TEXT NOT NULL,\n            FOREIGN KEY(source_hash) REFERENCES lexicon_nodes(concept_hash),\n            FOREIGN KEY(target_hash) REFERENCES lexicon_nodes(concept_hash),\n            UNIQUE(source_hash, target_hash, relation_type)\n        )\n        "
        )


def get_next_lamport(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT MAX(lamport_t) FROM lexicon_nodes")
    node_max = cur.fetchone()[0] or 0
    cur.execute("SELECT MAX(lamport_t) FROM lexicon_edges")
    edge_max = cur.fetchone()[0] or 0
    return max(node_max, edge_max) + 1


def insert_concept(conn: sqlite3.Connection, name: str, taint: str) -> str:
    concept_hash = str(uuid.uuid5(LEXICON_NAMESPACE, name))
    lamport = get_next_lamport(conn)
    conn.execute(
        "\n        INSERT INTO lexicon_nodes (concept_hash, canonical_name, lamport_t, causal_taint)\n        VALUES (?, ?, ?, ?)\n        ON CONFLICT(concept_hash) DO NOTHING\n    ",
        (concept_hash, name, lamport, taint),
    )
    return concept_hash


def insert_edge(conn: sqlite3.Connection, src: str, tgt: str, rel: str, taint: str) -> None:
    edge_id = f"{src}::{rel}::{tgt}"
    edge_hash = str(uuid.uuid5(LEXICON_NAMESPACE, edge_id))
    lamport = get_next_lamport(conn)
    conn.execute(
        "\n        INSERT INTO lexicon_edges (edge_hash, source_hash, target_hash, relation_type, lamport_t, causal_taint)\n        VALUES (?, ?, ?, ?, ?, ?)\n        ON CONFLICT DO NOTHING\n    ",
        (edge_hash, src, tgt, rel, lamport, taint),
    )


def main() -> None:
    db_path = get_lexicon_db_path()
    init_db(db_path)
    taint = "borjamoskv/2026-07-24/lexicon_bootstrap"
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        c_action = insert_concept(conn, "ACTION", taint)
        c_entity = insert_concept(conn, "ENTITY", taint)
        c_exergy = insert_concept(conn, "EXERGY", taint)
        c_anergy = insert_concept(conn, "ANERGY", taint)
        c_bft = insert_concept(conn, "BYZANTINE_FAULT_TOLERANCE", taint)
        c_truth = insert_concept(conn, "TRUTH_C5", taint)
        insert_edge(conn, c_action, c_entity, "MUTATES", taint)
        insert_edge(conn, c_action, c_exergy, "MAXIMIZES", taint)
        insert_edge(conn, c_anergy, c_bft, "THREATENS", taint)
        insert_edge(conn, c_truth, c_bft, "ANCHORS", taint)
        conn.commit()
    print(f"Lexicon crystallized at {db_path} con 6 base concepts.")


if __name__ == "__main__":
    main()
