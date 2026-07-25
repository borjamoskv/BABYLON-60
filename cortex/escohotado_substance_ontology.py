# C5-REAL EXERGY CERTIFIED
"""
CORTEX Escohotado Monistic Substance & Process Engine (C5-REAL)
Models the continuous ontology of 'Realidad y Substancia' (1985/1997).

Formalizes the transformation of potentiality into actuality and the collapse
of Cartesian/Kantian subject-object dualism (D_dual -> 0).

Rule Compliance: Ω10 (SQLite WAL + busy_timeout), Ω31 (Physical State Mapping).
"""

import math
import sqlite3
import os
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Any

DB_PATH = str(Path(__file__).resolve().parent.parent / "ledgers" / "escohotado_substance.db")

def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS substance_ontology (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                potentiality_phi REAL NOT NULL,
                actuality_phi REAL NOT NULL,
                dualism_index REAL NOT NULL,
                substance_exergy_density REAL NOT NULL,
                ontological_regime TEXT NOT NULL,
                cortex_taint TEXT NOT NULL,
                UNIQUE(potentiality_phi, actuality_phi, dualism_index)
            );
        """)
    conn.close()

def compute_substance_state(potentiality: float, actuality: float, dualism_separation: float) -> Dict[str, Any]:
    """
    potentiality (0.0 to 1.0): Virtual state options (Dynamis)
    actuality (0.0 to 1.0): Manifested physical structure (Energeia)
    dualism_separation (0.0 to 1.0): Degree of subject-object split (1.0 = Kantian Noumenon/Phenomenon split)
    """
    pot = max(0.0, min(1.0, potentiality))
    act = max(0.0, min(1.0, actuality))
    dual = max(0.0, min(1.0, dualism_separation))

    # Substance Exergy Density: E_substance = Actuality * (1 - Dualism) * sqrt(Potentiality)
    exergy_density = act * (1.0 - dual) * math.sqrt(pot if pot > 0 else 1e-6)

    if dual < 0.15 and act > 0.6:
        regime = "MONISTIC_PROCESS_REALITY (C5-REAL Escohotado)"
    elif dual >= 0.70:
        regime = "CARTESIAN_KANTIAN_DUALIST_SPLIT (C4-SIM Abstraction)"
    elif act < 0.20:
        regime = "UNMANIFESTED_VIRTUAL_POTENTIAL"
    else:
        regime = "TRANSITIONAL_DIALECTIC_PROCESS"

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    taint_raw = f"{pot}:{act}:{dual}:{exergy_density}:{regime}:{ts}"
    cortex_taint = hashlib.sha3_256(taint_raw.encode("utf-8")).hexdigest()

    return {
        "timestamp": ts,
        "potentiality_phi": pot,
        "actuality_phi": act,
        "dualism_index": dual,
        "substance_exergy_density": round(exergy_density, 4),
        "ontological_regime": regime,
        "cortex_taint": f"borjamoskv:escohotado_substance:{cortex_taint[:16]}",
    }

def run_substance_grid(
    pot_range: List[float],
    act_range: List[float],
    dual_range: List[float],
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    init_db(db_path)
    results = []

    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    for pot in pot_range:
        for act in act_range:
            for dual in dual_range:
                res = compute_substance_state(pot, act, dual)
                results.append(res)
                with conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO substance_ontology
                        (timestamp, potentiality_phi, actuality_phi, dualism_index, substance_exergy_density, ontological_regime, cortex_taint)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            res["timestamp"],
                            res["potentiality_phi"],
                            res["actuality_phi"],
                            res["dualism_index"],
                            res["substance_exergy_density"],
                            res["ontological_regime"],
                            res["cortex_taint"],
                        ),
                    )

    conn.close()
    return results

if __name__ == "__main__":
    p_grid = [0.2, 0.8, 1.0]
    a_grid = [0.1, 0.7, 1.0]
    d_grid = [0.0, 0.4, 0.9]
    res = run_substance_grid(p_grid, a_grid, d_grid)
    print(f"Executed {len(res)} substance ontology points. DB Updated at {DB_PATH}")
