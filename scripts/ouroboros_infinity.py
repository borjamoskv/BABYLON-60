import argparse
import hashlib
import json
import os
import signal
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DB_PATH: Path = PROJECT_ROOT / 'scripts' / 'cib_master_ledger.db'
CORTEX_DB_PATH: Path = PROJECT_ROOT / 'cortex' / 'engine' / 'nexus_anchors.db'


def get_db_connection(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    return conn


def init_ledger() -> None:
    with get_db_connection() as conn:
        conn.execute('\n            CREATE TABLE IF NOT EXISTS ouroboros_events (\n                event_id TEXT PRIMARY KEY,\n                protocol TEXT NOT NULL,\n                target TEXT,\n                exergy_delta REAL NOT NULL,\n                timestamp INTEGER NOT NULL,\n                causal_hash TEXT NOT NULL\n            )\n        ')


def log_event(protocol: str, target: str, exergy_delta: float) -> str:
    init_ledger()
    ts = int(time.time() * 1000)
    raw = f'{protocol}|{target}|{exergy_delta}|{ts}'.encode('utf-8')
    causal_hash = hashlib.blake2b(raw, digest_size=16).hexdigest()
    event_id = f'ouro-{ts}'
    with get_db_connection() as conn:
        conn.execute('\n            INSERT INTO ouroboros_events (event_id, protocol, target, exergy_delta, timestamp, causal_hash)\n            VALUES (?, ?, ?, ?, ?, ?)\n        ', (event_id, protocol, target, exergy_delta, ts, causal_hash))
    return causal_hash


def execute_pulse() -> dict[str, Any]:
    print('[OUROBOROS-∞] Executing Pulse (Entropy & Citadel Audit)...')
    alarms: list[str] = []
    large_files = 0
    for ext in ['*.py', '*.rs', '*.ts', '*.md']:
        for f in PROJECT_ROOT.rglob(ext):
            if '.git' in str(f) or 'node_modules' in str(f) or '.venv' in str(f):
                continue
            try:
                lines = len(f.read_text(errors='ignore').splitlines())
                if lines > 400 and f.name != '300_primitivas_external_compensation.yaml':
                    large_files += 1
                    if len(alarms) < 3:
                        alarms.append(f'High LOC ({lines}): {f.relative_to(PROJECT_ROOT)}')
            except Exception:
                os.kill(os.getpid(), signal.SIGKILL)
                raise RuntimeError('FAIL-FAST: General Exception intercepted.')
    uncommitted = 0
    try:
        uncommitted = len(subprocess.check_output(['git', '-C', str(PROJECT_ROOT), 'status', '-s']).splitlines())
        if uncommitted > 15:
            alarms.append(f'High uncommitted drift ({uncommitted} files)')
    except Exception:
        os.kill(os.getpid(), signal.SIGKILL)
        raise RuntimeError('FAIL-FAST: General Exception intercepted.')
    entropy_score = min(100, int(large_files * 2 + uncommitted * 1.5))
    status = '🟢 SOBERANO' if entropy_score < 20 else '🟡 DERIVA' if entropy_score < 40 else '🔴 COLAPSO'
    result: dict[str, Any] = {'entropy_score': entropy_score, 'status': status, 'large_files_count': large_files, 'uncommitted_drift': uncommitted, 'top_alarms': alarms}
    log_event('PULSE', str(PROJECT_ROOT), float(-entropy_score))
    return result


def execute_crystallize(target_md_path: str | None = None) -> dict[str, Any]:
    print('[OUROBOROS-∞] Executing CRYSTALLIZE Protocol (Linear Entropy Devourer)...')
    targets: list[Path] = []
    if target_md_path:
        p = Path(target_md_path)
        if p.exists():
            targets.append(p)
    else:
        for root_dir in [PROJECT_ROOT, Path.home() / '.gemini' / 'config' / 'skills']:
            if root_dir.exists():
                for md in root_dir.rglob('*.md'):
                    try:
                        content = md.read_text(errors='ignore')
                        if '### Ouroboros Auto-Injection' in content or 'Auto-Injection' in content:
                            targets.append(md)
                    except Exception:
                        os.kill(os.getpid(), signal.SIGKILL)
                        raise RuntimeError('FAIL-FAST: General Exception intercepted.')
    total_injections = 0
    consolidated_files: list[dict[str, object]] = []
    for md in targets:
        content = md.read_text(errors='ignore')
        injections = content.count('### Ouroboros Auto-Injection')
        if injections > 0:
            total_injections += injections
            consolidated_files.append({'file': str(md), 'linear_injections_found': injections})
            print(f'  -> Found {injections} linear injections in {md.name}. Ready for semantic merge.')
    exergy_gained = float(total_injections * 50.0)
    hash_id = log_event('CRYSTALLIZE', str(targets[0] if targets else 'global'), exergy_gained)
    return {'status': 'CRISTALIZADO', 'files_scanned': len(targets), 'total_linear_injections_detected': total_injections, 'exergy_gained': exergy_gained, 'ledger_hash': hash_id, 'details': consolidated_files}


def main() -> None:
    parser = argparse.ArgumentParser(description='OUROBOROS-∞ v3.0 C5-REAL Sovereign Engine')
    subparsers = parser.add_subparsers(dest='command', help='Master Protocol to execute')
    subparsers.add_parser('pulse', help='Check system entropy and report top alarms')
    cryst_parser = subparsers.add_parser('crystallize', help='Devour linear Auto-Injections and compress entropy')
    cryst_parser.add_argument('--target', '-t', help='Path to target markdown file to crystallize', default=None)
    args = parser.parse_args()
    if args.command == 'pulse' or not args.command:
        res = execute_pulse()
        print(f'\nResult: {json.dumps(res, indent=2, ensure_ascii=False)}')
    elif args.command == 'crystallize':
        res = execute_crystallize(args.target)
        print(f'\nResult: {json.dumps(res, indent=2, ensure_ascii=False)}')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()