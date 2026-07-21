"""
CORTEX Escohotado Chaos & Thermodynamic Simulation Engine (C5-REAL)
Models the non-linear dynamics of self-organizing vs state-coerced systems
as conceptualized in Antonio Escohotado's 'Caos y Orden' (1999).

Calculates exact physical entropy S = -sum(p_i * ln(p_i)) and Lyapunov exponent.
Rule Compliance: Ω10 (SQLite WAL + busy_timeout), Ω31 (Physical Entropy Calculation).
"""

import math
import sqlite3
import os
import json
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

DB_PATH = str(Path(__file__).resolve().parent.parent / "ledgers" / "escohotado_chaos_entropy.db")

def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chaos_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                growth_r REAL NOT NULL,
                coercion_c REAL NOT NULL,
                entropy_s REAL NOT NULL,
                lyapunov_exp REAL NOT NULL,
                regime TEXT NOT NULL,
                cortex_taint TEXT NOT NULL,
                UNIQUE(growth_r, coercion_c)
            );
        """)
    conn.close()

def compute_entropy(trajectory: List[float], num_bins: int = 50) -> float:
    """Computes exact Shannon/Gibbs entropy S = -sum(p_i * ln(p_i))."""
    if not trajectory:
        return 0.0
    
    min_v, max_v = min(trajectory), max(trajectory)
    if max_v - min_v < 1e-9:
        return 0.0

    bin_width = (max_v - min_v) / num_bins
    counts = [0] * num_bins

    for val in trajectory:
        idx = int((val - min_v) / bin_width)
        if idx >= num_bins:
            idx = num_bins - 1
        counts[idx] += 1

    total = len(trajectory)
    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log(p)

    return entropy

def compute_lyapunov(trajectory: List[float], r: float, c: float) -> float:
    """Computes the Lyapunov exponent to quantify chaos vs stability."""
    if len(trajectory) < 2:
        return 0.0
    
    sum_log_deriv = 0.0
    valid_points = 0

    for x in trajectory:
        deriv = abs(r * (1.0 - 2.0 * x) - c)
        if deriv > 1e-12:
            sum_log_deriv += math.log(deriv)
            valid_points += 1

    return sum_log_deriv / valid_points if valid_points > 0 else 0.0

def simulate_system(r: float, c: float, x0: float = 0.4, steps: int = 2000, transient: int = 500) -> Dict[str, Any]:
    """
    Simulates x_{t+1} = max(0, r * x_t * (1 - x_t) - c * x_t)
    r: Spontaneous exchange growth rate
    c: State coercion extraction rate
    """
    x = x0
    trajectory = []

    for t in range(steps + transient):
        x_next = r * x * (1.0 - x) - c * x
        x = max(0.0, min(1.0, x_next))
        if t >= transient:
            trajectory.append(x)

    s_val = compute_entropy(trajectory)
    lyap_val = compute_lyapunov(trajectory, r, c)

    if lyap_val > 0.05 and s_val > 1.5:
        regime = "COMPLEX_SELF_ORGANIZATION"
    elif lyap_val <= 0 and s_val < 0.5:
        regime = "STAGNANT_COERCIVE_FREEZE"
    elif s_val == 0.0:
        regime = "SYSTEMIC_COLLAPSE"
    else:
        regime = "PERIODIC_OSCILLATION"

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    taint_raw = f"{r}:{c}:{s_val}:{lyap_val}:{ts}"
    cortex_taint = hashlib.sha3_256(taint_raw.encode('utf-8')).hexdigest()

    return {
        "timestamp": ts,
        "growth_r": r,
        "coercion_c": c,
        "entropy_s": s_val,
        "lyapunov_exp": lyap_val,
        "regime": regime,
        "cortex_taint": f"borjamoskv:escohotado_chaos:{cortex_taint[:16]}"
    }

def run_simulation_grid(r_values: List[float], c_values: List[float], db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    results = []

    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    for r in r_values:
        for c in c_values:
            res = simulate_system(r, c)
            results.append(res)
            with conn:
                conn.execute("""
                    INSERT OR REPLACE INTO chaos_metrics 
                    (timestamp, growth_r, coercion_c, entropy_s, lyapunov_exp, regime, cortex_taint)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (res["timestamp"], res["growth_r"], res["coercion_c"], res["entropy_s"], res["lyapunov_exp"], res["regime"], res["cortex_taint"]))
    
    conn.close()
    return results

if __name__ == "__main__":
    r_range = [2.5, 3.2, 3.7, 3.9]
    c_range = [0.0, 0.05, 0.15, 0.30]
    res = run_simulation_grid(r_range, c_range)
    print(f"Executed {len(res)} simulation points. DB Updated at {DB_PATH}")
