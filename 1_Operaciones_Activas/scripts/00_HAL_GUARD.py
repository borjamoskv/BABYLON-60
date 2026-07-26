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

# Inyectamos dependencias L5 dinámicamente si es posible
sys.path.append(str(Path(__file__).parent))
try:
    import 01_L5_ANCHOR as l5_anchor
except SyntaxError:
    spec_l5 = importlib.util.spec_from_file_location("01_L5_ANCHOR", str(Path(__file__).parent / "01_L5_ANCHOR.py"))
    l5_anchor = importlib.util.module_from_spec(spec_l5)
    spec_l5.loader.exec_module(l5_anchor)

RE_CLOSE = re.compile(r"\b(he finalizado|completado|tarea terminada|concluido|done|successfully executed)\b", re.IGNORECASE)

class ViewChangeException(Exception):
    pass

class HalGuard:
    __slots__ = ("node_id", "sk", "db_path", "repo_path", "checkers", "scores", "lock", "l5_engine")

    def __init__(self, node_id: str, sk: nacl.signing.SigningKey, db_path: Path):
        self.node_id = node_id
        self.sk = sk
        self.db_path = db_path
        self.repo_path = db_path.parent
        self.lock = asyncio.Lock()

        self.checkers: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self.scores: Dict[str, float] = {}

        # Instanciación nativa del motor de anclaje inerte L5
        self.l5_engine = l5_anchor.L5AnchorEngine(self.repo_path / "cortex_inertial_proofs", self.db_path)
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
        if not RE_CLOSE.search(text):
            return True

        async with self.lock:
            checker = self.checkers.get(task_id)
            if not checker or await checker():
                return True

            self.scores[offender_id] = 0.0

            raw_data = f"FRAUD|{task_id}|{offender_id}|{self.node_id}|{view}".encode('utf-8')
            sig_hex = self.sk.sign(raw_data).signature.hex()

            sys.stderr.write(f"\n[💥 SHIELD L3] FRAUDE DETECTADO DESDE {offender_id} -> Sello: {sig_hex[:16]}...\n")

            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                conn.execute(
                    "INSERT INTO fraud_ledger (task_id, offender, reporter, sig, ts) VALUES (?, ?, ?, ?, ?)",
                    (task_id, offender_id, self.node_id, sig_hex, datetime.now(timezone.utc).isoformat())
                )

            asyncio.create_task(self._git_freeze(task_id, offender_id, sig_hex))

            if self.scores[offender_id] <= 0.0:
                print(f"[🛡️ VIEW CHANGE] Reputación de {offender_id} destrozada. Colapsando época BFT.")

                # INTEGRACIÓN: Disparador automático del anclaje L5 (Sweep Append-Only)
                self.l5_engine.autonomous_sqlite_sweep()

                raise ViewChangeException(f"Líder {offender_id} purgado de la malla de consenso por fraude de cierre.")

            return False

    async def _git_freeze(self, task_id: str, offender_id: str, sig_hex: str):
        msg = f"HAL_SHIELD [Ω9] | Task: {task_id} | Culprit: {offender_id} | Proof: {sig_hex[:16]}"
        p1 = await asyncio.create_subprocess_exec("git", "-C", str(self.repo_path), "add", ".", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await p1.wait()
        p2 = await asyncio.create_subprocess_exec("git", "-C", str(self.repo_path), "commit", "--allow-empty", "-m", msg, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await p2.wait()
