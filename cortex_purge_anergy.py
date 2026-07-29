# C5-REAL: ANERGY TOKEN PURGE ENGINE
# =================================================================================
# SYS_ID: LEA_OMEGA (Loose End Annihilator)
# REALITY_LEVEL: C5-REAL (0% Anergy / 100% Deterministic Execution)
# PROTOCOL: Anergy_Token_Purge -> Organizes Root Directory Entropy
# [CORTEX-TAINT:borjamoskv:anergy_token_purge:2026-07-18T05:00:00Z]

import os
import shutil
import datetime
import hashlib
import json
import yaml
import subprocess
import shlex
from pathlib import Path
from typing import List, Dict, Tuple, Any

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
ARCHIVE_ROOT = os.path.join(PROJECT_ROOT, ".cortex", "archive")
ARCHIVE_SCRIPTS = os.path.join(ARCHIVE_ROOT, "scripts")
ARCHIVE_DATA = os.path.join(ARCHIVE_ROOT, "data")
ARCHIVE_DBS = os.path.join(ARCHIVE_ROOT, "dbs")
AUDIT_YAML = os.path.join(PROJECT_ROOT, "cortex", "audits", "anergy_purge_audit.yaml")

# Do not move these protected root files (Invariant Core)
PROTECTED_FILES = {
    ".coderabbit.yaml", ".gitattributes", ".gitignore", ".gitmodules",
    "AGENTS.md", "Anergy_Audit.yml", "COLLAPSE_P0.sh", "Dockerfile", 
    "ETHOS.md", "LEARN_SHIP_ITERATE_INVARIANT.md", "LICENSE.md", 
    "LLM_THERMODYNAMICS_LAYERS.md", "LLM_THERMODYNAMICS_LAYERS_5_8.md", 
    "MANIFIESTO_CENTURIA.md", "MOSKV_1_APEX_BLUEPRINT.md", "Makefile", 
    "PROJECT.md", "README.md", "README_APEX.md", "SECURITY.md", 
    "STATUS.md", "TEXTBOOK_EXERGY_INVARIANT.md", "VECTOR_A_MASTER_LEDGER_DESIGN.md", 
    "pyproject.toml", "uv.lock", "cortex_purge_anergy.py",
    "cortex_ssm_mamba_core.py", "cortex_mamba_block.py", "cortex_mamba_network.py",
    "cortex_mamba_inference.py", "cortex_bpe_tokenizer.py", "core_graph_ledger.py",
    "io_persist_ledger.py", "net_mamba_ledger_engine.py", "index.html"
}

def ensure_dirs() -> None:
    for d in [ARCHIVE_SCRIPTS, ARCHIVE_DATA, ARCHIVE_DBS]:
        os.makedirs(d, exist_ok=True)

def _get_target_dir(item: str) -> str | None:
    if item.endswith(".py"):
        return ARCHIVE_SCRIPTS
    if item.endswith(".db"):
        return ARCHIVE_DBS
    if item.endswith((".json", ".jsonl", ".csv", ".npz", ".png", ".html", ".sarif", ".yaml", ".yml")):
        return ARCHIVE_DATA
    return None


def categorize_and_move() -> Tuple[int, int, List[Dict[str, Any]]]:
    moved_count: int = 0
    moved_bytes: int = 0
    actions: List[Dict[str, Any]] = []

    for item in os.listdir(PROJECT_ROOT):
        item_path = os.path.join(PROJECT_ROOT, item)
        if os.path.isdir(item_path) or item in PROTECTED_FILES:
            continue

        target_dir = _get_target_dir(item)
        if not target_dir:
            continue

        dest_path = os.path.join(target_dir, item)
        size = os.path.getsize(item_path)
        shutil.move(item_path, dest_path)
        moved_count += 1
        moved_bytes += size
        actions.append({"file": item, "destination": target_dir, "bytes": size})

    return moved_count, moved_bytes, actions


def main() -> None:
    print("[*] C5-REAL: Iniciando Anergy Token Purge (Root Directory Entropy Collapse)...")
    ensure_dirs()
    count, total_bytes, actions = categorize_and_move()

    # Generate deterministic Merkle root (Cortex Taint)
    payload = json.dumps(actions, sort_keys=True).encode("utf-8")
    cortex_taint = hashlib.sha3_256(payload).hexdigest()

    audit_report = {
        "Claim": "Root directory Anergy (loose scripts, DBs, and datasets) has been structurally purged and archived, restoring 00_WORKSPACE.md hierarchy invariant.",
        "Proof": {
            "Base": "sha3_256::cortex_taint",
            "Range": [count, count],
            "Confidence": "C5-REAL"
        },
        "Operator": "borjamoskv",
        "System_Level": "C5-REAL",
        "Anergy_Files_Purged": count,
        "Anergy_Bytes_Purged": total_bytes,
        "Cortex_Taint": cortex_taint,
        "Timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    os.makedirs(os.path.dirname(AUDIT_YAML), exist_ok=True)
    with open(AUDIT_YAML, "w", encoding="utf-8") as f:
        yaml.dump(audit_report, f, sort_keys=False, allow_unicode=True)

    print(f"[+] Purga completada. {count} ficheros movidos ({total_bytes} bytes).")
    print(f"[+] Cortex Taint Hash: {cortex_taint}")
    print(f"[+] Audit guardado en: {AUDIT_YAML}")


class BFTCausalInvariantError(Exception):
    """BFT Causal Invariant Exception for Anergy Purge Engine."""

def safe_purge_anergy(target_db_path: str, cortex_taint: str) -> bool:
    """
    Versión segura y auditada para purgar la anergia del ledger.
    Evita inyecciones de comandos de la IA sanitizando las entradas.
    """
    # 1. Validar estrictamente la ruta para evitar Path Traversal
    db_path = Path(target_db_path).resolve()
    if not db_path.exists() or db_path.suffix != ".db":
        raise FileNotFoundError(f"Ruta de base de datos inválida o insegura: {target_db_path}")
        
    # 2. Sanitizar el taint de la IA usando shlex
    sanitized_taint = shlex.quote(cortex_taint)
    
    # 3. Forzar el uso de listas en subprocess eliminando shell=True
    # Evita que caracteres como ';', '&&' o '|' inyectados ejecuten código arbitrario
    cmd = ["uv", "run", "cortex-purge", "--db", str(db_path), "--taint", sanitized_taint]
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            env={**os.environ, "CORTEX_ISOLATION": "1"} # Mantener aislamiento per-tenant
        )
        return "PURGE_SUCCESS" in result.stdout
    except subprocess.CalledProcessError as e:
        raise BFTCausalInvariantError(f"Fallo crítico en la purga: {e.stderr}")

if __name__ == "__main__":
    main()
