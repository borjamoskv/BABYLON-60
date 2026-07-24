"""
BABYLON60 IDE — Cortex notes (scratchpad event-sourced).

El "Buzón de Ideas" del diseño MOSKV-1: memoria de trabajo externalizada.
Hasta v1.2.x el scratchpad vivía en localStorage (teatro: se pierde por
navegador/perfil y no deja rastro causal). Ahora cada nota es un evento
COGNITIVE_NOTE en el CortexLedger del IDE (append-only, hash-chain SHA-256):
sobrevive sesiones, es auditable y entra en la verificación de cadena.

Append-only estricto: borrar una nota NO borra nada — se apendea un
tombstone COGNITIVE_NOTE_DELETED y la proyección la oculta.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..services import cortex_ledger


def _guard_local_origin(request: Request) -> None:
    """Misma defensa CSRF que delegation: mutaciones solo desde localhost
    o la extensión Alcove."""
    origin = request.headers.get("origin")
    if not origin:
        return
    host = urlparse(origin).hostname or ""
    if origin.startswith(("chrome-extension://", "moz-extension://")):
        return
    if host in ("localhost", "127.0.0.1", "::1"):
        return
    raise HTTPException(403, f"Origin '{origin}' no autorizado para mutar (solo localhost/Alcove)")


router = APIRouter(
    prefix="/api/cortex",
    tags=["cortex"],
    dependencies=[Depends(_guard_local_origin)],
)

ENTITY = "operator/scratchpad"
NOTE = "COGNITIVE_NOTE"
NOTE_DELETED = "COGNITIVE_NOTE_DELETED"


class NoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    route: str = Field("", max_length=40, description="ruta del IDE donde nació la idea (contexto causal)")


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _notes_projection(root: Path, limit: int) -> list[dict[str, Any]]:
    """Proyección: NOTE menos tombstones, más recientes primero."""
    data = cortex_ledger.list_events(root, limit=2000, offset=0)
    deleted: set[str] = set()
    notes: list[dict[str, Any]] = []
    for ev in data["events"]:  # ya viene newest-first
        et = ev["event_type"]
        if et == NOTE_DELETED:
            target = ev["payload"].get("note_event_id")
            if target:
                deleted.add(target)
        elif et == NOTE and ev["event_id"] not in deleted:
            notes.append(
                {
                    "event_id": ev["event_id"],
                    "seq": ev["seq"],
                    "text": ev["payload"].get("text", ""),
                    "route": ev["payload"].get("route", ""),
                    "created_at": ev["created_at"],
                    "hash": ev["current_hash"][:16],
                }
            )
        if len(notes) >= limit:
            break
    return notes


@router.get("/notes")
def list_notes(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    root = _get_project_root()
    return {"notes": _notes_projection(root, limit)}


@router.post("/notes")
def add_note(req: NoteRequest) -> dict[str, Any]:
    root = _get_project_root()
    ev = cortex_ledger.append_event(
        root,
        event_type=NOTE,
        entity_ref=ENTITY,
        payload={"text": req.text, "route": req.route},
        metadata={"taint": "operator:thought-burst"},
    )
    return {
        "event_id": ev["event_id"],
        "seq": ev["seq"],
        "text": req.text,
        "route": req.route,
        "created_at": ev["created_at"],
        "hash": ev["current_hash"][:16],
    }


@router.post("/notes/{event_id}/delete")
def delete_note(event_id: str) -> dict[str, Any]:
    """Tombstone append-only: la nota desaparece de la proyección,
    jamás del ledger (el rastro causal es sagrado)."""
    root = _get_project_root()
    existing = {n["event_id"] for n in _notes_projection(root, 200)}
    if event_id not in existing:
        raise HTTPException(404, f"Nota '{event_id}' no existe o ya está borrada")
    ev = cortex_ledger.append_event(
        root,
        event_type=NOTE_DELETED,
        entity_ref=ENTITY,
        payload={"note_event_id": event_id},
        metadata={"taint": "operator:note-tombstone"},
    )
    return {"deleted": event_id, "tombstone_seq": ev["seq"]}
