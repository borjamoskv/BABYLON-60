#!/usr/bin/env python3
"""
OUTREACH COCKPIT · TUI de Telemetría y Monitorización de Prospección BABYLON-60
Visualiza el estado de las campañas, métricas de base de datos FTS5 y cola de despacho.
"""

import sqlite3
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.lead_data_policy import (
        COMMERCIAL_DB_PATH,
        CAMPAIGNS_DIR,
        require_commercial_record as require_commercial_record,
    )
else:
    try:
        from scripts.lead_data_policy import (
            COMMERCIAL_DB_PATH,
            CAMPAIGNS_DIR,
            require_commercial_record as require_commercial_record,
        )
    except ModuleNotFoundError:
        from lead_data_policy import (
            COMMERCIAL_DB_PATH,
            CAMPAIGNS_DIR,
            require_commercial_record as require_commercial_record,
        )

DB_PATH = COMMERCIAL_DB_PATH
QUEUE_PATH = CAMPAIGNS_DIR / "outreach_queue_tier1_spain.jsonl"


def render_cockpit() -> None:
    if not os.path.exists(DB_PATH):
        print(f"Error: Base de datos no encontrada en {DB_PATH}")
        return

    conn = sqlite3.connect(Path(DB_PATH).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # Report only the same snapshot whose provenance was validated.
        conn.execute("BEGIN")
        for row in cur.execute("SELECT * FROM leads"):
            require_commercial_record(dict(row))
    except Exception:
        conn.close()
        raise

    cur.execute("SELECT COUNT(*) FROM leads;")
    total_leads = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT country) FROM leads;")
    total_countries = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT sector) FROM leads;")
    total_sectors = cur.fetchone()[0]

    cur.execute("SELECT sector, COUNT(*) FROM leads GROUP BY sector ORDER BY COUNT(*) DESC;")
    sector_counts = cur.fetchall()

    cur.execute("SELECT target_role, COUNT(*) FROM leads GROUP BY target_role ORDER BY COUNT(*) DESC;")
    role_counts = cur.fetchall()

    queue_count = 0
    if os.path.exists(QUEUE_PATH):
        with open(QUEUE_PATH, "r", encoding="utf-8") as qf:
            queue_count = sum(1 for _ in qf)

    conn.close()

    print("╔══════════════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║               BABYLON-60 · SOVEREIGN OUTREACH COCKPIT & TELEMETRÍA DE PROSPECCIÓN               ║")
    print("╚══════════════════════════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("╭─ [MÉTRICAS GLOBALES DEL WORKING SET] ────────────────────────────────────────────────────────────╮")
    print(f"│ • Contactos en base privada:      {total_leads:,} registros (SQLite WAL + FTS5 indexado)")
    print(f"│ • Países registrados:         {total_countries} etiquetas geográficas")
    print(f"│ • Sectores registrados:     {total_sectors} etiquetas sin clasificación jurídica automática")
    print(f"│ • Cola Asincrónica Tier-1:     {queue_count:,} borradores pendientes de revisión")
    print("╰──────────────────────────────────────────────────────────────────────────────────────────────────╯")
    print()
    print("╭─ [DESGLOSE POR SECTORES REGISTRADOS] ────────────────────────────────────────────────────────────╮")
    for s, c in sector_counts:
        pct = (c / total_leads) * 100
        bar = "█" * int(pct // 2)
        print(f"│ {s:<36} | {c:>5} ({pct:>4.1f}%) | {bar}")
    print("╰──────────────────────────────────────────────────────────────────────────────────────────────────╯")
    print()
    print("╭─ [DISTRIBUCIÓN POR ROLES DECISORES TÉCNICOS] ────────────────────────────────────────────────────╮")
    for r, c in role_counts:
        pct = (c / total_leads) * 100
        bar = "▓" * int(pct // 2)
        print(f"│ {r:<45} | {c:>5} ({pct:>4.1f}%) | {bar}")
    print("╰──────────────────────────────────────────────────────────────────────────────────────────────────╯")
    print()
    print("╭─ [ESTADO DEL AIR-GAP Y POLÍTICA DE DESPACHO] ────────────────────────────────────────────────────╮")
    print("│ • Estado:                    Borradores locales pendientes de revisión")
    print("│ • Procedencia:               Declarada en cada registro; no prueba de autorización legal")
    print("│ • Auditoría local:           Sintaxis básica e integridad; no verificación de buzón")
    print("│ • Despacho automático:       No implementado por estas herramientas")
    print("╰──────────────────────────────────────────────────────────────────────────────────────────────────╯")
    print()


if __name__ == "__main__":
    render_cockpit()
