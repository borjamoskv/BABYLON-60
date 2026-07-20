import os
import json
import re
import signal
import logging
import hashlib
from typing import TypedDict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class IPCReport(TypedDict):
    network_endpoints: list[dict[str, str]]
    ffi_bindings: list[dict[str, str]]
    database_locks: list[dict[str, str]]
    multiprocessing_ipc: list[dict[str, str]]


def sha3_256_payload(payload: str) -> str:
    h = hashlib.sha3_256()
    h.update(payload.encode("utf-8"))
    return h.hexdigest()


def analyze_ipc_and_runtime(target_dir: str) -> None:
    if not os.path.exists(target_dir):
        logging.error(f"Ruta objetivo inalcanzable: {target_dir}")
        os.kill(os.getpid(), signal.SIGKILL)

    report: IPCReport = {
        "network_endpoints": [],
        "ffi_bindings": [],
        "database_locks": [],
        "multiprocessing_ipc": [],
    }

    # Invariante Ω18/Ω39: Pruning estricto para evitar ahogamiento IO en os.walk
    exclude_dirs = {
        ".venv",
        "node_modules",
        "__pycache__",
        ".git",
        "target",
        "out",
        "dist",
        "bin",
        "obj",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }

    for root, dirs, files in os.walk(target_dir):
        # Modificar dirs in-place fuerza a os.walk a ignorar la topología muerta
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, target_dir)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()

                if (
                    "FastAPI" in source
                    or "APIRouter" in source
                    or "@app." in source
                    or "@router." in source
                ):
                    report["network_endpoints"].append(
                        {"file": rel_path, "type": "FastAPI Router"}
                    )
                if (
                    "urllib.request" in source
                    or "requests." in source
                    or "httpx." in source
                ):
                    report["network_endpoints"].append(
                        {"file": rel_path, "type": "HTTP Client"}
                    )
                if "socket." in source:
                    report["network_endpoints"].append(
                        {"file": rel_path, "type": "Raw Socket"}
                    )

                if "ctypes" in source or "cffi" in source:
                    report["ffi_bindings"].append({"file": rel_path, "type": "C-FFI"})
                if re.search(r"import\s+(strike_rs|moskv_core)", source):
                    report["ffi_bindings"].append(
                        {"file": rel_path, "type": "Rust PyO3"}
                    )

                if "busy_timeout" in source or "WAL" in source.upper():
                    report["database_locks"].append(
                        {"file": rel_path, "type": "SQLite WAL/Timeout"}
                    )

                if (
                    "asyncio.Queue" in source
                    or "multiprocessing" in source
                    or "threading" in source
                ):
                    report["multiprocessing_ipc"].append(
                        {"file": rel_path, "type": "Concurrency primitive"}
                    )

            except (OSError, ValueError, TypeError, UnicodeDecodeError) as e:
                # Invariante Ω26: Fail-Fast. Cero pass mudo. Purga Inmediata.
                logging.error(
                    f"Error estructural parseando {rel_path}: {e}. Ejecutando purga SIGKILL."
                )
                os.kill(os.getpid(), signal.SIGKILL)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_json = os.path.join(
        project_root, "cortex", "artifacts", "reports", "BABYLON_60_RUNTIME_IPC.json"
    )
    os.makedirs(os.path.dirname(out_json), exist_ok=True)

    payload_str = json.dumps(report, indent=2)
    payload_hash = sha3_256_payload(payload_str)

    # Invariante Ω15: Idempotency Lock
    if os.path.exists(out_json):
        with open(out_json, "r", encoding="utf-8") as f:
            if f.read() == payload_str:
                logging.info(
                    f"Idempotency Lock (Ω15): Estado previo idéntico [{payload_hash[:8]}]. Ahorro de ATP."
                )
                return

    with open(out_json, "w", encoding="utf-8") as f:
        f.write(payload_str)

    # Invariante Ω11: Firma CORTEX-TAINT obligatoria
    logging.info(
        f"CORTEX-TAINT:borjamoskv:ipc_analysis:completed_on:{os.path.basename(out_json)}:{payload_hash}"
    )


if __name__ == "__main__":
    # Invariante Ω23: Cero rutas absolutas quemadas. Fallback a CWD.
    target = os.environ.get("CORTEX_TARGET_DIR", os.path.abspath("."))
    analyze_ipc_and_runtime(target)
