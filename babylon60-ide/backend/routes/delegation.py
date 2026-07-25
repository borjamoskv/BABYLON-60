from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
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


router = APIRouter(prefix="/api/delegation", tags=["delegation"], dependencies=[Depends(_guard_local_origin)])
_LOCAL_KINDS = {"commit", "precommit", "status", "custom"}
_CLOUD_KINDS = {"push", "merge", "ship", "deploy"}
_ALL_KINDS = _LOCAL_KINDS | _CLOUD_KINDS
P0_OPEN = True
ENTITY = "git/delegation"


class DelegateRequest(BaseModel):
    directive: str = Field(..., min_length=1, max_length=2000)
    kind: str = Field("custom")


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _git(root: Path, *args: str) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, timeout=15)
    except FileNotFoundError:
        return (127, "", "git not found on PATH")
    except subprocess.TimeoutExpired:
        return (124, "", "git command timed out (15s)")
    except ValueError:
        return (2, "", "invalid argument (embedded NUL?)")
    return (proc.returncode, proc.stdout.strip(), proc.stderr.strip())


def _projection(root: Path) -> list[dict[str, Any]]:
    data = cortex_ledger.list_events(root, limit=2000, offset=0)
    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for ev in reversed(data["events"]):
        et = ev["event_type"]
        p = ev["payload"]
        if et == "DELEGATION_QUEUED":
            did = ev["current_hash"][:16]
            by_id[did] = {
                "delegation_id": did,
                "directive": p.get("directive", ""),
                "kind": p.get("kind", "custom"),
                "state": "QUEUED",
                "created_at": ev["created_at"],
                "event_id": ev["event_id"],
                "result": None,
            }
            order.append(did)
            continue
        did = p.get("delegation_id")
        if did and did in by_id:
            if et == "DELEGATION_EXECUTED":
                by_id[did]["state"] = "EXECUTED"
                by_id[did]["result"] = p.get("result")
            elif et == "DELEGATION_BLOCKED":
                by_id[did]["state"] = "BLOCKED"
                by_id[did]["result"] = p.get("reason")
            elif et == "DELEGATION_CANCELLED":
                by_id[did]["state"] = "CANCELLED"
            elif et == "DELEGATION_FAILED":
                by_id[did]["state"] = "FAILED"
                by_id[did]["result"] = p.get("result")
    return [by_id[i] for i in reversed(order)]


@router.post("")
def enqueue(req: DelegateRequest) -> dict[str, Any]:
    root = _get_project_root()
    kind = req.kind if req.kind in _ALL_KINDS else "custom"
    ev = cortex_ledger.append_event(
        root,
        event_type="DELEGATION_QUEUED",
        entity_ref=ENTITY,
        payload={"directive": req.directive, "kind": kind},
        metadata={"taint": "operator:delegation-intent", "cloud": kind in _CLOUD_KINDS},
    )
    did = ev["current_hash"][:16]
    return {
        "delegation_id": did,
        "directive": req.directive,
        "kind": kind,
        "state": "QUEUED",
        "cloud_blocked": kind in _CLOUD_KINDS and P0_OPEN,
        "event": ev,
    }


@router.get("")
def list_delegations() -> dict[str, Any]:
    root = _get_project_root()
    items = _projection(root)
    return {
        "delegations": items,
        "p0_open": P0_OPEN,
        "policy": "cloud-upload (push/merge/ship/deploy) blocked until P0 key rotation",
    }


@router.post("/{delegation_id}/execute")
def execute(delegation_id: str) -> dict[str, Any]:
    root = _get_project_root()
    items = {d["delegation_id"]: d for d in _projection(root)}
    deleg = items.get(delegation_id)
    if not deleg:
        raise HTTPException(404, f"Delegation '{delegation_id}' not found")
    if deleg["state"] != "QUEUED":
        raise HTTPException(409, f"Delegation is '{deleg['state']}', not QUEUED")
    kind = deleg["kind"]
    if kind in ("commit", "precommit", "status", "custom") and (not cortex_ledger.claim(root, f"exec:{delegation_id}")):
        raise HTTPException(409, f"Delegation '{delegation_id}' ya está en ejecución (claim tomado)")
    if kind in _CLOUD_KINDS and P0_OPEN:
        reason = f"CRASH CAUSAL — '{kind}' bloqueado: P0 abierto. El fork remoto público trackea master_key.hex y solana_keypair.json (claves comprometidas por definición). Ninguna entropía sale a la nube hasta rotar claves (STATUS.md)."
        cortex_ledger.append_event(
            root,
            event_type="DELEGATION_BLOCKED",
            entity_ref=ENTITY,
            payload={"delegation_id": delegation_id, "kind": kind, "reason": reason},
            metadata={"taint": "git-sentinel:p0-guard"},
        )
        raise HTTPException(423, reason)
    if kind in ("commit", "precommit"):
        if not (root / ".git").is_dir():
            result = f"'{root.name}' no es un repo git — no hay dónde commitear (Git Sentinel)."
            cortex_ledger.append_event(
                root,
                event_type="DELEGATION_FAILED",
                entity_ref=ENTITY,
                payload={"delegation_id": delegation_id, "kind": kind, "result": result},
                metadata={"taint": "git-sentinel:no-repo"},
            )
            raise HTTPException(422, result)
        msg = deleg["directive"].strip() or "chore(ide): delegated commit via MOSKV-1"
        _git(root, "add", "-A")
        code, out, err = _git(root, "commit", "-m", msg, "--no-verify")
        if code != 0:
            result = err or out or "commit failed"
            cortex_ledger.append_event(
                root,
                event_type="DELEGATION_FAILED",
                entity_ref=ENTITY,
                payload={"delegation_id": delegation_id, "kind": kind, "result": result},
                metadata={"taint": "git-sentinel:commit-fail"},
            )
            raise HTTPException(422, result)
        _, head, _ = _git(root, "rev-parse", "--short", "HEAD")
        result = f"commit {head}: {(out.splitlines()[0] if out else msg)}"
        ev = cortex_ledger.append_event(
            root,
            event_type="DELEGATION_EXECUTED",
            entity_ref=ENTITY,
            payload={"delegation_id": delegation_id, "kind": kind, "result": result, "head": head},
            metadata={"taint": "git-sentinel:commit-sealed"},
        )
        return {"delegation_id": delegation_id, "state": "EXECUTED", "result": result, "event": ev}
    if kind == "status":
        code, out, _ = _git(root, "status", "--porcelain")
        result = f"{len(out.splitlines())} ficheros sucios" if out else "árbol limpio"
        ev = cortex_ledger.append_event(
            root,
            event_type="DELEGATION_EXECUTED",
            entity_ref=ENTITY,
            payload={"delegation_id": delegation_id, "kind": kind, "result": result},
            metadata={"taint": "git-sentinel:status"},
        )
        return {"delegation_id": delegation_id, "state": "EXECUTED", "result": result, "event": ev}
    result = "directiva custom registrada en el ledger (ejecución manual del agente)"
    ev = cortex_ledger.append_event(
        root,
        event_type="DELEGATION_EXECUTED",
        entity_ref=ENTITY,
        payload={"delegation_id": delegation_id, "kind": kind, "result": result},
        metadata={"taint": "operator:custom-intent"},
    )
    return {"delegation_id": delegation_id, "state": "EXECUTED", "result": result, "event": ev}


@router.post("/{delegation_id}/cancel")
def cancel(delegation_id: str) -> dict[str, Any]:
    root = _get_project_root()
    items = {d["delegation_id"]: d for d in _projection(root)}
    deleg = items.get(delegation_id)
    if not deleg:
        raise HTTPException(404, f"Delegation '{delegation_id}' not found")
    if deleg["state"] != "QUEUED":
        raise HTTPException(409, f"Delegation is '{deleg['state']}', cannot cancel")
    if not cortex_ledger.claim(root, f"exec:{delegation_id}"):
        raise HTTPException(409, f"Delegation '{delegation_id}' ya está en ejecución — no cancelable")
    ev = cortex_ledger.append_event(
        root,
        event_type="DELEGATION_CANCELLED",
        entity_ref=ENTITY,
        payload={"delegation_id": delegation_id, "kind": deleg["kind"]},
        metadata={"taint": "operator:cancel"},
    )
    return {"delegation_id": delegation_id, "state": "CANCELLED", "event": ev}


@router.post("/verify")
def verify_ide_ledger() -> dict[str, Any]:
    return cortex_ledger.verify_chain(_get_project_root())
