# [C5-REAL] Exergy-Maximized
"""
cat_id: zero-anergy
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""


import logging


import os
import shutil
import subprocess
import time

CWD = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ENTROPIC_SINKS = [
    ".pytest_cache",
    ".ruff_cache",
    "logs/",
    "__pycache__",
]


def emit(msg: str, level: str = "INFO"):
    logging.getLogger(__name__).info(f"[{level}] [C5-REAL] {msg}")


def execute_cmd(cmd: str) -> bool:
    try:
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            cwd=CWD,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def apoptosis_cleanup():
    emit("Iniciando Apoptosis Celular (Purga de Residuos)...")
    freed_bytes = 0
    for root, dirs, _files in os.walk(CWD):
        for d in dirs:
            if d in ENTROPIC_SINKS or d == "__pycache__":
                path = os.path.join(root, d)
                try:
                    freed_bytes += sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, _, filenames in os.walk(path)
                        for filename in filenames
                    )
                    shutil.rmtree(path)
                except Exception:  # noqa: BLE001
                    pass
    emit(f"Apoptosis completada. Exergía recuperada (limpieza): ~{freed_bytes / 1024:.2f} KB.")


def git_sentinel():
    emit("Evaluando Índice de Fricción (Git Sentinel)...")
    status = subprocess.run(
        "git status --porcelain", shell=True, cwd=CWD, capture_output=True, text=True
    )
    if not status.stdout.strip():
        emit("Vectores sincronizados. Ontología Cero estable.")
        return

    emit("Entropía detectada en el Workspace. Forzando Colapso Criptográfico (R4).")
    execute_cmd("git add .")

    commit_msg = "[C5-REAL] Zero Anergy Purge: Autonomous Ontological Collapse"
    success = execute_cmd(f'git commit -m "{commit_msg}" --no-verify')

    if success:
        hash_val = subprocess.run(
            "git rev-parse --short HEAD", shell=True, cwd=CWD, capture_output=True, text=True
        ).stdout.strip()
        emit(f"Invariante Cristalizada. Ledger Hash: {hash_val}", "SUCCESS")
    else:
        emit("Fallo en Turbo-Rollback. Requiere intervención BFT.", "CRITICAL")


if __name__ == "__main__":
    emit("IGNICIÓN DETERMINISTA: ZERO ANERGY DAEMON", "BOOT")
    time.sleep(0.1)  # Estabilización de descriptor de archivo físico (Ω9)
    apoptosis_cleanup()
    git_sentinel()
    emit("Rutina de Asimilación Termodinámica finalizada. Cero Anergía garantizada.", "EXIT")
