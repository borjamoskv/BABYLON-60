#!/usr/bin/env python3
"""
PARTITION CAMPAIGNS · Particionador Estratégico de Campañas para BABYLON-60
Divide la base de datos de 10.000 leads en campañas segmentadas por vertical
y genera la campaña Tier-1 España de Máxima Prioridad.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING
import hashlib
import re

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


def partition_campaigns() -> None:
    print("=" * 75)
    print("       PARTICIONADOR ESTRATÉGICO DE CAMPAÑAS ENTERPRISE")
    print("=" * 75)

    conn = sqlite3.connect(Path(DB_PATH).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # Keep validation and export on one read snapshot even if a writer commits.
        conn.execute("BEGIN")
        for row in cur.execute("SELECT * FROM leads"):
            require_commercial_record(dict(row))
    except Exception:
        conn.close()
        raise
    os.makedirs(CAMPAIGNS_DIR, exist_ok=True)

    # 1. Partición por sectores
    cur.execute("SELECT DISTINCT sector FROM leads ORDER BY sector;")
    sectors = [r["sector"] for r in cur.fetchall()]

    summary = {}
    for s in sectors:
        clean_name = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:80] or "sector"
        sector_digest = hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]
        filename = f"campaign_{clean_name}_{sector_digest}.jsonl"
        filepath = os.path.join(CAMPAIGNS_DIR, filename)

        cur.execute("SELECT * FROM leads WHERE sector = ? ORDER BY lead_id;", (s,))
        rows = cur.fetchall()

        with open(filepath, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")

        summary[s] = len(rows)
        print(f"➔ {s:<35} | {len(rows):>5} leads | {filename}")

    # 2. Campaña Especial: Tier-1 España (Madrid, Barcelona, Bilbao, Valencia)
    tier1_path = os.path.join(CAMPAIGNS_DIR, "campaign_tier1_spain_top_priority.jsonl")
    cur.execute("""
        SELECT * FROM leads 
        WHERE country = 'España' AND (target_role LIKE '%CISO%' OR target_role LIKE '%DPO%')
        ORDER BY lead_id;
    """)
    tier1_rows = cur.fetchall()
    with open(tier1_path, "w", encoding="utf-8") as f:
        for row in tier1_rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")

    print("-" * 75)
    print(f"➔ Tier-1 España (CISO & DPO):       | {len(tier1_rows):>5} leads | campaign_tier1_spain_top_priority.jsonl")
    print(f"➔ Total campañas generadas en: {CAMPAIGNS_DIR}")
    print("=" * 75)
    conn.close()


if __name__ == "__main__":
    partition_campaigns()
