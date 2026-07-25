from __future__ import annotations
import contextlib
import sqlite3
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from ..services.chain_verifier import verify_chain
from ..services.db_pool import connect_readonly
router = APIRouter(prefix='/api/ledger', tags=['ledger'])
_LEDGER_DB_CACHE: Path | None = None

def _find_ledger_db(project_root: Path) -> Path | None:
    global _LEDGER_DB_CACHE
    if _LEDGER_DB_CACHE is not None and _LEDGER_DB_CACHE.exists():
        return _LEDGER_DB_CACHE
    _LEDGER_DB_CACHE = _discover_ledger_db(project_root)
    return _LEDGER_DB_CACHE

def _discover_ledger_db(project_root: Path) -> Path | None:
    candidates = [project_root / 'master_ledger.db', project_root / 'babylon60' / 'bft' / 'ultrathink_ledger.db']
    for c in candidates:
        if c.exists():
            return c
    for db_file in sorted(project_root.glob('*.db')):
        try:
            with contextlib.closing(connect_readonly(db_file)) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ledger_entries'")
                if cursor.fetchone():
                    return db_file
        except sqlite3.DatabaseError:
            continue
    return None

def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent

@router.get('/stats')
def ledger_stats() -> dict[str, Any]:
    root = _get_project_root()
    db_path = _find_ledger_db(root)
    if not db_path:
        return {'exists': False, 'entries': 0, 'message': 'No ledger database found'}
    conn = connect_readonly(db_path)
    try:
        cursor = conn.execute('SELECT COUNT(*) as cnt FROM ledger_entries')
        total = cursor.fetchone()['cnt']
        latest: dict[str, Any] = {}
        if total > 0:
            cursor = conn.execute('SELECT entry_hash, lamport_t, created_at FROM ledger_entries ORDER BY seq DESC LIMIT 1')
            row = cursor.fetchone()
            latest = {'entry_hash': row['entry_hash'], 'lamport_t': row['lamport_t'], 'created_at': row['created_at']}
        return {'exists': True, 'db_path': db_path.name, 'entries': total, 'latest': latest}
    finally:
        conn.close()

@router.get('/entries')
def list_entries(limit: int=Query(50, ge=1, le=500), offset: int=Query(0, ge=0)) -> dict[str, Any]:
    root = _get_project_root()
    db_path = _find_ledger_db(root)
    if not db_path:
        raise HTTPException(404, 'No ledger database found')
    conn = connect_readonly(db_path)
    try:
        count_cursor = conn.execute('SELECT COUNT(*) as cnt FROM ledger_entries')
        total = count_cursor.fetchone()['cnt']
        cursor = conn.execute('SELECT seq, event_id, stream, entity_id, event_type, lamport_t, entry_hash, prev_hash, cortex_taint, created_at FROM ledger_entries ORDER BY seq DESC LIMIT ? OFFSET ?', (limit, offset))
        entries = []
        for row in cursor.fetchall():
            entries.append({'seq': row['seq'], 'event_id': row['event_id'], 'stream': row['stream'], 'entity_id': row['entity_id'], 'event_type': row['event_type'], 'lamport_t': row['lamport_t'], 'entry_hash': row['entry_hash'], 'prev_hash': row['prev_hash'], 'cortex_taint': row['cortex_taint'], 'created_at': row['created_at']})
        return {'entries': entries, 'total': total, 'limit': limit, 'offset': offset}
    finally:
        conn.close()

@router.get('/entry/{seq}')
def get_entry(seq: int) -> dict[str, Any]:
    root = _get_project_root()
    db_path = _find_ledger_db(root)
    if not db_path:
        raise HTTPException(404, 'No ledger database found')
    conn = connect_readonly(db_path)
    try:
        cursor = conn.execute('SELECT * FROM ledger_entries WHERE seq = ?', (seq,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(404, f'Entry seq={seq} not found')
        return dict(row)
    finally:
        conn.close()

@router.post('/verify')
def verify_ledger() -> dict[str, Any]:
    root = _get_project_root()
    db_path = _find_ledger_db(root)
    if not db_path:
        raise HTTPException(404, 'No ledger database found')
    return verify_chain(db_path)