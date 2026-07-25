import os
import sys

import yaml
from cryptography.fernet import Fernet

import babylon60.database.core

_BASE = os.path.dirname(os.path.abspath(__file__))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_BASE, '.env.vault'))
except ImportError:
    pass
VAULT_DIR = os.path.expandvars('$CORTEX_ROOT/20_VAULT')
VAULT_KEY = os.environ.get('CORTEX_VAULT_KEY')
DB_PATH = os.path.expandvars(os.environ.get('CORTEX_DB_PATH', os.path.join(_BASE, 'cortex_memory.db')))
MATRIZ_PATH = os.path.expandvars(os.environ.get('CORTEX_MATRIZ_PATH', os.path.join(VAULT_DIR, 'matriz_1000_primitivas.yaml.enc')))
ISOMORFISMOS_PATH = os.path.expandvars(os.environ.get('CORTEX_ISOMORFISMOS_PATH', os.path.join(VAULT_DIR, 'isomorfismos_cruzados_1000_primitivas.yaml.enc')))

def bootstrap_cortex() -> None:
    print('[CORTEX] Iniciando bootstrap de persistencia de base de datos...')
    if not VAULT_KEY:
        print('\x1b[1;31m[CORTEX APOPTOSIS]\x1b[0m CORTEX_VAULT_KEY is missing. C5-REAL Fail-Fast.', file=sys.stderr)
        sys.exit(1)
    master_ledger = os.path.join(_BASE, 'bft', 'master_ledger.db')
    if os.path.exists(master_ledger) or os.path.exists(DB_PATH):
        print(f'\x1b[1;31m[CORTEX APOPTOSIS]\x1b[0m Freezing Lock: Ledger {master_ledger} or {DB_PATH} already exists. Cannot mutate historical RO state.', file=sys.stderr)
        sys.exit(1)
    for path in [MATRIZ_PATH, ISOMORFISMOS_PATH]:
        if not os.path.exists(path):
            print(f'\x1b[1;31m[CORTEX APOPTOSIS]\x1b[0m Essential Config Missing: {path}. C5-REAL Fail-Fast.', file=sys.stderr)
            sys.exit(1)
    fernet = Fernet(VAULT_KEY)
    with open(MATRIZ_PATH, 'rb') as f:
        matriz_enc = f.read()
    matriz = yaml.safe_load(fernet.decrypt(matriz_enc))
    with open(ISOMORFISMOS_PATH, 'rb') as f:
        isomorfismos_enc = f.read()
    isomorfismos = yaml.safe_load(fernet.decrypt(isomorfismos_enc))
    conn = babylon60.database.core.connect_sync(DB_PATH)
    conn.execute('PRAGMA journal_mode = WAL;')
    conn.execute('PRAGMA busy_timeout = 5000;')
    cursor = conn.cursor()
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS L1_primitive_nodes (\n            id TEXT PRIMARY KEY,\n            theory TEXT,\n            dimension TEXT,\n            name TEXT,\n            access_count int DEFAULT 0,\n            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n        )\n    ')
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS L2_isomorphism_edges (\n            id TEXT PRIMARY KEY,\n            type TEXT,\n            source TEXT,\n            target TEXT,\n            weight int,\n            justification TEXT,\n            hits int DEFAULT 0,\n            last_used TIMESTAMP\n        )\n    ')
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS L3_inference_cache (\n            query_hash TEXT PRIMARY KEY,\n            active_mode TEXT,\n            retrieved_nodes TEXT,\n            applied_isomorphisms TEXT,\n            trace_payload TEXT,\n            hits int DEFAULT 0\n        )\n    ')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_l1_theory ON L1_primitive_nodes (theory);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_l2_source ON L2_isomorphism_edges (source);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_l2_target ON L2_isomorphism_edges (target);')
    primitives_inserted = 0
    for t_id, t_info in matriz['theories'].items():
        theory_name = t_info['name']
        for d_name, prims in t_info['dimensions'].items():
            for p_name in prims:
                p_id = f"{t_id}.{d_name.split('_')[0]}.{p_name}"
                cursor.execute('\n                    INSERT OR REPLACE INTO L1_primitive_nodes (id, theory, dimension, name)\n                    VALUES (?, ?, ?, ?)\n                ', (p_id, theory_name, d_name, p_name))
                primitives_inserted += 1
    isomorphisms_inserted = 0
    for iso in isomorfismos['isomorphisms']:
        if iso['type'] == 'Fusion-Operator':
            p_id = f"FUSION.{iso['name']}"
            cursor.execute("\n                INSERT OR REPLACE INTO L1_primitive_nodes (id, theory, dimension, name)\n                VALUES (?, 'FUSION', 'OPERATOR', ?)\n            ", (p_id, iso['name']))
            primitives_inserted += 1
            for idx, inp in enumerate(iso['inputs']):
                cursor.execute("\n                    INSERT OR REPLACE INTO L2_isomorphism_edges (id, type, source, target, weight, justification)\n                    VALUES (?, 'FUSION-INPUT', ?, ?, 1.0, ?)\n                ", (f"FUSE-{iso['name']}-{idx}", inp, p_id, iso['output_description']))
                isomorphisms_inserted += 1
        else:
            cursor.execute('\n                INSERT OR REPLACE INTO L2_isomorphism_edges (id, type, source, target, weight, justification)\n                VALUES (?, ?, ?, ?, ?, ?)\n            ', (iso['id'], iso['type'], iso['source'], iso['target'], iso.get('weight', 1.0), iso.get('justification', '')))
            isomorphisms_inserted += 1
    conn.commit()
    conn.close()
    print('[CORTEX] SQLite persistida exitosamente.')
    print(f'[CORTEX] Nodos Primitivos (L1) instanciados: {primitives_inserted}')
    print(f'[CORTEX] Enlaces Isomorfos (L2) instanciados: {isomorphisms_inserted}')
if __name__ == '__main__':
    bootstrap_cortex()