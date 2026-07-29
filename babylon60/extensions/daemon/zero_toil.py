# [C5-REAL] Exergy-Maximized
"""CORTEX v6+ - Zero-Toil Autonomous Assimilation Daemon.

Erradica la entropía operacional mediante:
1. Apoptosis celular reactiva en paths mutados.
2. Auto-Recall CWD (Sincronización de active-context).
3. Persistencia Asíncrona (Cierre semántico al colapsar task.md).
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path

from babylon60.cli.common import DEFAULT_DB

logger = logging.getLogger("babylon60.daemon.zero_toil")

BRAIN_DIR = Path(os.path.expanduser("~/.gemini/antigravity/brain"))
CORTEX_META_DIR = Path(os.path.expanduser("~/10_PROJECTS/cortex-meta"))

ENTROPIC_SINKS = {".pytest_cache", ".ruff_cache", "__pycache__"}


class ZeroToilDaemon:
    """The Autonomous Entropy Assimilator."""

    def __init__(self, repo_path: Path, db_path: str = DEFAULT_DB):
        self.repo_path = repo_path
        self.db_path = db_path
        self._last_processed_tasks = {}

    def trigger_apoptosis(self, target_dir: Path) -> int:
        """Elimina basura termodinámica en caliente."""
        if not target_dir.exists():
            return 0

        purged_bytes = 0
        for root, dirs, _files in os.walk(target_dir):
            for d in dirs:
                if d in ENTROPIC_SINKS:
                    path = Path(root) / d
                    try:
                        for dirpath, _, filenames in os.walk(path):
                            for filename in filenames:
                                purged_bytes += os.path.getsize(os.path.join(dirpath, filename))
                        shutil.rmtree(path)
                        logger.info(f"[ZERO-TOIL] Apoptosis executed on {path}")
                    except Exception as e:  # noqa: BLE001
                        logger.error(f"[ZERO-TOIL] Failed apoptosis on {path}: {e}")
        return purged_bytes

    async def execute_semantic_closer(self, conv_id: str, transcript_path: Path):
        """Asimila la sesión asíncronamente."""
        logger.info(f"[ZERO-TOIL] Invocando cierre asíncrono para {conv_id}")

        # Invocamos al CLI closer en background para automatizar el cierre
        # sin que el usuario tenga que hacerlo interactivamente.

        script_path = Path(os.path.expanduser("~/60_SCRIPTS/cortex_session_closer.py"))
        if script_path.exists():
            env = os.environ.copy()
            env["CORTEX_CONV_ID"] = conv_id
            env["CORTEX_NO_TAINT_ENFORCE"] = "1"
            try:
                proc = await asyncio.create_subprocess_exec(
                    "python3",
                    str(script_path),
                    f"Auto-closed by ZeroToil {conv_id[:8]}",
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0:
                    logger.info(f"[ZERO-TOIL] Sesión {conv_id} cristalizada exitosamente.")
                else:
                    logger.error(f"[ZERO-TOIL] Fallo en cristalización: {stderr.decode()}")
            except Exception as e:  # noqa: BLE001
                logger.error(f"[ZERO-TOIL] Excepción en cierre asíncrono: {e}")

    async def _check_task_collapse(self):
        """Revisa si algún task.md reciente ha pasado a [x]."""
        if not BRAIN_DIR.exists():
            return

        try:
            convs = [d for d in BRAIN_DIR.iterdir() if d.is_dir()]
            convs.sort(key=lambda d: d.stat().st_mtime, reverse=True)

            # Revisamos las 3 más recientes
            for conv_dir in convs[:3]:
                task_md = conv_dir / "task.md"
                if task_md.exists():
                    mtime = task_md.stat().st_mtime
                    last_mtime = self._last_processed_tasks.get(conv_dir.name, 0)
                    if mtime > last_mtime:
                        content = task_md.read_text(encoding="utf-8")

                        tasks_total = (
                            content.count("- [ ]") + content.count("- [/]") + content.count("- [x]")
                        )
                        tasks_done = content.count("- [x]")

                        if tasks_total > 0 and tasks_done == tasks_total:
                            # Tarea completada.
                            logger.info(
                                f"[ZERO-TOIL] Colapso de tarea detectado en {conv_dir.name}. {tasks_done}/{tasks_total} completadas."
                            )
                            self._last_processed_tasks[conv_dir.name] = mtime

                            transcript = (
                                conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
                            )
                            if transcript.exists():
                                asyncio.create_task(
                                    self.execute_semantic_closer(conv_dir.name, transcript)
                                )
        except Exception as e:  # noqa: BLE001
            logger.error(f"[ZERO-TOIL] Error al verificar task.md: {e}")

    async def loop(self):
        """Bucle principal asíncrono."""
        logger.info("[ZERO-TOIL] Iniciando loop de asimilación autónoma.")
        while True:
            await self._check_task_collapse()
            await asyncio.sleep(10)
