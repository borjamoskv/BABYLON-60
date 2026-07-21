"""
CORTEX Escohotado Market & Prohibition Economics Engine (C5-REAL)
Models the formal economics of prohibitionism ('Historia General de las Drogas')
and the informational entropy of property suppression ('Los Enemigos del Comercio').

Rule Compliance: Ω10 (SQLite WAL + busy_timeout), Ω31 (Empirical Metric Calculation).
"""

import math
import sqlite3
import os
import hashlib
import datetime
from typing import Dict, List, Any

DB_PATH = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/ledgers/escohotado_economics.db"

def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prohibition_economics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                enforcement_level REAL NOT NULL,
                property_rights_index REAL NOT NULL,
                risk_premium_multiplier REAL NOT NULL,
                purity_index REAL NOT NULL,
                black_market_violence_index REAL NOT NULL,
                information_loss_index REAL NOT NULL,
                systemic_exergy_loss REAL NOT NULL,
                cortex_taint TEXT NOT NULL,
                UNIQUE(enforcement_level, property_rights_index)
            );
        """)
    conn.close()

def simulate_prohibition_and_property(enforcement: float, property_rights: float) -> Dict[str, Any]:
    """
    enforcement (0.0 to 1.0): Legal Prohibition & Police Enforcement Level
    property_rights (0.0 to 1.0): Respect for Private Property Rights & Free Price Signals
    """
    enforcement = max(0.0, min(1.0, enforcement))
    property_rights = max(0.0, min(1.0, property_rights))

    # Risk premium multiplier on black market (Escohotado Renta de Ilegalidad)
    risk_premium = 1.0 + 8.5 * math.pow(enforcement, 1.8)

    # Purity degradation under prohibition
    purity = max(0.05, 1.0 - 0.85 * enforcement)

    # Violence index (Cartelization & lack of legal recourse)
    violence_index = 10.0 * math.pow(enforcement, 2.0) * (2.0 - property_rights)

    # Price Signal Noise / Information Loss (Hayek-Mises-Escohotado)
    info_loss = 1.0 - property_rights

    # Systemic Exergy Loss: Wasted enforcement capital + misallocation + health damage
    exergy_loss = (0.4 * enforcement + 0.6 * info_loss) * risk_premium

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    taint_raw = f"{enforcement}:{property_rights}:{risk_premium}:{purity}:{violence_index}:{info_loss}:{ts}"
    cortex_taint = hashlib.sha3_256(taint_raw.encode('utf-8')).hexdigest()

    return {
        "timestamp": ts,
        "enforcement_level": enforcement,
        "property_rights_index": property_rights,
        "risk_premium_multiplier": round(risk_premium, 4),
        "purity_index": round(purity, 4),
        "black_market_violence_index": round(violence_index, 4),
        "information_loss_index": round(info_loss, 4),
        "systemic_exergy_loss": round(exergy_loss, 4),
        "cortex_taint": f"borjamoskv:escohotado_econ:{cortex_taint[:16]}"
    }

def run_economic_grid(enforcement_levels: List[float], property_indices: List[float], db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    results = []

    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    for enf in enforcement_levels:
        for pr in property_indices:
            res = simulate_prohibition_and_property(enf, pr)
            results.append(res)
            with conn:
                conn.execute("""
                    INSERT OR REPLACE INTO prohibition_economics 
                    (timestamp, enforcement_level, property_rights_index, risk_premium_multiplier, 
                     purity_index, black_market_violence_index, information_loss_index, systemic_exergy_loss, cortex_taint)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (res["timestamp"], res["enforcement_level"], res["property_rights_index"], 
                      res["risk_premium_multiplier"], res["purity_index"], res["black_market_violence_index"], 
                      res["information_loss_index"], res["systemic_exergy_loss"], res["cortex_taint"]))

    conn.close()
    return results

if __name__ == "__main__":
    enf_grid = [0.0, 0.25, 0.50, 0.75, 1.0]
    pr_grid = [0.0, 0.50, 1.0]
    res = run_economic_grid(enf_grid, pr_grid)
    print(f"Executed {len(res)} economic simulation points. DB Updated at {DB_PATH}")
