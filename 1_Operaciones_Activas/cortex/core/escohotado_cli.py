# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX Escohotado Unified CLI Transducer (C5-REAL)
Command-line interface to query and inspect all 3 Escohotado SQLite Ledgers:
1. Caos y Orden Entropy & Lyapunov Phase Space (ledgers/escohotado_chaos_entropy.db)
2. Market & Prohibition Economics (ledgers/escohotado_economics.db)
3. Substance Process Ontology (ledgers/escohotado_substance.db)

Rule Compliance: Ω10 (SQLite WAL query), Ω14 (Environment Parametrization).
"""

import os
import sqlite3
import json
import argparse
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAOS_DB = os.path.join(BASE_DIR, "ledgers", "escohotado_chaos_entropy.db")
ECON_DB = os.path.join(BASE_DIR, "ledgers", "escohotado_economics.db")
SUBSTANCE_DB = os.path.join(BASE_DIR, "ledgers", "escohotado_substance.db")

def query_chaos_db() -> List[Dict[str, Any]]:
    if not os.path.exists(CHAOS_DB):
        return []
    conn = sqlite3.connect(CHAOS_DB, timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT growth_r, coercion_c, entropy_s, lyapunov_exp, regime FROM chaos_metrics ORDER BY growth_r, coercion_c"
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def query_econ_db() -> List[Dict[str, Any]]:
    if not os.path.exists(ECON_DB):
        return []
    conn = sqlite3.connect(ECON_DB, timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT enforcement_level, property_rights_index, risk_premium_multiplier, purity_index, black_market_violence_index, information_loss_index, systemic_exergy_loss FROM prohibition_economics ORDER BY enforcement_level, property_rights_index"
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def query_substance_db() -> List[Dict[str, Any]]:
    if not os.path.exists(SUBSTANCE_DB):
        return []
    conn = sqlite3.connect(SUBSTANCE_DB, timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT potentiality_phi, actuality_phi, dualism_index, substance_exergy_density, ontological_regime FROM substance_ontology ORDER BY dualism_index, actuality_phi, potentiality_phi"
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def main() -> None:
    parser = argparse.ArgumentParser(description="CORTEX Escohotado Unified CLI Transducer (C5-REAL)")
    parser.add_argument(
        "--module",
        choices=["chaos", "econ", "substance", "all"],
        default="all",
        help="Target ledger module",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON payload")

    args = parser.parse_args()

    payload = {}
    if args.module in ["chaos", "all"]:
        payload["caos_y_orden"] = query_chaos_db()
    if args.module in ["econ", "all"]:
        payload["drogas_y_comercio"] = query_econ_db()
    if args.module in ["substance", "all"]:
        payload["realidad_y_substancia"] = query_substance_db()

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("================================================================================")
        print("            CORTEX ESCOHOTADO UNIFIED C5-REAL METRIC TRANSDUCER                ")
        print("================================================================================")
        if "caos_y_orden" in payload:
            print("\n[1] CAOS Y ORDEN (Sistemas No Lineales & Entropía Física):")
            for row in payload["caos_y_orden"][:5]:
                print(
                    f"  r={row['growth_r']:.2f} | c={row['coercion_c']:.2f} -> S={row['entropy_s']:.4f} | λ={row['lyapunov_exp']:.4f} | Regime: {row['regime']}"
                )
        if "drogas_y_comercio" in payload:
            print("\n[2] HISTORIA DE LAS DROGAS Y ENEMIGOS DEL COMERCIO (Economía de Prohibición):")
            for row in payload["drogas_y_comercio"][:5]:
                print(
                    f"  Enf={row['enforcement_level']:.2f} | PR={row['property_rights_index']:.2f} -> Risk={row['risk_premium_multiplier']:.2f}x | Purity={row['purity_index']:.2f} | Violence={row['black_market_violence_index']:.2f}"
                )
        if "realidad_y_substancia" in payload:
            print("\n[3] REALIDAD Y SUBSTANCIA (Ontología de Proceso Monista):")
            for row in payload["realidad_y_substancia"][:5]:
                print(
                    f"  Φ_pot={row['potentiality_phi']:.2f} | Φ_act={row['actuality_phi']:.2f} | Dual={row['dualism_index']:.2f} -> Exergy={row['substance_exergy_density']:.4f} | {row['ontological_regime']}"
                )
        print("================================================================================")

if __name__ == "__main__":
    main()
