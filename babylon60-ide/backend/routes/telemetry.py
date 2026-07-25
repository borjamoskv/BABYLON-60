from __future__ import annotations
import asyncio
import json
import time
from pathlib import Path
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
router = APIRouter(tags=['telemetry'])

def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent

def _collect_snapshot() -> dict[str, Any]:
    root = _get_project_root()
    db_files: list[dict[str, Any]] = []
    for db_file in sorted(root.glob('*.db')):
        try:
            size = db_file.stat().st_size
            db_files.append({'name': db_file.name, 'size_bytes': size, 'size_mb': round(size / (1024 * 1024), 2)})
        except OSError:
            continue
    total_db_size = sum((int(d['size_bytes']) for d in db_files))
    wal_files: list[dict[str, Any]] = []
    for wal in sorted(root.glob('*.db-wal')):
        try:
            size = wal.stat().st_size
            wal_files.append({'name': wal.name, 'size_bytes': size})
        except OSError:
            continue
    git_dir = root / '.git'
    git_info: dict[str, Any] = {'exists': git_dir.is_dir()}
    if git_dir.is_dir():
        try:
            pack_dir = git_dir / 'objects' / 'pack'
            if pack_dir.is_dir():
                pack_size = 0
                for f in pack_dir.iterdir():
                    try:
                        if f.is_file():
                            pack_size += f.stat().st_size
                    except OSError:
                        continue
                git_info['pack_size_mb'] = round(pack_size / (1024 * 1024), 2)
            head_file = git_dir / 'HEAD'
            if head_file.exists():
                git_info['head'] = head_file.read_text().strip()
        except OSError:
            git_info['head'] = '(no legible)'
    try:
        import resource
        import sys
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        rss_divisor = 1024 * 1024 if sys.platform == 'darwin' else 1024
        process_info = {'user_time_s': round(rusage.ru_utime, 2), 'system_time_s': round(rusage.ru_stime, 2), 'max_rss_mb': round(rusage.ru_maxrss / rss_divisor, 2)}
    except (ImportError, ValueError):
        process_info = {}
    return {'timestamp': time.time(), 'databases': db_files, 'total_db_size_mb': round(total_db_size / (1024 * 1024), 2), 'wal_files': wal_files, 'git': git_info, 'process': process_info, 'project_root': str(root)}

@router.get('/api/telemetry/snapshot')
def telemetry_snapshot() -> dict[str, Any]:
    return _collect_snapshot()

def _snapshot_signature(snap: dict[str, Any]) -> str:
    stable = {'databases': snap.get('databases'), 'total_db_size_mb': snap.get('total_db_size_mb'), 'wal_files': snap.get('wal_files'), 'git': snap.get('git')}
    return json.dumps(stable, sort_keys=True)

@router.websocket('/ws/telemetry')
async def telemetry_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    last_sig = ''
    beats_suppressed = 0
    try:
        while True:
            snapshot = await asyncio.to_thread(_collect_snapshot)
            sig = _snapshot_signature(snapshot)
            if sig != last_sig or beats_suppressed >= 14:
                await websocket.send_text(json.dumps(snapshot))
                last_sig = sig
                beats_suppressed = 0
            else:
                beats_suppressed += 1
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        pass