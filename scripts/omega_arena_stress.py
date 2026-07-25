import logging
import argparse
import os
import random
import sqlite3
import sys
import threading
import time
import traceback
import uuid
from typing import Any
import babylon60.database.core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'strike_rs', 'target', 'debug')))
try:
    import strike_rs
except ImportError:
    logging.info('FATAL: Cannot import strike_rs. Make sure to build it with maturin or run python from a suitable environment.', file=sys.stderr)
    sys.exit(1)

def run_worker(worker_id: int, kernel: Any, duration: int, stats: dict[str, int], lock: threading.Lock) -> None:
    end_time = time.time() + duration
    ops = 0
    atms_ops = 0
    ledger_ops = 0
    vault_read_ops = 0
    while time.time() < end_time:
        try:
            choice = random.random()
            env_id = f'env_stress_{worker_id}'
            if choice < 0.4:
                stmt = f'Conjecture {uuid.uuid4()}'
                kernel.assert_knowledge(stmt, f'sensor_{worker_id}', env_id)
                kernel.contradict_knowledge(stmt, env_id)
                atms_ops += 1
            elif choice < 0.7:
                stmt = f'Blob {uuid.uuid4().hex * 10}'
                kernel.assert_knowledge(stmt, f'sensor_{worker_id}', env_id)
                ledger_ops += 1
            elif choice < 0.9:
                stmt = f'Fact {uuid.uuid4()}'
                kernel.assert_knowledge(stmt, f'sensor_{worker_id}', env_id)
                ledger_ops += 1
            else:
                kernel.is_believed(f'Fact {uuid.uuid4()}')
                kernel.contradiction_free(f'Fact {uuid.uuid4()}')
                vault_read_ops += 1
            ops += 1
        except RuntimeError as e:
            logging.info(f'Worker {worker_id} panicked: {e}')
            traceback.print_exc()
            with lock:
                stats['panics'] += 1
            break
    with lock:
        stats['ops'] += ops
        stats['atms_ops'] += atms_ops
        stats['ledger_ops'] += ledger_ops
        stats['vault_read_ops'] += vault_read_ops
        stats['workers_done'] += 1

def main() -> None:
    parser = argparse.ArgumentParser(description='Omega Arena Lite - Stress test for GIL-Bypass')
    parser.add_argument('--workers', type=int, default=10, help='Number of concurrent workers')
    parser.add_argument('--duration', type=str, default='1m', help='Duration of test (e.g. 1m, 10s)')
    args = parser.parse_args()
    unit = args.duration[-1]
    val = int(args.duration[:-1])
    if unit == 'm':
        duration_sec = val * 60
    elif unit == 's':
        duration_sec = val
    else:
        duration_sec = val
    db_path = 'stress_ledger.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    logging.info('[VECTOR 3] Initiating Omega Arena Lite Stress Test')
    logging.info(f'Workers: {args.workers}')
    logging.info(f'Duration: {duration_sec}s')
    try:
        kernel = strike_rs.CortexKernel(db_path)
    except RuntimeError as e:
        logging.info(f'FATAL: Failed to init CortexKernel: {e}')
        return
    stats = {'ops': 0, 'atms_ops': 0, 'ledger_ops': 0, 'vault_read_ops': 0, 'panics': 0, 'workers_done': 0}
    lock = threading.Lock()
    threads = []
    start_time = time.time()
    for i in range(args.workers):
        t = threading.Thread(target=run_worker, args=(i, kernel, duration_sec, stats, lock))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    elapsed = time.time() - start_time
    logging.info('\n--- RESULTS ---')
    logging.info(f"Total ops: {stats['ops']} ({stats['ops'] / elapsed:.2f} ops/sec)")
    logging.info(f"ATMS ops: {stats['atms_ops']}")
    logging.info(f"Ledger ops: {stats['ledger_ops']}")
    logging.info(f"Vault Read ops: {stats['vault_read_ops']}")
    logging.info(f"Panics: {stats['panics']}")
    try:
        conn = babylon60.database.core.connect_sync(db_path)
        cur = conn.cursor()
        cur.execute('PRAGMA integrity_check')
        res = cur.fetchone()[0]
        logging.info(f'SQLite Integrity: {res}')
        cur.execute('PRAGMA page_count')
        pages = cur.fetchone()[0]
        cur.execute('PRAGMA page_size')
        page_size = cur.fetchone()[0]
        logging.info(f'DB Size: {pages * page_size / 1024:.2f} KB')
        if os.path.exists(f'{db_path}-wal'):
            wal_size = os.path.getsize(f'{db_path}-wal')
            logging.info(f'WAL Size: {wal_size / 1024:.2f} KB')
        else:
            logging.info('WAL Size: 0 KB (No WAL file)')
    except sqlite3.Error as e:
        logging.info(f'SQLite Integrity Check Failed: {e}')
    if stats['panics'] > 0:
        logging.info('TEST FAILED: Workers panicked')
        sys.exit(1)
    else:
        logging.info('TEST PASSED: 0 panics, GIL-Bypass is stable.')
if __name__ == '__main__':
    main()