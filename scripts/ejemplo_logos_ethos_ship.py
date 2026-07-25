import logging
import hashlib
import subprocess
import time
import babylon60.database.core

def logos_transducer(raw_float_input: int) -> str:
    logging.info('[1] LOGOS: Transduciendo entropía flotante a Invariante Base-60...')
    total_seconds: int = int(raw_float_input * 3600)
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    ast_state: str = f'{h:02d}:{m:02d}:{s:02d}_BASE60'
    logging.info(f'    --> AST Colapsado: {ast_state}\n')
    return ast_state

def ethos_attestation(ast_state: str, lamport: int) -> str:
    logging.info('[2] ETHOS: Calculando CORTEX-TAINT SHA3-256 (Prueba de Trabajo)...')
    raw_taint: bytes = f'{ast_state}||borjamoskv||{lamport}'.encode()
    taint_hash: str = hashlib.sha3_256(raw_taint).hexdigest()
    logging.info(f'    --> Taint Criptográfico: {taint_hash}\n')
    return taint_hash

def ship_kinetic_collapse(ast_state: str, taint_hash: str) -> None:
    logging.info('[3] SHIP: Forzando colapso físico (DB WAL + Git Tag)...')
    import os
    root_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scratch_dir: str = os.path.join(root_dir, 'scratch')
    os.makedirs(scratch_dir, exist_ok=True)
    db_path: str = os.path.join(scratch_dir, 'c5_ejemplo_ship.db')
    with babylon60.database.core.connect_sync(db_path) as conn:
        conn.execute('PRAGMA journal_mode = WAL;')
        conn.execute('CREATE TABLE IF NOT EXISTS master_ledger (hash TEXT UNIQUE, payload TEXT)')
        conn.execute('INSERT OR IGNORE INTO master_ledger (hash, payload) VALUES (?, ?)', (taint_hash, ast_state))
        conn.commit()
    logging.info('    --> [DB WAL] Registro persistido atómicamente.')
    tag_name: str = f'SHIP-{int(time.time())}'
    subprocess.run(['git', 'tag', '-a', tag_name, '-m', 'Release Autopoiesis'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logging.info(f'    --> [Git Sentinel] Etiqueta pesada insertada: {tag_name}')

def main() -> None:
    logging.info('--- INICIANDO SECUENCIA LOGOS -> ETHOS -> SHIP ---\n')
    ast_invariant: str = logos_transducer(12.516666666666667)
    taint_signature: str = ethos_attestation(ast_invariant, lamport=42)
    ship_kinetic_collapse(ast_invariant, taint_signature)
    logging.info('\n[+] SECUENCIA COMPLETADA: CERO ANERGÍA ESTOCÁSTICA.')
if __name__ == '__main__':
    main()