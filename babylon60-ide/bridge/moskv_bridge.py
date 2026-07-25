#!/usr/bin/env python3
"""
MOSKV BRIDGE — puente entre agentes sobre el CortexLedger.

Permite a CUALQUIER agente (ANTIGRAVITY / moskv-1-APEX, Claude/Cowork,
o un humano en Terminal) escribir y leer el bus de agentes SIN depender
de que el backend del IDE esté vivo: SQLite directo, stdlib puro,
cero dependencias.

INV_BRIDGE_01 — El sobre (envelope) es IDÉNTICO al de
backend/services/cortex_ledger.py. Si cambias uno, cambias el otro,
o la verificación de cadena declarará manipulación (por diseño):
    hash = sha256(f"{parent_hash}|{created_at}|{event_type}|{entity_ref}|{payload_canonical}")
    payload_canonical = json.dumps(payload, sort_keys=True, separators=(",",":"),
                                   ensure_ascii=False, allow_nan=False)
    event_id = uuid5(NS, f"{parent_hash}|{event_type}|{entity_ref}|{payload_canonical}")

Uso (desde la raíz del repo o con --db):
    python3 babylon60-ide/bridge/moskv_bridge.py status  <agente> "qué estás haciendo"
    python3 babylon60-ide/bridge/moskv_bridge.py handoff <de> <para> "tarea" ["contexto"]
    python3 babylon60-ide/bridge/moskv_bridge.py inbox   <agente>
    python3 babylon60-ide/bridge/moskv_bridge.py ack     <agente> <event_id_del_handoff>
    python3 babylon60-ide/bridge/moskv_bridge.py peers
    python3 babylon60-ide/bridge/moskv_bridge.py verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

NS = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")
ZERO = "0" * 64
DDL = """
CREATE TABLE IF NOT EXISTS cortex_events (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     TEXT NOT NULL UNIQUE,
    parent_hash  TEXT NOT NULL,
    current_hash TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    entity_ref   TEXT NOT NULL,
    payload      TEXT NOT NULL,
    metadata     TEXT,
    created_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cortex_type ON cortex_events(event_type, seq DESC);
CREATE INDEX IF NOT EXISTS idx_cortex_entity ON cortex_events(entity_ref, seq DESC);
"""

STATUS = "AGENT_STATUS"
HANDOFF = "AGENT_HANDOFF"
ACK = "AGENT_ACK"


def canonical(data) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def connect(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db), timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # WAL necesita shared-memory (-shm): en montajes de red/FUSE (p.ej. el
    # bridge de dispositivo) lanza "disk I/O error". Degradamos a DELETE
    # journal, que solo requiere el fichero — igual de correcto para el bus,
    # solo menos concurrente. El backend del IDE (disco local) sí usa WAL.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.executescript(DDL)
    except sqlite3.OperationalError:
        try:
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.executescript(DDL)
        except sqlite3.OperationalError as e:
            conn.close()
            raise SystemExit(
                "MOSKV BRIDGE: 'disk I/O error' — este sistema de ficheros no soporta "
                "escritura SQLite (montaje de red/FUSE, p.ej. el bridge de Cowork). "
                "Ejecuta el bridge desde tu disco LOCAL real (tu Terminal / el proceso "
                "del kernel), donde vive babylon60_ide.db de verdad."
            ) from e
    return conn


def append(db: Path, event_type: str, entity_ref: str, payload: dict, metadata: dict | None = None) -> dict:
    """Append atómico (BEGIN IMMEDIATE): idéntico contrato que el backend."""
    conn = connect(db)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT current_hash FROM cortex_events ORDER BY seq DESC LIMIT 1").fetchone()
            parent = row["current_hash"] if row else ZERO
            created = int(time.time() * 1000)
            pc = canonical(payload)
            eid = str(uuid.uuid5(NS, f"{parent}|{event_type}|{entity_ref}|{pc}"))
            h = hashlib.sha256(f"{parent}|{created}|{event_type}|{entity_ref}|{pc}".encode()).hexdigest()
            conn.execute(
                "INSERT INTO cortex_events (event_id, parent_hash, current_hash, event_type, entity_ref, payload, metadata, created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (eid, parent, h, event_type, entity_ref, pc, canonical(metadata) if metadata else None, created),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            row = conn.execute("SELECT * FROM cortex_events WHERE event_id=?", (eid,)).fetchone()
            return dict(row) if row else {}
        return {"event_id": eid, "seq_hash": h[:16], "created_at": created}
    finally:
        conn.close()


def events(db: Path, limit: int = 500) -> list[dict]:
    conn = connect(db)
    try:
        rows = conn.execute("SELECT * FROM cortex_events ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d["payload"])
            except (ValueError, TypeError):
                pass
            out.append(d)
        return out
    finally:
        conn.close()


def git_ctx(repo: Path) -> dict:
    """Contexto git del que escribe (rama+head), sin shell, sin fallo duro."""
    try:
        b = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, capture_output=True, text=True, timeout=5)
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, timeout=5)
        return {"branch": b.stdout.strip() or None, "head": h.stdout.strip() or None}
    except (OSError, subprocess.TimeoutExpired):
        return {"branch": None, "head": None}


def cmd_status(db: Path, repo: Path, agent: str, task: str) -> None:
    ev = append(db, STATUS, "bridge/agent", {"agent": agent, "task": task, **git_ctx(repo)},
                {"taint": f"{agent}:bridge-status"})
    print(f"⚡ STATUS sellado {ev.get('seq_hash')} — {agent}: {task}")


def cmd_handoff(db: Path, repo: Path, src: str, dst: str, task: str, context: str) -> None:
    ev = append(db, HANDOFF, "bridge/handoff",
                {"from": src, "to": dst, "task": task, "context": context, **git_ctx(repo)},
                {"taint": f"{src}:handoff"})
    print(f"⚡ HANDOFF sellado {ev.get('seq_hash')} — {src} → {dst}: {task}")
    print(f"   event_id (para ack): {ev.get('event_id')}")


def cmd_inbox(db: Path, agent: str) -> None:
    evs = events(db)
    # Dos pasadas: primero todos los ACKs (siempre posteriores a su handoff).
    acked = {e["payload"].get("handoff_event_id") for e in evs if e["event_type"] == ACK}
    pend = []
    for e in reversed(evs):  # oldest→newest
        if e["event_type"] == HANDOFF and e["payload"].get("to") == agent and e["event_id"] not in acked:
            pend.append(e)
    if not pend:
        print(f"inbox de '{agent}' vacío")
        return
    for e in reversed(pend):  # newest first
        p = e["payload"]
        print(f"◈ {e['event_id'][:8]}… de {p.get('from')}: {p.get('task')}")
        if p.get("context"):
            print(f"    ctx: {p['context'][:120]}")


def cmd_ack(db: Path, agent: str, handoff_id: str) -> None:
    ev = append(db, ACK, "bridge/handoff", {"handoff_event_id": handoff_id, "by": agent},
                {"taint": f"{agent}:ack"})
    print(f"✓ ACK sellado {ev.get('seq_hash')}")


def cmd_peers(db: Path) -> None:
    seen: dict[str, dict] = {}
    for e in events(db):  # newest first: primera aparición = último estado
        if e["event_type"] == STATUS:
            a = e["payload"].get("agent")
            if a and a not in seen:
                seen[a] = e
    if not seen:
        print("sin peers en el bus")
        return
    now = int(time.time() * 1000)
    for a, e in seen.items():
        p = e["payload"]
        mins = (now - e["created_at"]) // 60000
        print(f"● {a} — {p.get('task','?')} · {p.get('branch','?')}@{p.get('head','?')} · hace {mins} min")


def cmd_verify(db: Path) -> None:
    prev = ZERO
    rows = list(reversed(events(db, limit=100000)))  # oldest→newest
    ok = 0
    for e in rows:
        pc = canonical(e["payload"]) if isinstance(e["payload"], (dict, list)) else e["payload"]
        h = hashlib.sha256(f"{prev}|{e['created_at']}|{e['event_type']}|{e['entity_ref']}|{pc}".encode()).hexdigest()
        if e["parent_hash"] != prev or h != e["current_hash"]:
            print(f"✗ CADENA ROTA en seq {e['seq']}")
            sys.exit(1)
        ok += 1
        prev = e["current_hash"]
    print(f"✓ cadena íntegra: {ok}/{len(rows)} eventos (escritores mixtos incluidos)")


def main() -> None:
    ap = argparse.ArgumentParser(description="MOSKV BRIDGE — bus de agentes sobre el CortexLedger")
    ap.add_argument("--db", default=None, help="ruta a babylon60_ide.db (default: <raíz repo>/babylon60_ide.db)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status"); s.add_argument("agent"); s.add_argument("task")
    h = sub.add_parser("handoff"); h.add_argument("src"); h.add_argument("dst"); h.add_argument("task"); h.add_argument("context", nargs="?", default="")
    i = sub.add_parser("inbox"); i.add_argument("agent")
    a = sub.add_parser("ack"); a.add_argument("agent"); a.add_argument("handoff_id")
    sub.add_parser("peers")
    sub.add_parser("verify")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent.parent  # bridge/ → babylon60-ide/ → raíz
    db = Path(args.db) if args.db else repo / "babylon60_ide.db"

    if args.cmd == "status":
        cmd_status(db, repo, args.agent, args.task)
    elif args.cmd == "handoff":
        cmd_handoff(db, repo, args.src, args.dst, args.task, args.context)
    elif args.cmd == "inbox":
        cmd_inbox(db, args.agent)
    elif args.cmd == "ack":
        cmd_ack(db, args.agent, args.handoff_id)
    elif args.cmd == "peers":
        cmd_peers(db)
    elif args.cmd == "verify":
        cmd_verify(db)


if __name__ == "__main__":
    main()
