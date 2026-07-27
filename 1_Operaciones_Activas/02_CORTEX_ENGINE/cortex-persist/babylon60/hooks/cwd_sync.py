# [C5-REAL] Exergy-Maximized
"""CORTEX v6+ - CWD Sync Hook.

Mantiene `active-context.json` sincronizado con el entorno activo
para evitar bloqueos de git sentinel pre-commit.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("babylon60.hooks.cwd_sync")


def sync_active_context(cortex_meta_dir: Path, target_repo_path: Path):
    """Sincroniza el active-context.json con el repo actual."""
    context_file = cortex_meta_dir / "active-context.json"

    # Extraemos el nombre del repositorio asumiendo que target_repo_path es la raíz
    # y mapeamos al namespace del operador si aplica, ej: borjamoskv/repo
    repo_name = target_repo_path.name
    context_val = f"borjamoskv/{repo_name}"

    current_val = None
    if context_file.exists():
        try:
            with open(context_file, encoding="utf-8") as f:
                data = json.load(f)
                current_val = data.get("active_repo")
        except Exception:  # noqa: BLE001
            pass

    if current_val != context_val:
        try:
            context_file.parent.mkdir(parents=True, exist_ok=True)
            with open(context_file, "w", encoding="utf-8") as f:
                json.dump({"active_repo": context_val}, f, indent=4)
            logger.info(f"[CWD-SYNC] Sincronizado active-context.json a {context_val}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"[CWD-SYNC] Fallo al escribir active-context.json: {e}")
