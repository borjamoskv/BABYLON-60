import logging
import subprocess
import time
from pathlib import Path
WORKSPACE: Path = Path('/Users/borjafernandezangulo/30_BABYLON-60')
MEMORY_THRESHOLD_PAGES: int = 128000
POLL_INTERVAL: int = 15
MAX_WAL_BYTES: int = 10 * 1024 * 1024

def get_free_pages() -> int:
    import sys
    try:
        res = subprocess.run(['vm_stat'], capture_output=True, text=True)
        for line in res.stdout.split('\n'):
            if 'Pages free' in line:
                return int(line.split()[2].strip('.'))
    except (subprocess.SubprocessError, ValueError, IndexError):
        pass
    return sys.maxsize

def run_mapek_loop() -> None:
    logging.info('⚡ [C5-REAL] Autopoietic Exergy Daemon Initialized. 100% Autonomous.')
    while True:
        try:
            entropy_flags: list[str] = []
            free_pages = get_free_pages()
            if free_pages < MEMORY_THRESHOLD_PAGES:
                entropy_flags.append('MEMORY_PRESSURE')
            wals_to_collapse: list[Path] = []
            for db_path in WORKSPACE.rglob('*.db'):
                if '.venv' in db_path.parts or 'target' in db_path.parts:
                    continue
                wal_path = db_path.with_name(db_path.name + '-wal')
                if wal_path.exists() and wal_path.stat().st_size > MAX_WAL_BYTES:
                    wals_to_collapse.append(db_path)
            if wals_to_collapse:
                entropy_flags.append('WAL_FRAGMENTATION')
            stale_locks: list[Path] = list((WORKSPACE / '.git').glob('**/*.lock'))
            if stale_locks:
                entropy_flags.append('DEADLOCKS_DETECTED')
            if entropy_flags:
                logging.info(f"[{time.strftime('%H:%M:%S')}] Entropy Detected: {', '.join(entropy_flags)}")
                if 'DEADLOCKS_DETECTED' in entropy_flags:
                    for lock in stale_locks:
                        try:
                            lock.unlink()
                            logging.info(f'  [-] Purged stale lock: {lock.name}')
                        except OSError:
                            pass
                if 'WAL_FRAGMENTATION' in entropy_flags:
                    for db in wals_to_collapse:
                        subprocess.run(['sqlite3', str(db), 'PRAGMA wal_checkpoint(TRUNCATE);'], capture_output=True)
                        logging.info(f'  [-] Collapsed WAL for: {db.name}')
                if 'MEMORY_PRESSURE' in entropy_flags:
                    subprocess.run(['osascript', '-e', 'do shell script "purge"'], capture_output=True)
                    subprocess.run(['killall', '-9', 'mediaanalysisd', 'studentd'], capture_output=True)
                    logging.info('  [-] Executed Kinetic OS Purge.')
        except (OSError, subprocess.SubprocessError) as e:
            logging.info(f'[!] Daemon Fault (recoverable): {e}')
        time.sleep(POLL_INTERVAL)
if __name__ == '__main__':
    run_mapek_loop()