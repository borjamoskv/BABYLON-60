import datetime
import hashlib
import json
import os
import shutil
from typing import Any

import yaml

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
ARCHIVE_ROOT = os.path.join(PROJECT_ROOT, ".cortex", "archive")
ARCHIVE_SCRIPTS = os.path.join(ARCHIVE_ROOT, "scripts")
ARCHIVE_DATA = os.path.join(ARCHIVE_ROOT, "data")
ARCHIVE_DBS = os.path.join(ARCHIVE_ROOT, "dbs")
AUDIT_YAML = os.path.join(PROJECT_ROOT, "cortex", "audits", "anergy_purge_audit.yaml")
PROTECTED_FILES = {
    ".coderabbit.yaml",
    ".gitattributes",
    ".gitignore",
    ".gitmodules",
    "AGENTS.md",
    "Anergy_Audit.yml",
    "COLLAPSE_P0.sh",
    "Dockerfile",
    "ETHOS.md",
    "LEARN_SHIP_ITERATE_INVARIANT.md",
    "LICENSE.md",
    "LLM_THERMODYNAMICS_LAYERS.md",
    "LLM_THERMODYNAMICS_LAYERS_5_8.md",
    "MANIFIESTO_CENTURIA.md",
    "MOSKV_1_APEX_BLUEPRINT.md",
    "Makefile",
    "PROJECT.md",
    "README.md",
    "README_APEX.md",
    "SECURITY.md",
    "STATUS.md",
    "TEXTBOOK_EXERGY_INVARIANT.md",
    "VECTOR_A_MASTER_LEDGER_DESIGN.md",
    "pyproject.toml",
    "uv.lock",
    "cortex_purge_anergy.py",
    "cortex_ssm_mamba_core.py",
    "cortex_mamba_block.py",
    "cortex_mamba_network.py",
    "cortex_mamba_inference.py",
    "cortex_bpe_tokenizer.py",
    "core_graph_ledger.py",
    "io_persist_ledger.py",
    "net_mamba_ledger_engine.py",
    "index.html",
}


def ensure_dirs() -> None:
    for d in [ARCHIVE_SCRIPTS, ARCHIVE_DATA, ARCHIVE_DBS]:
        os.makedirs(d, exist_ok=True)


def categorize_and_move() -> tuple[int, int, list[dict[str, Any]]]:
    moved_count: int = 0
    moved_bytes: int = 0
    actions: list[dict[str, Any]] = []
    for item in os.listdir(PROJECT_ROOT):
        item_path = os.path.join(PROJECT_ROOT, item)
        if os.path.isdir(item_path):
            continue
        if item in PROTECTED_FILES:
            continue
        target_dir = None
        if item.endswith(".py"):
            target_dir = ARCHIVE_SCRIPTS
        elif item.endswith(".db"):
            target_dir = ARCHIVE_DBS
        elif item.endswith((".json", ".jsonl", ".csv", ".npz", ".png", ".html", ".sarif")):
            target_dir = ARCHIVE_DATA
        elif item.endswith(".yaml") or item.endswith(".yml"):
            target_dir = ARCHIVE_DATA
        if target_dir:
            dest_path = os.path.join(target_dir, item)
            size = os.path.getsize(item_path)
            shutil.move(item_path, dest_path)
            moved_count += 1
            moved_bytes += size
            actions.append({"file": item, "destination": target_dir, "bytes": size})
    return (moved_count, moved_bytes, actions)


def main() -> None:
    print("[*] C5-REAL: Iniciando Anergy Token Purge (Root Directory Entropy Collapse)...")
    ensure_dirs()
    count, total_bytes, actions = categorize_and_move()
    payload = json.dumps(actions, sort_keys=True).encode("utf-8")
    cortex_taint = hashlib.sha3_256(payload).hexdigest()
    audit_report = {
        "Claim": "Root directory Anergy (loose scripts, DBs, and datasets) has been structurally purged and archived, restoring 00_WORKSPACE.md hierarchy invariant.",
        "Proof": {"Base": "sha3_256::cortex_taint", "Range": [count, count], "Confidence": "C5-REAL"},
        "Operator": "borjamoskv",
        "System_Level": "C5-REAL",
        "Anergy_Files_Purged": count,
        "Anergy_Bytes_Purged": total_bytes,
        "Cortex_Taint": cortex_taint,
        "Timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    os.makedirs(os.path.dirname(AUDIT_YAML), exist_ok=True)
    with open(AUDIT_YAML, "w", encoding="utf-8") as f:
        yaml.dump(audit_report, f, sort_keys=False, allow_unicode=True)
    print(f"[+] Purga completada. {count} ficheros movidos ({total_bytes} bytes).")
    print(f"[+] Cortex Taint Hash: {cortex_taint}")
    print(f"[+] Audit guardado en: {AUDIT_YAML}")


if __name__ == "__main__":
    main()
