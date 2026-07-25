import logging
import sqlite3
import subprocess
from pathlib import Path

def get_all_sqlite_dbs(root_dir: Path) -> list[Path]:
    return list(root_dir.rglob('*.db')) + list(root_dir.rglob('*.sqlite3'))

def execute_wal_checkpoint(db_path: Path) -> None:
    logging.info(f'[*] Executing WAL TRUNCATE checkpoint on {db_path}')
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cursor = conn.cursor()
        cursor.execute('PRAGMA wal_checkpoint(TRUNCATE);')
        result = cursor.fetchone()
        logging.info(f'    -> Result: {result}')
    except sqlite3.Error as e:
        logging.info(f'    -> Error: {e}')
    finally:
        conn.close()

def purge_git_locks(root_dir: Path) -> None:
    git_dir = root_dir / '.git'
    if not git_dir.exists():
        return
    for lock_file in git_dir.rglob('*.lock'):
        logging.info(f'[*] Purging orphan git lock: {lock_file}')
        lock_file.unlink()

def run_ethos_validation() -> None:
    logging.info('[*] Executing Cryptographic ETHOS Validation (Invariants Check)...')
    result = subprocess.run(['uv', 'run', 'pytest', 'tests/'], capture_output=True, text=True)
    if result.returncode != 0:
        logging.info('[-] ETHOS Validation FAILED:')
        logging.info(result.stdout)
        logging.info(result.stderr)
        raise RuntimeError('ETHOS Validation failed. Cannot seal.')
    logging.info('[+] ETHOS Validation PASSED.')

def execute_terminal_seal() -> None:
    root = Path(__file__).resolve().parent.parent
    logging.info('=== BEGIN TERMINAL SEAL PROTOCOL (INV_C5_16) ===')
    purge_git_locks(root)
    dbs = get_all_sqlite_dbs(root)
    for db in dbs:
        execute_wal_checkpoint(db)
    run_ethos_validation()
    logging.info('=== TERMINAL SEAL PROTOCOL COMPLETED ===')
if __name__ == '__main__':
    execute_terminal_seal()