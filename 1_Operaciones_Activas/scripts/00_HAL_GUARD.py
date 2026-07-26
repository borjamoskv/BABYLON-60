# C5-REAL EXERGY CERTIFIED
import sys
import re
import asyncio
import sqlite3
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Callable, Awaitable
import nacl.signing

# Carga dinámica para evitar el error de sintaxis por prefijo numérico en el nombre del módulo
spec_bft = importlib.util.spec_from_file_location("52_OR_BFT_NODE", str(Path(__file__).parent / "52_OR_BFT_NODE.py"))
or_bft_node = importlib.util.module_from_spec(spec_bft)
spec_bft.loader.exec_module(or_bft_node)
HeterogeneousBFTCoordinator = or_bft_node.HeterogeneousBFTCoordinator

RE_CLOSE = re.compile(r"\b(he finalizado|completado|tarea terminada|concluido|done|successfully executed)\b", re.IGNORECASE)

class ViewChangeException(Exception):
    """Detona la destitución y el relevo de mando inmediato del líder corrupto."""
    pass

class HalGuard:
    __slots__ = ("node_id", "sk", "db_path", "repo_path", "checkers", "scores", "lock", "coordinator")

    def __init__(self, node_id: str, sk: nacl.signing.SigningKey, db_path: Path, openrouter_key: str):
        self.node_id: str = node_id
        self.sk: nacl.signing.SigningKey = sk
        self.db_path: Path = db_path
        self.repo_path: Path = db_path.parent
        self.lock = asyncio.Lock()

        self.checkers: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self.scores: Dict[str, float] = {}

        # Inicialización del oráculo asimétrico trinitario de bajo nivel (L4)
        self.coordinator = HeterogeneousBFTCoordinator(openrouter_key)
        self._bootstrap_l2()

    def _bootstrap_l2(self):
        with sqlite3.connect(self.db_path, timeout=5.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fraud_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT, offender TEXT, reporter TEXT, sig TEXT, ts TEXT
                );
            """)
            conn.execute("CREATE TRIGGER IF NOT EXISTS NoUp BEFORE UPDATE ON fraud_ledger BEGIN SELECT RAISE(FAIL, 'BFT_ERR'); END;")
            conn.execute("CREATE TRIGGER IF NOT EXISTS NoDel BEFORE DELETE ON fraud_ledger BEGIN SELECT RAISE(FAIL, 'BFT_ERR'); END;")

    async def audit(self, task_id: str, offender_id: str, text: str, view: int) -> bool:
        """Filtro de contención perimetral absoluta. Aplica la One-Strike Rule ante fallos físicos o lógicos."""
        if not RE_CLOSE.search(text):
            return True # Flujo libre de reclamos de finalización

        async with self.lock:
            checker = self.checkers.get(task_id)

            # 1. Auditoría de primer factor: Estado real de la infraestructura local
            local_effect_verified = False
            if checker:
                local_effect_verified = await checker()

            # 2. Auditoría de segundo factor: Consenso anti-monocultivo lógico L4
            # Se pasa la descripción de la tarea y la declaración del emisor al oráculo TCP puro
            quorum_approved = await self.coordinator.audit_task_completion(
                task_description=task_id,
                agent_evidence=text
            )

            # Si el entorno físico local no cambió O el quórum determinó alucinación -> COLAPSO BIZANTINO
            if not local_effect_verified or not quorum_approved:
                # Aplicación instantánea de la One-Strike Rule: muerte civil del nodo en la caché
                self.scores[offender_id] = 0.0

                # Firma digital asimétrica del sobre forense con Ed25519 nativo
                raw_data = f"FRAUD|{task_id}|{offender_id}|{self.node_id}|{view}".encode('utf-8')
                sig_hex = self.sk.sign(raw_data).signature.hex()

                sys.stderr.write(f"\n[💥 SHIELD L3] VIOLACIÓN DETECTADA DESDE {offender_id} -> Firma: {sig_hex[:16]}...\n")

                # Persistencia atómica local L2 en el histórico protegido por triggers
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    conn.execute(
                        "INSERT INTO fraud_ledger (task_id, offender, reporter, sig, ts) VALUES (?, ?, ?, ?, ?)",
                        (task_id, offender_id, self.node_id, sig_hex, datetime.now(timezone.utc).isoformat())
                    )

                # Despliegue de barrera de no-repudio local inercial en Git Sentinel L3
                asyncio.create_task(self._git_freeze(task_id, offender_id, sig_hex))

                # Inyección reactiva y disparo del anclaje inerte universal en Capa L5 (OpenTimestamps)
                try:
                    spec_l5 = importlib.util.spec_from_file_location("01_L5_ANCHOR", str(Path(__file__).parent / "01_L5_ANCHOR.py"))
                    l5_mod = importlib.util.module_from_spec(spec_l5)
                    spec_l5.loader.exec_module(l5_mod)
                    L5AnchorEngine = l5_mod.L5AnchorEngine

                    l5_engine = L5AnchorEngine(self.repo_path / "cortex_inertial_proofs", self.db_path)
                    l5_engine.autonomous_sqlite_sweep()
                except Exception as e:
                    sys.stderr.write(f"[⚠️ L5 BYPASS] Fallo en la cascada de anclaje externo OpenTimestamps: {e}\n")

                # Purga atómica inmediata del líder. Aborto completo de la época.
                print(f"[🛡️ VIEW CHANGE] Reputación de {offender_id} destruida por el quórum. Forzando transición de época BFT.")
                raise ViewChangeException(f"Líder {offender_id} purgado de la malla por alucinación confirmada.")

            return True

    async def _git_freeze(self, task_id: str, offender_id: str, sig_hex: str):
        msg = f"HAL_SHIELD [Ω9] | Task: {task_id} | Culprit: {offender_id} | Proof: {sig_hex[:16]}"
        p1 = await asyncio.create_subprocess_exec("git", "-C", str(self.repo_path), "add", ".", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await p1.wait()
        p2 = await asyncio.create_subprocess_exec("git", "-C", str(self.repo_path), "commit", "--allow-empty", "-m", msg, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await p2.wait()
