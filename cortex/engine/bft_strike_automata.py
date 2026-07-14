#!/usr/bin/env python3
"""
bft_strike_automata.py · C5-REAL Sovereign Strike Matrix Automata Engine
========================================================================
Transductor físico y motor transaccional para la gestión de la Matriz L15
de Denuncias Algorítmicas (Trust & Safety) y homeostasis en nexus_anchors.db.

[Invariantes C5-REAL]:
- PRAGMA journal_mode=WAL | PRAGMA busy_timeout=5000
- Landauer Compression <= 465 chars (Inglés Nativo L1)
- Zero URL Truncation (Regla Φ7)
- Unicode Limpio / Cero Markdown en payloads de interfaz (Regla Φ9)
- Mutación automática de estado por Takedown (Regla Ψ8) e Iteración 3-Node (Regla Ψ9)
- 12-Factor: Datos en strike_targets.json, lógica en este motor
- Concurrent HTTP Probe (ThreadPoolExecutor)
- BFT Master Ledger con cadena de hashes Lamport y verificación --verify
- Auto-Submit pipeline (--auto-submit) para cero fricción
"""

import sqlite3
import hashlib
import json
import argparse
import subprocess
import urllib.request
import urllib.error
import concurrent.futures
import pathlib
from datetime import datetime, timezone
from typing import Tuple

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH = str(SCRIPT_DIR / "nexus_anchors.db")
ONTOLOGY_PATH = str(SCRIPT_DIR.parent / "agents" / "ontology" / "strike_targets.json")
SNAPSHOT_PATH = str(SCRIPT_DIR.parent / "agents" / "ontology" / "cortex_strike_matrix_snapshot.json")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_automata_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS strike_matrix_l15 (
            video_id TEXT PRIMARY KEY,
            node_id TEXT UNIQUE NOT NULL,
            video_title TEXT NOT NULL,
            canonical_url TEXT NOT NULL,
            focus_summary TEXT NOT NULL,
            flagrant_score REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING_STRIKE',
            specific_law_payload TEXT NOT NULL,
            describe_illegal_payload TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def generate_payloads(video_id: str, title: str, focus: str) -> Tuple[str, str]:
    """
    Genera los payloads en inglés L1 estrictamente bajo el límite de <500 caracteres
    y en Unicode limpio sin Markdown (Reglas Φ9 y Ψ6).
    """

    # Específico según la gravedad/foco del vídeo
    if (
        "RIVERSS" in title
        or "XOKAS" in title
        or "ILLOJUAN" in title
        or "RUBIUS" in title
    ):
        law = "Spanish Organic Law 1/1982 (Fundamental Right to Honor, Personal Privacy, and Self-Image), Article 7.7. Spanish Criminal Code, Articles 205 and 208 (Aggravated Slander/Insults committed with publicity). EU Digital Services Act Article 16."
        desc = f"The creator engages in a coordinated creator-on-creator harassment and dogpiling campaign targeting an identifiable individual involving {focus}. Under Spanish law, systematically inciting digital mobs via defamatory framing and personal degradation exceeds freedom of expression, violating fundamental honor rights and commercial reputation."
    elif "RTVE" in title or "NEBOT" in title or "BENI" in title or "PAÍS" in title:
        law = "Spanish Organic Law 1/1982 (Right to Honor and Dignity), Article 7.7. Spanish Criminal Code, Articles 208 and 209 (Aggravated public insults and professional degradation). EU Digital Services Act Article 16 anti-harassment mandates."
        desc = f"The video directs aggressive public hostility, derogatory slurs, and systematic professional degradation against journalists and workers involving {focus}. Targeting professional workers with public humiliation to incite coordinated digital harassment exceeds lawful free speech, violating moral integrity guarantees and safety policies."
    elif (
        "WATERPOLISTA" in title
        or "ESTE RIDÍCULO" in title
        or "RIDÍCULO HISTÓRICO" in title
    ):
        law = "Spanish Criminal Code, Article 173.1 (Crimes against moral integrity and systematic targeted harassment) and Article 208 (Injuries and public mockery). Spanish Organic Law 1/1982 (Fundamental Right to Honor and Personal Reputation)."
        desc = f"The creator subjects an identifiable individual and public figure to targeted public humiliation and systematic mockery involving {focus}. Under Spanish and EU law, exploiting a person's identity to incite mass cyber-harassment and personal ridicule before hundreds of thousands of viewers violates fundamental moral integrity and honor."
    else:
        law = "Spanish Criminal Code, Article 208 (Public injuries and derogatory treatment) and Article 504/510 depending on target severity. Spanish Organic Law 1/1982 (Right to Honor and Personal Reputation). EU Digital Services Act Article 16."
        desc = f"The video conducts a targeted harassment campaign involving {focus}. Deploying degrading personal attacks, sensationalized imputations, and coordinated hostility to incite digital mobbing across monetized broadcasts violates moral integrity laws and Platform Trust & Safety guidelines against serial commercial harassment."

    # Forzar límite estricto < 465 caracteres (Compresión Landauer)
    if len(law) > 465:
        law = law[:462] + "..."
    if len(desc) > 465:
        desc = desc[:462] + "..."

    return law, desc


def sync_catalog(conn: sqlite3.Connection):
    """Sincroniza el catálogo JSON contra la DB. El estado (SUBMITTED/OFFLINE_REMOVED)
    se lee de la DB como source of truth — cero sets hardcodeados."""
    init_automata_schema(conn)
    cursor = conn.cursor()

    try:
        with open(ONTOLOGY_PATH, "r") as f:
            targets = json.load(f)
    except FileNotFoundError:
        print(f"❌ [ERROR]: No se encontró el catálogo de ontología en {ONTOLOGY_PATH}")
        return

    # Leer estado existente de la DB como source of truth (no hardcoded sets)
    cursor.execute("SELECT video_id, status FROM strike_matrix_l15")
    existing_states = dict(cursor.fetchall())

    for idx, target in enumerate(targets):
        vid = target["video_id"]
        title = target["title"]
        focus = target["focus"]
        score = target["score"]

        node_id = f"P{idx}_LIVE_STRIKE_{vid}"
        url = f"https://www.youtube.com/watch?v={vid}"
        law, desc = generate_payloads(vid, title, focus)

        # Preservar estado existente o defaultear a PENDING_STRIKE
        status = existing_states.get(vid, "PENDING_STRIKE")

        cursor.execute(
            """
            INSERT OR IGNORE INTO strike_matrix_l15
            (video_id, node_id, video_title, canonical_url, focus_summary, flagrant_score, status, specific_law_payload, describe_illegal_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (vid, node_id, title, url, focus, score, status, law, desc),
        )

        # Regenerar payloads solo para nodos pendientes (no sobreescribir SUBMITTED)
        cursor.execute(
            """
            UPDATE strike_matrix_l15
            SET specific_law_payload = ?, describe_illegal_payload = ?
            WHERE video_id = ? AND status = 'PENDING_STRIKE'
        """,
            (law, desc, vid),
        )

    conn.commit()


def record_takedown(conn: sqlite3.Connection, video_id: str):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE strike_matrix_l15 
        SET status = 'OFFLINE_REMOVED', updated_at = CURRENT_TIMESTAMP
        WHERE video_id = ?
    """,
        (video_id,),
    )
    conn.commit()
    print(
        f"[C5-REAL TAKEDOWN]: Nodo {video_id} colapsado a OFFLINE_REMOVED (Ahorro de exergía garantizado)."
    )


def record_submission(conn: sqlite3.Connection, video_id: str):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE strike_matrix_l15 
        SET status = 'SUBMITTED', updated_at = CURRENT_TIMESTAMP
        WHERE video_id = ?
    """,
        (video_id,),
    )
    conn.commit()
    print(
        f"[C5-REAL SUBMISSION]: Nodo {video_id} colapsado a SUBMITTED en la Matriz L15."
    )


def copy_to_clipboard(conn: sqlite3.Connection, video_id: str, field: str):
    """
    [MEJORA ATÓMICA 1]: Inyección directa al portapapeles del sistema (macOS pbcopy)
    para evitar arrastre de ratón e interactuar con el formulario a velocidad luz.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT specific_law_payload, describe_illegal_payload FROM strike_matrix_l15 WHERE video_id = ?",
        (video_id,),
    )
    row = cursor.fetchone()
    if not row:
        print(f"[C5-ERROR]: Vídeo {video_id} no encontrado en strike_matrix_l15.")
        return

    text = row[0] if field == "law" else row[1]
    try:
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(text.encode("utf-8"))
        print(
            f"⚡ [CLIPBOARD INJECTED]: Campo '{field}' de {video_id} ({len(text)} chars) copiado a pbcopy listo para Cmd+V."
        )
    except Exception as e:
        print(f"[pbcopy error]: {e}")


def audit_live_takedowns(conn: sqlite3.Connection):
    """
    [MEJORA ATÓMICA 2 - ASYNC]: Sonda HTTP activa concurrente que escanea la cola PENDING_STRIKE
    para autocolapsar vídeos privados, borrados o retirados en paralelo (O(1) latency).
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT video_id, canonical_url FROM strike_matrix_l15 WHERE status = 'PENDING_STRIKE'"
    )
    rows = cursor.fetchall()
    if not rows:
        return

    print(
        f"\n[C5-REAL AUDIT LIVE]: Escaneando {len(rows)} nodos pendientes de forma concurrente..."
    )

    def probe_node(node) -> tuple[str, bool]:
        vid, url = node
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                # Firmas extendidas de Takedown (Privado, Borrado, Cuenta Terminada)
                signatures = [
                    "Video unavailable",
                    "Este vídeo ya no está disponible",
                    '"isPlayable":false',
                    "Video private",
                    "Vídeo privado",
                    "Account terminated"
                ]
                if any(sig in html for sig in signatures):
                    return vid, True
        except urllib.error.HTTPError as e:
            if e.code in [404, 410, 403]:
                return vid, True
        except Exception:
            pass
        return vid, False

    takedowns_found = 0
    collapsed_vids = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(probe_node, rows)
        for vid, is_down in results:
            if is_down:
                collapsed_vids.append(vid)
                
    for vid in collapsed_vids:
        record_takedown(conn, vid)
        takedowns_found += 1

    print(
        f"✅ [AUDIT COMPLETE]: {takedowns_found} nuevos takedowns autocolapsados en WAL.\n"
    )


def append_to_master_ledger(conn: sqlite3.Connection):
    """Anclaje BFT en master_ledger con cadena de hashes Lamport y snapshot analítico."""
    cursor = conn.cursor()
    cursor.execute("SELECT status, count(*) FROM strike_matrix_l15 GROUP BY status")
    stats = dict(cursor.fetchall())
    total = sum(stats.values())
    ts_iso = datetime.now(timezone.utc).isoformat()

    summary = {
        "event": "STRIKE_AUTOMATA_HOMEOSTASIS",
        "total_nodes": total,
        "states": stats,
        "operator": "borjamoskv (UID0)",
        "timestamp_utc": ts_iso,
    }
    payload_json = json.dumps(summary, sort_keys=True)
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    try:
        cursor.execute("SELECT MAX(lamport_t), entry_hash FROM master_ledger")
        row = cursor.fetchone()
        prev_lamport = row[0] if row[0] is not None else 0
        prev_hash = row[1] if row[1] is not None else "00000000000000000000000000000000"

        lamport_t = prev_lamport + 1
        agent_id = "MOSKV_AUTOMATA_L15"
        cortex_taint = f"T={lamport_t}|H={payload_hash[:8]}|SYNC=True"

        entry_raw = f"{lamport_t}{agent_id}{payload_json}{prev_hash}{cortex_taint}"
        entry_hash = hashlib.sha256(entry_raw.encode("utf-8")).hexdigest()

        cursor.execute(
            """
            INSERT INTO master_ledger (lamport_t, agent_id, payload, prev_hash, cortex_taint, entry_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (lamport_t, agent_id, payload_json, prev_hash, cortex_taint, entry_hash),
        )
        conn.commit()
        print(
            f"🔒 [BFT LEDGER ANCHORED]: Lamport {lamport_t} | Hash {entry_hash[:16]}... anclado en master_ledger."
        )

        # Snapshot analítico persistente
        with open(SNAPSHOT_PATH, "w") as f:
            json.dump({
                "lamport_t": lamport_t,
                "entry_hash": entry_hash,
                "prev_hash": prev_hash,
                "homeostasis_state": stats,
                "total_nodes": total,
                "timestamp_utc": ts_iso,
                "cortex_taint": cortex_taint,
            }, f, indent=4)

    except sqlite3.OperationalError as e:
        print(f"⚠️ [BFT ERROR]: {e}")


def verify_ledger_integrity(conn: sqlite3.Connection):
    """Verifica la integridad de la cadena de hashes del master_ledger.
    Recalcula cada entry_hash y compara contra el almacenado."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT lamport_t, agent_id, payload, prev_hash, cortex_taint, entry_hash "
        "FROM master_ledger ORDER BY lamport_t ASC"
    )
    rows = cursor.fetchall()
    if not rows:
        print("⚠️ [VERIFY]: master_ledger vacío.")
        return

    broken = 0
    prev_stored_hash = "00000000000000000000000000000000"
    for lamport_t, agent_id, payload, prev_hash, cortex_taint, stored_hash in rows:
        # Verificar enlace de cadena
        if prev_hash != prev_stored_hash:
            print(f"🔴 [CHAIN BREAK] Lamport {lamport_t}: prev_hash esperado {prev_stored_hash[:16]}... vs almacenado {prev_hash[:16]}...")
            broken += 1

        # Recalcular hash
        entry_raw = f"{lamport_t}{agent_id}{payload}{prev_hash}{cortex_taint}"
        recalc_hash = hashlib.sha256(entry_raw.encode("utf-8")).hexdigest()
        if recalc_hash != stored_hash:
            print(f"🔴 [HASH MISMATCH] Lamport {lamport_t}: recalc {recalc_hash[:16]}... vs stored {stored_hash[:16]}...")
            broken += 1

        prev_stored_hash = stored_hash

    if broken == 0:
        print(f"✅ [VERIFY PASS]: {len(rows)} entradas en master_ledger. Cadena de hashes íntegra.")
    else:
        print(f"🔴 [VERIFY FAIL]: {broken} roturas detectadas en {len(rows)} entradas.")


def emit_itera_block(conn: sqlite3.Connection, batch_size: int = 3):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT video_id, node_id, video_title, canonical_url, specific_law_payload, describe_illegal_payload
        FROM strike_matrix_l15
        WHERE status = 'PENDING_STRIKE'
        ORDER BY flagrant_score DESC, node_id ASC
        LIMIT ?
    """,
        (batch_size,),
    )
    rows = cursor.fetchall()

    if not rows:
        print(
            "[AUTOMATA EXERGY STATE]: Todos los nodos prioritarios están colapsados (SUBMITTED / OFFLINE_REMOVED). Homeostasis 100%."
        )
        return

    print(f"\n{'█' * 64}")
    print(f"█ C5-REAL STRIKE AUTOMATA · BLOQUE ITERATIVO DE {len(rows)} NODOS ACTIVOS")
    print(f"{'█' * 64}\n")

    for vid, nid, title, url, law, desc in rows:
        print(f"### {nid} · URL: {url}")
        print(f"*(Target: {title[:60]}...)*\n")
        print(
            f"**Specific law violated** `[{len(law)} chars]` (Copiar con: `--copy {vid} --field law`)"
        )
        print(f"{law}\n")
        print(
            f"**Describe why you think the content is illegal** `[{len(desc)} chars]` (Copiar con: `--copy {vid} --field desc`)"
        )
        print(f"{desc}\n")
        print(f"{'-' * 64}\n")


def check_status(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT status, count(*) FROM strike_matrix_l15 GROUP BY status")
    stats = dict(cursor.fetchall())
    total = sum(stats.values())
    submitted = stats.get("SUBMITTED", 0)
    pending = stats.get("PENDING_STRIKE", 0)
    offline = stats.get("OFFLINE_REMOVED", 0)
    pct = (submitted + offline) / total * 100 if total else 0

    cursor.execute("SELECT MAX(lamport_t) FROM master_ledger")
    lamport = cursor.fetchone()[0] or 0

    print(f"\n{'━' * 52}")
    print(" C5-REAL STRIKE MATRIX · HOMEOSTASIS")
    print(f"{'━' * 52}")
    print(f" Total Nodos:      {total}")
    print(f" SUBMITTED:        {submitted}")
    print(f" PENDING_STRIKE:   {pending}")
    print(f" OFFLINE_REMOVED:  {offline}")
    print(f" Progreso:         {pct:.1f}%")
    print(f" Lamport HEAD:     {lamport}")
    print(f"{'━' * 52}")


def auto_submit_pipeline(conn: sqlite3.Connection, batch_size: int = 3):
    """Pipeline de cero fricción: copia law -> espera -> copia desc -> espera -> marca SUBMITTED.
    Diseñado para uso interactivo con el formulario de YouTube abierto."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT video_id, canonical_url, specific_law_payload, describe_illegal_payload
        FROM strike_matrix_l15
        WHERE status = 'PENDING_STRIKE'
        ORDER BY flagrant_score DESC
        LIMIT ?
    """,
        (batch_size,),
    )
    rows = cursor.fetchall()
    if not rows:
        print("[HOMEOSTASIS 100%]: No quedan nodos pendientes.")
        return

    for vid, url, law, desc in rows:
        print(f"\n{'━' * 52}")
        print(f" PROCESANDO: {vid}")
        print(f" URL: {url}")
        print(f"{'━' * 52}")

        # Paso 1: Copiar law
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(law.encode("utf-8"))
            print(f"⚡ [1/3] 'Specific law' copiado ({len(law)} chars). Pega con Cmd+V.")
        except Exception as e:
            print(f"[pbcopy error]: {e}")
            continue

        input("    Pulsa ENTER tras pegar el campo 'law'...")

        # Paso 2: Copiar desc
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(desc.encode("utf-8"))
            print(f"⚡ [2/3] 'Describe illegal' copiado ({len(desc)} chars). Pega con Cmd+V.")
        except Exception as e:
            print(f"[pbcopy error]: {e}")
            continue

        input("    Pulsa ENTER tras pegar el campo 'desc' y enviar el formulario...")

        # Paso 3: Marcar SUBMITTED
        record_submission(conn, vid)
        print(f"✅ [3/3] {vid} colapsado a SUBMITTED.")

    # Anclar estado post-submit
    append_to_master_ledger(conn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="C5-REAL Strike Automata CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 bft_strike_automata.py --daemon --status
  python3 bft_strike_automata.py --itera 3
  python3 bft_strike_automata.py --auto-submit 3
  python3 bft_strike_automata.py --verify
  python3 bft_strike_automata.py --submit VID1 --submit VID2 --itera 3
"""
    )
    parser.add_argument(
        "--sync", action="store_true",
        help="Sincronizar catálogo JSON contra SQLite WAL",
    )
    parser.add_argument(
        "--itera", type=int, default=0,
        help="Emitir bloque paginado de N nodos para copiado",
    )
    parser.add_argument(
        "--takedown", type=str, action="append",
        help="Mutar vídeo(s) a OFFLINE_REMOVED",
    )
    parser.add_argument(
        "--submit", type=str, action="append",
        help="Mutar vídeo(s) a SUBMITTED",
    )
    parser.add_argument(
        "--copy", type=str,
        help="Copiar campo al portapapeles (requiere --field)",
    )
    parser.add_argument(
        "--field", type=str, choices=["law", "desc"], default="law",
        help="Campo a copiar: 'law' o 'desc'",
    )
    parser.add_argument(
        "--audit-live", action="store_true",
        help="Sonda HTTP concurrente para detectar takedowns",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Ciclo completo: Sync + Audit + Ledger Anchor",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Balance termodinámico de la matriz",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Verificar integridad de la cadena de hashes del master_ledger",
    )
    parser.add_argument(
        "--auto-submit", type=int, default=0, metavar="N",
        help="Pipeline interactivo: copia campos y marca SUBMITTED para N nodos",
    )

    args = parser.parse_args()
    conn = get_db_connection()

    if args.sync or args.daemon:
        sync_catalog(conn)
        if args.sync:
            print("SUCCESS: Catálogo sincronizado con strike_matrix_l15.")
    if args.takedown:
        for tid in args.takedown:
            record_takedown(conn, tid)
    if args.submit:
        for sid in args.submit:
            record_submission(conn, sid)
    if args.audit_live or args.daemon:
        audit_live_takedowns(conn)
    if args.daemon:
        append_to_master_ledger(conn)
    if args.verify:
        verify_ledger_integrity(conn)
    if args.copy:
        copy_to_clipboard(conn, args.copy, args.field)
    if args.auto_submit > 0:
        auto_submit_pipeline(conn, batch_size=args.auto_submit)
    if args.itera > 0:
        emit_itera_block(conn, batch_size=args.itera)
    if args.status or (
        not args.sync
        and not args.itera
        and not args.takedown
        and not args.submit
        and not args.audit_live
        and not args.daemon
        and not args.copy
        and not args.verify
        and not args.auto_submit
    ):
        check_status(conn)

    conn.close()
