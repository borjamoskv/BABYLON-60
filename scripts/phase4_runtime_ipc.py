import os
import json
import re
import sys
import logging
from typing import TypedDict, List, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class IPCReport(TypedDict):
    network_endpoints: List[Dict[str, str]]
    ffi_bindings: List[Dict[str, str]]
    database_locks: List[Dict[str, str]]
    multiprocessing_ipc: List[Dict[str, str]]


def analyze_ipc_and_runtime(target_dir: str) -> None:
    if not os.path.exists(target_dir):
        raise OSError(f"Ruta objetivo inalcanzable: {target_dir}")

    report: IPCReport = {
        "network_endpoints": [],
        "ffi_bindings": [],
        "database_locks": [],
        "multiprocessing_ipc": [],
    }

    for root, dirs, files in os.walk(target_dir):
        if any(x in root for x in [".venv", "node_modules", "__pycache__", ".git", "target"]):
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, target_dir)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()

                    if "FastAPI" in source or "APIRouter" in source or "@app." in source or "@router." in source:
                        report["network_endpoints"].append({"file": rel_path, "type": "FastAPI Router"})
                    if "urllib.request" in source or "requests." in source or "httpx." in source:
                        report["network_endpoints"].append({"file": rel_path, "type": "HTTP Client"})
                    if "socket." in source:
                        report["network_endpoints"].append({"file": rel_path, "type": "Raw Socket"})

                    if "ctypes" in source or "cffi" in source:
                        report["ffi_bindings"].append({"file": rel_path, "type": "C-FFI"})
                    if re.search(r"import\s+(strike_rs|moskv_core)", source):
                        report["ffi_bindings"].append({"file": rel_path, "type": "Rust PyO3"})

                    if "busy_timeout" in source or "WAL" in source.upper():
                        report["database_locks"].append({"file": rel_path, "type": "SQLite WAL/Timeout"})

                    if "asyncio.Queue" in source or "multiprocessing" in source or "threading" in source:
                        report["multiprocessing_ipc"].append({"file": rel_path, "type": "Concurrency primitive"})

                except (OSError, ValueError, TypeError) as e:
                    # Invariante Ω26: Fail-Fast o Log Explícito, cero pass mudo.
                    logging.warning(f"Error IO/Tipado parseando {rel_path}: {e}")
                except SyntaxError as e:
                    logging.warning(f"Error de sintaxis parseando {rel_path}: {e}")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_json = os.path.join(project_root, "cortex", "artifacts", "reports", "BABYLON_60_RUNTIME_IPC.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Invariante Ω11/R4: Firma CORTEX-TAINT
    logging.info(f"CORTEX-TAINT:borjamoskv:ipc_analysis:completed_on:{os.path.basename(out_json)}")


if __name__ == "__main__":
    # Invariante Ω23: Cero rutas absolutas quemadas. Fallback a CWD.
    target = os.environ.get("CORTEX_TARGET_DIR", os.path.abspath("."))
    analyze_ipc_and_runtime(target)
