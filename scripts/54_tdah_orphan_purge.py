#!/usr/bin/env python3
"""
TDAH Orphan Thread Purge — C5-REAL (Intervención Isomórfica).
Mapeo: TDAH -> Context Switching excesivo en el procesador (Thrashing de CPU por exceso de hilos huérfanos).
Fase: Auditoría y Purga Termodinámica (Brutalismo Cinético).
"""

import os
import sys
import subprocess
import signal
import time
import sqlite3
import hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, ".cortex", "cortex.db")


def write_to_ledger(payload: str, agent_id: str = "tdah_orphan_purge_c5"):
    """Registra la purga en el Master Ledger (Ω11, Ω12)."""
    if not os.path.exists(DB_PATH):
        print(f"[Ledger] WARNING: No se encuentra la BD {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")

    cursor.execute(
        "SELECT payload_hash, lamport_t FROM bft_ledger ORDER BY id DESC LIMIT 1"
    )
    row = cursor.fetchone()
    if row:
        prev_hash = row[0]
        last_lamport = row[1]
    else:
        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        last_lamport = 0

    new_lamport = last_lamport + 1
    new_hash = hashlib.sha3_256(payload.encode("utf-8")).hexdigest()
    taint_signature = f"CORTEX-TAINT:borjamoskv:orphan_purge:{time.strftime('%Y-%m-%dT%H:%M:%SZ')}:{new_hash[:8]}"

    try:
        cursor.execute(
            "INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?)",
            (agent_id, new_lamport, new_hash, prev_hash, taint_signature),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[Ledger] ERROR BFT: {e}", file=sys.stderr)
    finally:
        conn.close()


def audit_and_purge_orphans() -> None:
    print(
        f"[{time.strftime('%H:%M:%S')}] Iniciando TDAH Orphan Thread Purge (C5-REAL)..."
    )

    # Extraer procesos con PPID = 1, %CPU > 10.0 (Thrashing)
    cmd = ["ps", "-eo", "pid,ppid,pcpu,command"]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando ps: {e}", file=sys.stderr)
        sys.exit(1)

    lines = result.stdout.strip().split("\n")[1:]
    purged_count = 0
    payload_log = []

    for line in lines:
        parts = line.split(maxsplit=3)
        if len(parts) < 4:
            continue

        pid_str, ppid_str, pcpu_str, command = parts

        try:
            pid = int(pid_str)
            ppid = int(ppid_str)
            pcpu = float(pcpu_str)
        except ValueError:
            continue

        # Si es huerfano (PPID=1) y consume exergía excesiva (ej. > 50.0%)
        if ppid == 1 and pcpu > 50.0:
            print(
                f"[TDAH Detectado] Hilo huérfano consumiendo CPU: PID {pid} | {pcpu}% | {command}"
            )
            # Brutalismo Cinético
            try:
                os.kill(pid, signal.SIGKILL)
                msg = f"PURGADO: PID {pid} ({command}) - CPU: {pcpu}%"
                print(f"[SIGKILL] {msg}")
                payload_log.append(msg)
                purged_count += 1
            except PermissionError:
                msg = f"DENEGADO (Requiere sudo): PID {pid} ({command})"
                print(f"[ERROR] {msg}")
                payload_log.append(msg)
            except OSError as e:
                print(f"[ERROR] Fallo al matar PID {pid}: {e}")

    if purged_count > 0 or payload_log:
        full_payload = "\\n".join(payload_log)
        write_to_ledger(f"TDAH Purge Result:\\n{full_payload}")
        print(
            f"[{time.strftime('%H:%M:%S')}] Purga completada. {purged_count} vectores de entropía aniquilados."
        )
    else:
        print(
            f"[{time.strftime('%H:%M:%S')}] Cero Anergía detectada. Homeostasis confirmada. Abortando JIT."
        )


if __name__ == "__main__":
    audit_and_purge_orphans()
