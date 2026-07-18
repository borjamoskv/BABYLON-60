"""
BABYLON60 IDE — Delegation engine (100% de la subida a la nube al agente).

The operator declares intent; MOSKV-1 executes with the Git Sentinel and
seals every step in the CortexLedger. This is NOT localStorage theatre:
directives are hash-chained events, `commit` runs a real (whitelisted)
git subprocess, and cloud-upload ops (push/merge/ship/deploy) HARD-CRASH
with a causal reason while P0 (leaked keys in the dead remote) is open.

Causal contract: a blocked op is not a silent no-op — it appends a
DELEGATION_BLOCKED event and returns 423 Locked (Ley 1: Falla = Crash Causal).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import cortex_ledger

router = APIRouter(prefix="/api/delegation", tags=["delegation"])

# ── Kind taxonomy ──────────────────────────────────────────────────────────
# LOCAL ops mutate only the local lineage (allowed).
# CLOUD ops push entropy off-machine → blocked while P0 open.
_LOCAL_KINDS = {"commit", "precommit", "status", "custom"}
_CLOUD_KINDS = {"push", "merge", "ship", "deploy"}
_ALL_KINDS = _LOCAL_KINDS | _CLOUD_KINDS

# P0 gate — STATUS.md: master_key.hex + solana_keypair.json leaked in the
# public dead fork. No cloud upload until rotation. Flip to False post-rotation.
P0_OPEN = True

ENTITY = "git/delegation"


class DelegateRequest(BaseModel):
    directive: str = Field(..., min_length=1, max_length=2000)
    kind: str = Field("custom")


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _git(root: Path, *args: str) -> tuple[int, str, str]:
    """Run a whitelisted git command with argv (no shell). Returns (code, out, err)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return 127, "", "git not found on PATH"
    except subprocess.TimeoutExpired:
        return 124, "", "git command timed out (15s)"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _projection(root: Path) -> list[dict[str, Any]]:
    """Project current delegation state from the append-only event log.

    A delegation's id IS the current_hash[:16] of its QUEUED event — the
    causal anchor. Lifecycle events reference it via payload.delegation_id.
    """
    data = cortex_ledger.list_events(root, limit=500, offset=0)
    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for ev in reversed(data["events"]):  # oldest → newest
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
    return [by_id[i] for i in reversed(order)]  # newest first


@router.post("")
def enqueue(req: DelegateRequest) -> dict[str, Any]:
    root = _get_project_root()
    kind = req.kind if req.kind in _ALL_KINDS else "custom"
    # Single append; the event's own current_hash[:16] is the delegation id.
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

    # ── Causal crash: cloud upload blocked while P0 open ──
    if kind in _CLOUD_KINDS and P0_OPEN:
        reason = (
            f"CRASH CAUSAL — '{kind}' bloqueado: P0 abierto. El fork remoto "
            "público trackea master_key.hex y solana_keypair.json (claves "
            "comprometidas por definición). Ninguna entropía sale a la nube "
            "hasta rotar claves (STATUS.md)."
        )
        cortex_ledger.append_event(
            root,
            event_type="DELEGATION_BLOCKED",
            entity_ref=ENTITY,
            payload={"delegation_id": delegation_id, "kind": kind, "reason": reason},
            metadata={"taint": "git-sentinel:p0-guard"},
        )
        raise HTTPException(423, reason)

    # ── Real local execution (whitelisted argv) ──
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
        result = f"commit {head}: {out.splitlines()[0] if out else msg}"
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

    # custom → recorded as executed intent (no shell execution of free text; INV: Fricción Cero, no injection)
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
    """Verify the IDE's OWN CortexLedger hash-chain."""
    return cortex_ledger.verify_chain(_get_project_root())
