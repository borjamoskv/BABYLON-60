"""
BABYLON60 IDE — Agent Bridge (puente Claude ⇄ ANTIGRAVITY/moskv-1-APEX).

El bus físico es el CortexLedger: ambos agentes escriben eventos
AGENT_STATUS / AGENT_HANDOFF / AGENT_ACK en la MISMA cadena de hashes —
el kernel externo vía `bridge/moskv_bridge.py` (SQLite directo, sin
depender de este backend), y este IDE vía estas rutas. Una sola fuente
de verdad, escritores mixtos, integridad verificable.

INV_BRIDGE_01: el sobre criptográfico es idéntico en ambos escritores
(ver services/cortex_ledger.py y bridge/moskv_bridge.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..services import cortex_ledger


def _guard_local_origin(request: Request) -> None:
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
    prefix="/api/bridge",
    tags=["bridge"],
    dependencies=[Depends(_guard_local_origin)],
)

STATUS = "AGENT_STATUS"
HANDOFF = "AGENT_HANDOFF"
ACK = "AGENT_ACK"
SELF_AGENT = "claude-cowork"


class StatusRequest(BaseModel):
    agent: str = Field(SELF_AGENT, max_length=60)
    task: str = Field(..., min_length=1, max_length=500)


class HandoffRequest(BaseModel):
    to: str = Field(..., min_length=1, max_length=60, description="agente destino, ej. 'moskv-1-apex'")
    task: str = Field(..., min_length=1, max_length=1000)
    context: str = Field("", max_length=4000)
    src: str = Field(SELF_AGENT, max_length=60)


class AckRequest(BaseModel):
    handoff_event_id: str = Field(..., min_length=8, max_length=64)
    by: str = Field(SELF_AGENT, max_length=60)


def _root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _bus_events(limit: int = 1000) -> list[dict[str, Any]]:
    res = cortex_ledger.list_events(_root(), limit=limit, offset=0)
    return cast(list[dict[str, Any]], res["events"])


@router.get("/peers")
def peers() -> dict[str, Any]:
    """Último estado conocido de cada agente en el bus (newest wins)."""
    seen: dict[str, dict[str, Any]] = {}
    for ev in _bus_events():  # newest first
        if ev["event_type"] == STATUS:
            agent = ev["payload"].get("agent")
            if agent and agent not in seen:
                seen[agent] = {
                    "agent": agent,
                    "task": ev["payload"].get("task", ""),
                    "branch": ev["payload"].get("branch"),
                    "head": ev["payload"].get("head"),
                    "last_seen": ev["created_at"],
                    "hash": ev["current_hash"][:16],
                }
    return {"peers": list(seen.values())}


@router.get("/inbox")
def inbox(agent: str = SELF_AGENT) -> dict[str, Any]:
    """Handoffs dirigidos a `agent` sin ACK (pendientes de atender)."""
    evs = _bus_events()
    # Dos pasadas: primero TODOS los ACKs (un ACK siempre es posterior a su
    # handoff; en una sola pasada viejo→nuevo el handoff se colaría al inbox
    # antes de ver su ACK).
    acked: set[str] = {
        ev["payload"].get("handoff_event_id")
        for ev in evs
        if ev["event_type"] == ACK and ev["payload"].get("handoff_event_id")
    }
    pending: list[dict[str, Any]] = []
    for ev in reversed(evs):  # oldest → newest
        et = ev["event_type"]
        if et == HANDOFF and ev["payload"].get("to") == agent and ev["event_id"] not in acked:
            pending.append(
                {
                    "event_id": ev["event_id"],
                    "from": ev["payload"].get("from", "?"),
                    "task": ev["payload"].get("task", ""),
                    "context": ev["payload"].get("context", ""),
                    "created_at": ev["created_at"],
                }
            )
    pending.reverse()  # newest first
    return {"agent": agent, "pending": pending}


@router.post("/status")
def post_status(req: StatusRequest) -> dict[str, Any]:
    ev = cortex_ledger.append_event(
        _root(),
        event_type=STATUS,
        entity_ref="bridge/agent",
        payload={"agent": req.agent, "task": req.task, "branch": None, "head": None},
        metadata={"taint": f"{req.agent}:bridge-status"},
    )
    return {"sealed": ev["current_hash"][:16], "event_id": ev["event_id"]}


@router.post("/handoff")
def post_handoff(req: HandoffRequest) -> dict[str, Any]:
    ev = cortex_ledger.append_event(
        _root(),
        event_type=HANDOFF,
        entity_ref="bridge/handoff",
        payload={"from": req.src, "to": req.to, "task": req.task, "context": req.context},
        metadata={"taint": f"{req.src}:handoff"},
    )
    return {"sealed": ev["current_hash"][:16], "event_id": ev["event_id"]}


@router.post("/ack")
def post_ack(req: AckRequest) -> dict[str, Any]:
    ev = cortex_ledger.append_event(
        _root(),
        event_type=ACK,
        entity_ref="bridge/handoff",
        payload={"handoff_event_id": req.handoff_event_id, "by": req.by},
        metadata={"taint": f"{req.by}:ack"},
    )
    return {"sealed": ev["current_hash"][:16]}
