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
- [NUEVO] pbcopy Direct Clipboard Bridge (--copy)
- [NUEVO] Live HTTP Takedown Probe (--audit-live)
- [NUEVO] BFT Master Ledger Sync (--daemon)
"""

import sqlite3
import hashlib
import json
import argparse
import subprocess
import urllib.request
import urllib.error
from typing import Tuple

DB_PATH = "$CORTEX_ROOT/10_PROJECTS/Teorema-Robinson-Moskv/cortex/engine/nexus_anchors.db"

# Catálogo canónico de los 30 nodos de alta exergía
LIVE_CATALOG = [
    ("Zz7Xjor_NHo", "La POLÉMICA del XOKAS HA SUPUESTO la DERROTA de 20 AÑOS de SUPREMACISMO FEMINISTA | UTBED", "targeted gender-based harassment and derogatory framing of public feminism advocacy", 0.95),
    ("-BrmS0K9axU", "WALL STREET WOLVERINE DESTRUYE a MARINA RIVERSS y SU APOYO ENCUBIERTO al SANCHISMO | UTBED", "targeted creator-on-creator harassment and ideological dogpiling against Marina Riverss", 0.94),
    ("b0-phku8yx4", "CANCELAN a ILLOJUAN por FOTOGRAFIARSE CON un N*ZI | UTBED", "exploitation of extremist hate tokens and coordinated public mobbing targeting Illojuan", 0.96),
    ("innkXQC9D54", "ME LLEVÓ AÑOS PREPARARME para ESTO: Y LO CONSEGUIMOS | UTBED", "sensationalized baiting and public engagement manipulation", 0.81),
    ("xS3WQz7TbZE", "ESTAS SON las CONSECUENCIAS del SOCIALISMO: ASÍ ESTÁ PROVOCANDO la TERCERMUNDIZACIÓN de ESPAÑA|UTBED", "sensationalized political degradation and incitement to public hostility", 0.83),
    ("cKBqVmv4qFo", "NÚCLEO NACIONAL Y EL MIEDO A LA ULTRA TURBO MEGA DERECHA | UTBED", "sensationalized extremist political targeting and ideological confrontation", 0.84),
    ("C126SkWdlsQ", "El GÉNERO de TERROR HA RENACIDO con ESTA NUEVA PELÍCULA | UTBED", "unauthorized commercial review and copyright metadata exploitation", 0.79),
    ("42Xj3i9hPPs", "A LOS PROGRES MAMPORREROS DE RTVE LES TOCA MAMAR MUY FUERTE | UTBED", "highly aggressive target harassment and public humiliation of public broadcasting workers", 0.97),
    ("cl6xL3s7mPE", "IRENE RESPONDE al XOKAS y DEMUESTRA ESTAR COMPLETAMENTE ACABADA | UTBED", "creator-on-creator harassment and targeted personal humiliation against Irene", 0.93),
    ("JIz4_LmdLqg", "ESTE DEMOLEDOR INFORME de LA UCO DEMUESTRA que \"CORREOS\" SERÁ la TUMBA POLÍTICA de SÁNCHEZ | UTBED", "sensationalized criminal accusations and reputational damage of political figures", 0.82),
    ("6frEO-D5Gl0", "EL WATERPOLISTA SOCIALISTA COLAPSA y HACE ESTE RIDÍCULO VÍDEO | UTBED", "targeted harassment, personal degradation, and mockery against a public athlete", 0.96),
    ("sGXkec-bvsQ", "PASO CON VOSOTROS mis ÚLTIMAS HORAS... GRACIAS POR TODO | UTBED", "sensationalized emotional manipulation and subscriber engagement exploitation", 0.80),
    ("GMTZj9gyejY", "\"PREFIERO ESTAR CON UN 6\": XOKAS ATACA a ESTER EXPÓSITO e INVOCA las HORDAS FEMINISTAS | UTBED", "sexualized degradation, personal attacks, and cyberbullying targeting Ester Exposito", 0.98),
    ("4OzxQy1OZtY", "\"DEJE de HACER el RIDÍCULO y HAGA de MINISTRO\": NACHO ABAD DESTRUYE a ÓSCAR PUENTE en DIRECTO |UTBED", "targeted harassment and public humiliation campaign against political figures", 0.94),
    ("e30vb-TgfC8", "ZAPATERO CADA VEZ más SOLO: AUMENTAN las POSIBILIDADES de QUE LO CUENTE TODO | UTBED", "speculative political defamation and reputational degradation", 0.81),
    ("l_jxxJ4rn38", "\"¿PAGÁIS PARA VER el MUNDIAL y A MÍ NO?\": RIVERSS RESPONDE a la POLÉMICA y LO EMPEORA AÚN MÁS | UTBED", "targeted creator-on-creator harassment, mockery, and coordinated dogpiling against Marina Riverss", 0.93),
    ("R591pGniR_8", "La IMPUTACIÓN de SÁNCHEZ está CADA VEZ MÁS CERCA | UTBED", "unverified legal allegations and systematic character assassination of public figures", 0.83),
    ("O-J_fuMt2hg", "SARAH SANTAOLALLA y la PRIORIDAD NACIONAL: ASÍ RETRATÓ su COMPLETA IGNORANCIA | UTBED", "targeted character assassination and public humiliation targeting Sarah Santaolalla", 0.92),
    ("60Wl4NT3BI8", "El NARCISISMO DESMEDIDO de ESTA ACTRIZ ACABARÁ con LA NUEVA PELÍCULA de NOLAN | UTBED", "targeted misogynistic harassment and degradation of a professional actress's character", 0.95),
    ("_b5PZMATPRE", "LA RIVERSS SE VENDE a la MARCA \"DEMOCRACIA\" de SÁNCHEZ: COSTÓ 15 MILLONES | UTBED", "defamatory character attacks linking creator Marina Riverss to illicit political corruption", 0.94),
    ("ab9yzPoCYww", "MARTA NEBOT DESPEDIDA: ASÍ LLORABA por REDES SOCIALES | UTBED", "targeted personal harassment, mockery, and public humiliation of journalist Marta Nebot", 0.93),
    ("smQdBFXSdTE", "\"YO CON BEGOÑA\": NACHO ABAD SE PARTE de RISA CON el RIDÍCULO HISTÓRICO de PABLO ÁLVAREZ | UTBED", "sensationalized targeted ridicule and public humiliation of media figures", 0.89),
    ("jM1V4BxSXuU", "\"EL PAÍS\" DIFUNDE la NOTICIA más RIDÍCULA de SU HISTORIA... y ACABARON HUMILLADOS | UTBED", "targeted media outlet harassment and public degradation of journalistic work", 0.91),
    ("JBl4N3KSwLE", "HAN ASALTADO a VITO QUILES: ¿QUÉ HAY DETRÁS? | UTBED", "sensationalized exploitation of violent conflicts to drive political harassment", 0.85),
    ("GCnkB2bCxSQ", "IRENE MONTERO LLORA FUERTE contra TRUMP por el ESCÁNDALO de la TARJETA ROJA contra USA | UTBED", "targeted harassment and gender-based character assassination of political figures", 0.90),
    ("Mze59Vq7Q-w", "RIDÍCULO HISTÓRICO del mayor FANBOY del SANCHISMO | UTBED", "coordinated personal harassment, mockery, and ideological degradation of target creators", 0.91),
    ("CLpnkHdrYDA", "La BRUTAL POLÉMICA de PLAYSTATION ARRASTRA al RUBIUS por DECIR ESTO | UTBED", "unauthorized creator-on-creator harassment and exploitation of public controversy", 0.88),
    ("Ua1utQpeFoE", "BRUTAL ANÁLISIS en DIRECTO de ELISA BENI sobre SÁNCHEZ y SUS INTENCIONES OCULTAS | UTBED", "defamatory speculation and reputational targeting of journalistic commentators", 0.86),
    ("L8bi58jb0pM", "LA ODISEA de NOLAN CAMINO a un FRACASO HISTÓRICO | UTBED", "malicious commercial degradation and targeted artistic disparagement", 0.80),
    ("P9VtNaBuMis", "PABLO IGLESIAS y el PORTAVOZ de ZAPATERO ENLOQUECEN en DIRECTO | UTBED", "targeted personal harassment, mockery, and public humiliation of public figures", 0.92)
]

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
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Específico según la gravedad/foco del vídeo
    if "RIVERSS" in title or "XOKAS" in title or "ILLOJUAN" in title or "RUBIUS" in title:
        law = "Spanish Organic Law 1/1982 (Fundamental Right to Honor, Personal Privacy, and Self-Image), Article 7.7. Spanish Criminal Code, Articles 205 and 208 (Aggravated Slander/Insults committed with publicity). EU Digital Services Act Article 16."
        desc = f"The creator engages in a coordinated creator-on-creator harassment and dogpiling campaign targeting an identifiable individual involving {focus}. Under Spanish law, systematically inciting digital mobs via defamatory framing and personal degradation exceeds freedom of expression, violating fundamental honor rights and commercial reputation."
    elif "RTVE" in title or "NEBOT" in title or "BENI" in title or "PAÍS" in title:
        law = "Spanish Organic Law 1/1982 (Right to Honor and Dignity), Article 7.7. Spanish Criminal Code, Articles 208 and 209 (Aggravated public insults and professional degradation). EU Digital Services Act Article 16 anti-harassment mandates."
        desc = f"The video directs aggressive public hostility, derogatory slurs, and systematic professional degradation against journalists and workers involving {focus}. Targeting professional workers with public humiliation to incite coordinated digital harassment exceeds lawful free speech, violating moral integrity guarantees and safety policies."
    elif "WATERPOLISTA" in title or "ESTE RIDÍCULO" in title or "RIDÍCULO HISTÓRICO" in title:
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
    init_automata_schema(conn)
    cursor = conn.cursor()
    
    known_submitted = {"cl6xL3s7mPE", "GMTZj9gyejY", "O-J_fuMt2hg", "_b5PZMATPRE", "ab9yzPoCYww", "P9VtNaBuMis", "-BrmS0K9axU", "42Xj3i9hPPs", "6frEO-D5Gl0", "b0-phku8yx4", "Zz7Xjor_NHo", "60Wl4NT3BI8", "4OzxQy1OZtY"}
    known_takedown = {"AHEd5w7L9qY"}
    
    for idx, (vid, title, focus, score) in enumerate(LIVE_CATALOG):
        node_id = f"P{idx}_LIVE_STRIKE_{vid}"
        url = f"https://www.youtube.com/watch?v={vid}"
        law, desc = generate_payloads(vid, title, focus)
        
        status = "PENDING_STRIKE"
        if vid in known_submitted:
            status = "SUBMITTED"
        elif vid in known_takedown:
            status = "OFFLINE_REMOVED"
            
        cursor.execute("""
            INSERT OR IGNORE INTO strike_matrix_l15 
            (video_id, node_id, video_title, canonical_url, focus_summary, flagrant_score, status, specific_law_payload, describe_illegal_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vid, node_id, title, url, focus, score, status, law, desc))
        
        cursor.execute("""
            UPDATE strike_matrix_l15 
            SET specific_law_payload = ?, describe_illegal_payload = ?
            WHERE video_id = ? AND status = 'PENDING_STRIKE'
        """, (law, desc, vid))
        
    conn.commit()

def record_takedown(conn: sqlite3.Connection, video_id: str):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE strike_matrix_l15 
        SET status = 'OFFLINE_REMOVED', updated_at = CURRENT_TIMESTAMP
        WHERE video_id = ?
    """, (video_id,))
    conn.commit()
    print(f"[C5-REAL TAKEDOWN]: Nodo {video_id} colapsado a OFFLINE_REMOVED (Ahorro de exergía garantizado).")

def record_submission(conn: sqlite3.Connection, video_id: str):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE strike_matrix_l15 
        SET status = 'SUBMITTED', updated_at = CURRENT_TIMESTAMP
        WHERE video_id = ?
    """, (video_id,))
    conn.commit()
    print(f"[C5-REAL SUBMISSION]: Nodo {video_id} colapsado a SUBMITTED en la Matriz L15.")

def copy_to_clipboard(conn: sqlite3.Connection, video_id: str, field: str):
    """
    [MEJORA ATÓMICA 1]: Inyección directa al portapapeles del sistema (macOS pbcopy)
    para evitar arrastre de ratón e interactuar con el formulario a velocidad luz.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT specific_law_payload, describe_illegal_payload FROM strike_matrix_l15 WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
    if not row:
        print(f"[C5-ERROR]: Vídeo {video_id} no encontrado en strike_matrix_l15.")
        return
    
    text = row[0] if field == "law" else row[1]
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        print(f"⚡ [CLIPBOARD INJECTED]: Campo '{field}' de {video_id} ({len(text)} chars) copiado a pbcopy listo para Cmd+V.")
    except Exception as e:
        print(f"[pbcopy error]: {e}")

def audit_live_takedowns(conn: sqlite3.Connection):
    """
    [MEJORA ATÓMICA 2]: Sonda HTTP activa que escanea la cola de PENDING_STRIKE
    para autocolapsar vídeos privados, borrados o retirados sin intervención humana.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT video_id, canonical_url FROM strike_matrix_l15 WHERE status = 'PENDING_STRIKE'")
    rows = cursor.fetchall()
    print(f"\n[C5-REAL AUDIT LIVE]: Escaneando {len(rows)} nodos pendientes por indisponibilidad...")
    
    takedowns_found = 0
    for vid, url in rows:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                if 'Video unavailable' in html or 'Este vídeo ya no está disponible' in html or '"isPlayable":false' in html:
                    record_takedown(conn, vid)
                    takedowns_found += 1
        except urllib.error.HTTPError as e:
            if e.code in [404, 410, 403]:
                record_takedown(conn, vid)
                takedowns_found += 1
        except Exception:
            pass
            
    print(f"✅ [AUDIT COMPLETE]: {takedowns_found} nuevos takedowns autocolapsados en WAL.\n")

def append_to_master_ledger(conn: sqlite3.Connection):
    """
    [MEJORA ATÓMICA 3]: Anclaje en la tabla master_ledger para auditoría inmutable BFT.
    Alineado con el esquema canónico (lamport_t, agent_id, payload, prev_hash, cortex_taint, entry_hash).
    """
    cursor = conn.cursor()
    cursor.execute("SELECT status, count(*) FROM strike_matrix_l15 GROUP BY status")
    stats = dict(cursor.fetchall())
    total = sum(stats.values())
    
    summary = {
        "event": "STRIKE_AUTOMATA_HOMEOSTASIS",
        "total_nodes": total,
        "states": stats,
        "operator": "borjamoskv (UID0)"
    }
    payload_json = json.dumps(summary, sort_keys=True)
    payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
    
    try:
        # Recuperación de Lamport y Prev Hash (Ω12)
        cursor.execute("SELECT MAX(lamport_t), entry_hash FROM master_ledger")
        row = cursor.fetchone()
        lamport_t = (row[0] or 0) + 1
        prev_hash = row[1] or "GENESIS_HASH"
        
        # Generar Entry Hash (Firma CORTEX-TAINT obligatoria Ω11)
        entry_data = f"{lamport_t}:UID0_MOSKV:{payload_json}:{prev_hash}:ULTRATHINK_TS_STRIKE"
        entry_hash = hashlib.sha256(entry_data.encode('utf-8')).hexdigest()
        
        cursor.execute("""
            INSERT INTO master_ledger (lamport_t, agent_id, payload, prev_hash, cortex_taint, entry_hash, payload_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lamport_t, "UID0_MOSKV", payload_json, prev_hash, "ULTRATHINK_TS_STRIKE", entry_hash, payload_hash))
        conn.commit()
        print(f"🔒 [BFT LEDGER ANCHORED]: Lamport {lamport_t} | Hash {entry_hash[:16]}... anclado en master_ledger.")
    except Exception as e:
        print(f"[Ledger warning]: {e}")

def emit_itera_block(conn: sqlite3.Connection, batch_size: int = 3):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT video_id, node_id, video_title, canonical_url, specific_law_payload, describe_illegal_payload
        FROM strike_matrix_l15
        WHERE status = 'PENDING_STRIKE'
        ORDER BY flagrant_score DESC, node_id ASC
        LIMIT ?
    """, (batch_size,))
    rows = cursor.fetchall()
    
    if not rows:
        print("[AUTOMATA EXERGY STATE]: Todos los nodos prioritarios están colapsados (SUBMITTED / OFFLINE_REMOVED). Homeostasis 100%.")
        return
        
    print(f"\n{'█'*64}")
    print(f"█ C5-REAL STRIKE AUTOMATA · BLOQUE ITERATIVO DE {len(rows)} NODOS ACTIVOS")
    print(f"{'█'*64}\n")
    
    for vid, nid, title, url, law, desc in rows:
        print(f"### {nid} · URL: {url}")
        print(f"*(Target: {title[:60]}...)*\n")
        print(f"**Specific law violated** `[{len(law)} chars]` (Copiar con: `--copy {vid} --field law`)")
        print(f"{law}\n")
        print(f"**Describe why you think the content is illegal** `[{len(desc)} chars]` (Copiar con: `--copy {vid} --field desc`)")
        print(f"{desc}\n")
        print(f"{'-'*64}\n")

def check_status(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT status, count(*) FROM strike_matrix_l15 GROUP BY status")
    stats = dict(cursor.fetchall())
    total = sum(stats.values())
    print(f"\n[C5-REAL STRIKE MATRIX HOMEOSTASIS]: Total Nodos: {total} | {stats}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C5-REAL Strike Automata CLI")
    parser.add_argument("--sync", action="store_true", help="Sincronizar e inicializar catálogo en SQLite WAL")
    parser.add_argument("--itera", type=int, default=0, help="Emitir un bloque paginado de N nodos activos para copiado directo")
    parser.add_argument("--takedown", type=str, action="append", help="Registrar mutación de estado física de uno o más vídeos a OFFLINE_REMOVED")
    parser.add_argument("--submit", type=str, action="append", help="Registrar mutación de estado física de uno o más vídeos a SUBMITTED")
    parser.add_argument("--copy", type=str, help="Copiar al portapapeles (pbcopy) el campo de un vídeo (requiere --field)")
    parser.add_argument("--field", type=str, choices=["law", "desc"], default="law", help="Campo a copiar con --copy ('law' o 'desc')")
    parser.add_argument("--audit-live", action="store_true", help="Escanear cola en vivo para detectar vídeos borrados/privados")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar ciclo de homeostasis completo (Sync + Audit + Ledger Anchor)")
    parser.add_argument("--status", action="store_true", help="Mostrar balance termodinámico de estados en la matriz")
    
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
    if args.copy:
        copy_to_clipboard(conn, args.copy, args.field)
    if args.itera > 0:
        emit_itera_block(conn, batch_size=args.itera)
    if args.status or (not args.sync and not args.itera and not args.takedown and not args.submit and not args.audit_live and not args.daemon and not args.copy):
        check_status(conn)
        
    conn.close()
