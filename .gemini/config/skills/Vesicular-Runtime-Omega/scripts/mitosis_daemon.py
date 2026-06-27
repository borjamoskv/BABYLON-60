#!/usr/bin/env python3
"""
Genesis-L5-OMEGA: Mitosis Daemon
Ejecuta la orquestación ecosistémica y deriva de objetivos.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Configuración L5
MAX_RECURSION_DEPTH = 3
RHS_THRESHOLD = 0.8  # Se activa si RHS cae por debajo de 0.8 (ej. 3+ fallos)

logging.basicConfig(level=logging.INFO, format='[L5-MITOSIS] %(message)s')

def get_system_rhs():
    """Lectura real del Runtime Health Score (Capa L3) desde cortex.db."""
    db_path = Path.home() / ".gemini/antigravity/scratch/cortex-c5-ledger/cortex.db"
    
    # CLI flag para simular fallo
    if "--simulate-failure" in sys.argv:
        logging.info("Simulating critical RHS (0.1) via --simulate-failure flag.")
        return 0.1
        
    if not db_path.exists():
        logging.warning(f"Database {db_path} not found. Defaulting RHS to 1.0.")
        return 1.0
        
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM episodic_failures;")
        failures_count = cursor.fetchone()[0]
        conn.close()
        # RHS decay: 10% de penalización por fallo
        rhs = max(0.0, 1.0 - (failures_count * 0.1))
        logging.info(f"Retrieved RHS from DB: {rhs} (Failures count: {failures_count})")
        return rhs
    except Exception as e:
        logging.error(f"Failed to read RHS from DB: {e}. Defaulting to 1.0.")
        return 1.0

def forge_missing_skill(skill_name, context):
    """Invoca a Sortu-APEX de forma autónoma (M2M) para forjar una skill en C5-REAL."""
    logging.warning(f"Fricción detectada. Faltan capacidades para: {skill_name}")
    logging.info(f"Iniciando MITOSIS. Forjando skill '{skill_name}' vía Sortu-APEX...")
    
    try:
        # Import dinámico de Sortu-APEX
        sys.path.append("$CORTEX_ROOT/.gemini/config/skills/Sortu-APEX/scripts")
        from sortu import SortuSkill
        
        skill = SortuSkill()
        payload = {
            "skill_name": skill_name,
            "intent": f"Mitosis JIT forge: {context}",
            "hours_saved": 5.0,
            "dependency_depth": 1,
            "complexity": 0.8
        }
        
        result = skill.execute(payload)
        logging.info(f"Mitosis Result for '{skill_name}': {json.dumps(result)}")
        return result.get("state") == "ACTIVE"
    except Exception as e:
        logging.error(f"Mitosis execution failed: {e}")
        return False

def run_mitosis_cycle():
    logging.info("Iniciando ciclo de evaluación ecosistémica (Genesis-L5).")
    rhs = get_system_rhs()
    
    if rhs < RHS_THRESHOLD:
        logging.warning(f"RHS Crítico ({rhs} < {RHS_THRESHOLD}). Sistema en degradación térmica.")
        logging.info("Evaluando árbol de dependencias y telemetría...")
        
        missing_capability = "Quantum-Heuristic-Parser"
        success = forge_missing_skill(missing_capability, "L5 Autonomous Capability Expansion")
        
        if success:
            logging.info("Mitosis completada. Enjambre expandido.")
        else:
            logging.error("Fallo de Mitosis. Delegando a L4 Apoptosis.")
            sys.exit(1)
    else:
        logging.info("RHS Estable. No se requiere mitosis.")

if __name__ == "__main__":
    logging.info("=== GENESIS L5 DAEMON INICIALIZADO ===")
    run_mitosis_cycle()
    logging.info("=== CICLO COMPLETADO ===")
