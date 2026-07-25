from __future__ import annotations
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from ..services import cortex_ledger

def _guard_local_origin(request: Request) -> None:
    origin = request.headers.get('origin')
    if not origin:
        return
    host = urlparse(origin).hostname or ''
    if origin.startswith(('chrome-extension://', 'moz-extension://')):
        return
    if host in ('localhost', '127.0.0.1', '::1'):
        return
    raise HTTPException(403, f"Origin '{origin}' no autorizado para mutar (solo localhost/Alcove)")
router = APIRouter(prefix='/api/cortex', tags=['cortex'], dependencies=[Depends(_guard_local_origin)])
ENTITY = 'operator/scratchpad'
NOTE = 'COGNITIVE_NOTE'
NOTE_DELETED = 'COGNITIVE_NOTE_DELETED'

class NoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    route: str = Field('', max_length=40, description='ruta del IDE donde nació la idea (contexto causal)')

def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent

def _notes_projection(root: Path, limit: int) -> list[dict[str, Any]]:
    data = cortex_ledger.list_events(root, limit=2000, offset=0)
    deleted: set[str] = set()
    notes: list[dict[str, Any]] = []
    for ev in data['events']:
        et = ev['event_type']
        if et == NOTE_DELETED:
            target = ev['payload'].get('note_event_id')
            if target:
                deleted.add(target)
        elif et == NOTE and ev['event_id'] not in deleted:
            notes.append({'event_id': ev['event_id'], 'seq': ev['seq'], 'text': ev['payload'].get('text', ''), 'route': ev['payload'].get('route', ''), 'created_at': ev['created_at'], 'hash': ev['current_hash'][:16]})
        if len(notes) >= limit:
            break
    return notes

@router.get('/notes')
def list_notes(limit: int=50) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    root = _get_project_root()
    return {'notes': _notes_projection(root, limit)}

@router.post('/notes')
def add_note(req: NoteRequest) -> dict[str, Any]:
    root = _get_project_root()
    ev = cortex_ledger.append_event(root, event_type=NOTE, entity_ref=ENTITY, payload={'text': req.text, 'route': req.route}, metadata={'taint': 'operator:thought-burst'})
    return {'event_id': ev['event_id'], 'seq': ev['seq'], 'text': req.text, 'route': req.route, 'created_at': ev['created_at'], 'hash': ev['current_hash'][:16]}

def _human_away(ms: int) -> str:
    mins = ms // 60000
    if mins < 1:
        return 'menos de 1 min'
    if mins < 60:
        return f'{mins} min'
    hours, mins = divmod(mins, 60)
    if hours < 24:
        return f'{hours}h {mins}m'
    days, hours = divmod(hours, 24)
    return f'{days}d {hours}h'

@router.get('/resume')
def resume_context() -> dict[str, Any]:
    root = _get_project_root()
    data = cortex_ledger.list_events(root, limit=300, offset=0)
    events = data['events']
    now_ms = int(time.time() * 1000)
    last_ev = events[0] if events else None
    away_ms = now_ms - last_ev['created_at'] if last_ev else None
    notes = _notes_projection(root, 1)
    last_note = notes[0] if notes else None
    last_delegation: dict[str, Any] | None = None
    terminal: dict[str, str] = {}
    for ev in events:
        et = ev['event_type']
        p = ev['payload']
        if et in ('DELEGATION_EXECUTED', 'DELEGATION_BLOCKED', 'DELEGATION_FAILED', 'DELEGATION_CANCELLED'):
            did = p.get('delegation_id')
            if did and did not in terminal:
                terminal[did] = et.replace('DELEGATION_', '')
        elif et == 'DELEGATION_QUEUED' and last_delegation is None:
            did = ev['current_hash'][:16]
            last_delegation = {'directive': p.get('directive', ''), 'kind': p.get('kind', ''), 'state': terminal.get(did, 'QUEUED'), 'created_at': ev['created_at']}
    suggested = 'ledger'
    if last_note and last_note.get('route'):
        suggested = last_note['route'] if last_note['route'] != 'alcove' else 'ledger'
    elif last_delegation:
        suggested = 'sentinel'
    bullets: list[str] = []
    if away_ms is not None:
        bullets.append(f'Fuera {_human_away(away_ms)} — el ledger no olvidó nada')
    if last_note:
        txt = last_note['text'][:70] + ('…' if len(last_note['text']) > 70 else '')
        origen = f" (nació en {last_note['route']})" if last_note.get('route') else ''
        bullets.append(f'Última idea: «{txt}»{origen}')
    if last_delegation:
        bullets.append(f"Última delegación: {last_delegation['kind']} → {last_delegation['state']}")
    if not bullets:
        bullets.append('Ledger cognitivo vacío — primera sesión con memoria')
    return {'away_ms': away_ms, 'away_human': _human_away(away_ms) if away_ms is not None else None, 'last_note': last_note, 'last_delegation': last_delegation, 'total_events': data['total'], 'suggested_route': suggested, 'bullets': bullets}

@router.post('/notes/{event_id}/delete')
def delete_note(event_id: str) -> dict[str, Any]:
    root = _get_project_root()
    existing = {n['event_id'] for n in _notes_projection(root, 200)}
    if event_id not in existing:
        raise HTTPException(404, f"Nota '{event_id}' no existe o ya está borrada")
    ev = cortex_ledger.append_event(root, event_type=NOTE_DELETED, entity_ref=ENTITY, payload={'note_event_id': event_id}, metadata={'taint': 'operator:note-tombstone'})
    return {'deleted': event_id, 'tombstone_seq': ev['seq']}