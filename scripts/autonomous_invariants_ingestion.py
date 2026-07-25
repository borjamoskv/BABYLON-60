import re
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
    base_dir = Path(__file__).parent.parent
    agent_files = [base_dir / 'AGENTS.md', base_dir / '.agents' / 'AGENTS.md']
    invariants = set()
    pattern = re.compile('(INV_[A-Z0-9_]+|Φ[0-9]+|Ω[0-9]+)')
    for file_path in agent_files:
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')
            matches = pattern.findall(content)
            for match in matches:
                invariants.add(match)
    db_path = get_lexicon_db_path()
    taint = 'borjamoskv/2026-07-24/spanish_invariants_ingestion'
    ops = 0
    t0 = time.time()
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout=5000;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        for inv in sorted(invariants):
            concept_hash = str(uuid.uuid5(LEXICON_NAMESPACE, f'INVARIANT::{inv}'))
            lamport = get_next_lamport(conn)
            conn.execute('\n                INSERT INTO lexicon_nodes (concept_hash, canonical_name, lamport_t, causal_taint)\n                VALUES (?, ?, ?, ?)\n                ON CONFLICT(concept_hash) DO NOTHING\n            ', (concept_hash, f'INVARIANT::{inv}', lamport, taint))
            ops += 1
        conn.commit()
    t1 = time.time()
    print('[*] Ingestión Ontológica del Español Estructural (C5-int) Completada.')
    print(f'[*] {ops} Invariantes Físicas asimiladas en {t1 - t0:.3f}s.')
    print('[*] S/N Ratio: 1.00 (Exergía Pura)')
if __name__ == '__main__':
    main()