import sqlite3
import subprocess
from pathlib import Path


def get_all_sqlite_dbs(root_dir: Path) -> list[Path]:
    return list(root_dir.rglob('*.db')) + list(root_dir.rglob('*.sqlite3'))

def execute_wal_checkpoint(db_path: Path) -> None:
    print(f'[*] Executing WAL TRUNCATE checkpoint on {db_path}')
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        cursor = conn.cursor()
        cursor.execute('PRAGMA wal_checkpoint(TRUNCATE);')
        result = cursor.fetchone()
        print(f'    -> Result: {result}')
    except sqlite3.Error as e:
        print(f'    -> Error: {e}')
    finally:
        conn.close()

def purge_git_locks(root_dir: Path) -> None:
    git_dir = root_dir / '.git'
    if not git_dir.exists():
        return
    for lock_file in git_dir.rglob('*.lock'):
        print(f'[*] Purging orphan git lock: {lock_file}')
        lock_file.unlink()

def run_ethos_validation() -> None:
    print('[*] Executing Cryptographic ETHOS Validation (Invariants Check)...')
    result = subprocess.run(['uv', 'run', 'pytest', 'tests/'], capture_output=True, text=True)
    if result.returncode != 0:
        print('[-] ETHOS Validation FAILED:')
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError('ETHOS Validation failed. Cannot seal.')
    print('[+] ETHOS Validation PASSED.')

def execute_terminal_seal() -> None:
    root = Path(__file__).resolve().parent.parent
    print('=== BEGIN TERMINAL SEAL PROTOCOL (INV_C5_16) ===')
    purge_git_locks(root)
    dbs = get_all_sqlite_dbs(root)
    for db in dbs:
        execute_wal_checkpoint(db)
    run_ethos_validation()
    print('=== TERMINAL SEAL PROTOCOL COMPLETED ===')
if __name__ == '__main__':
    execute_terminal_seal()