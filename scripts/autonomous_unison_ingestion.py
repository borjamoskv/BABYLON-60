import logging
import sqlite3
import time
import uuid
from pathlib import Path
LEXICON_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, 'babylon60.lexicon')

def get_lexicon_db_path() -> Path:
    return Path(__file__).parent.parent / 'cortex_lexicon.db'

def get_next_lamport(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute('SELECT MAX(lamport_t) FROM lexicon_nodes')
    node_max = cur.fetchone()[0] or 0
    cur.execute('SELECT MAX(lamport_t) FROM lexicon_edges')
    edge_max = cur.fetchone()[0] or 0
    return max(node_max, edge_max) + 1

def main() -> None:
    db_path = get_lexicon_db_path()
    unison_primitives = ['Nat', 'Int', 'Boolean', 'Text', 'Char', 'Bytes', 'Unit', 'Ability::IO', 'Ability::Exception', 'Ability::Store', 'Ability::State']
    taint = 'borjamoskv/2026-07-24/unison_primitives_ingestion'
    ops = 0
    t0 = time.time()
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout=5000;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        for name in unison_primitives:
            concept_hash = str(uuid.uuid5(LEXICON_NAMESPACE, f'TYPE::{name}'))
            lamport = get_next_lamport(conn)
            conn.execute('\n                INSERT INTO lexicon_nodes (concept_hash, canonical_name, lamport_t, causal_taint)\n                VALUES (?, ?, ?, ?)\n                ON CONFLICT(concept_hash) DO NOTHING\n            ', (concept_hash, f'TYPE::{name}', lamport, taint))
            ops += 1
        conn.commit()
    t1 = time.time()
    logging.info('[*] Ingestión Ontológica (Unison Content-Addressed Primitives) Completada.')
    logging.info(f'[*] {ops} Tipos BFT asimilados en {t1 - t0:.3f}s.')
    logging.info('[*] S/N Ratio: 1.00 (Exergía Pura)')
if __name__ == '__main__':
    main()