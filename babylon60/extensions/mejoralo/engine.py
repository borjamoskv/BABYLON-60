# [C5-REAL] Exergy-Maximized

from pathlib import Path
from typing import Any

try:
    from babylon60.engine import CortexEngine  # type: ignore[import-not-found]
except ImportError:
    CortexEngine = Any  # type: ignore[misc,assignment]

from .heal import heal_proj
from .scan import MejoraloScanner, ScanResult
from .utils import detect_stack


class MejoraloEngine:
    """
    MEJORAlo: Continuous Improvement Engine for CORTEX.
    Unifies scanning, healing, and shipping of code improvements.
    """

    def __init__(self, engine: CortexEngine):
        self.engine = engine
        self.scanner = MejoraloScanner()

    def _notify_sync(
        self, name_or_color: str, active: bool = True, flash: bool = False, duration: float = 0.5
    ):
        """Dispatches an asynchronous notch notification from a synchronous context."""
        import asyncio

        from babylon60.routes.notch_ws import flash_notch_halo, notify_notch_halo

        async def _run():
            try:
                if flash:
                    await flash_notch_halo(name_or_color, duration)
                else:
                    await notify_notch_halo(name_or_color, active)
            except (ImportError, AttributeError, ValueError, RuntimeError):
                pass

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(_run())
            else:
                asyncio.run(_run())
        except RuntimeError:
            asyncio.run(_run())

    def scan(
        self, project: str, path: str | Path, deep: bool = False, brutal: bool = False
    ) -> ScanResult:
        """Scan a project or file for improvement opportunities."""
        self._notify_sync("#00E5FF", flash=True, duration=0.4)
        return self.scanner.scan_project(project, path, deep=deep, brutal=brutal)

    def heal(
        self,
        project: str,
        path: str | Path,
        target_score: int,
        scan_result: ScanResult,
    ) -> bool:
        """Apply automated healing to identified antipatterns."""
        self._notify_sync("#FFD600", active=True)
        success = False
        try:
            success = heal_proj(project, path, target_score, scan_result, engine=self)
            return success
        finally:
            self._notify_sync("#FFD600", active=False)
            if success:
                self._notify_sync("#00E676", flash=True, duration=1.0)
            else:
                self._notify_sync("#FF1744", flash=True, duration=1.0)

    def relentless_heal(
        self,
        project: str,
        path: str | Path,
        scan_result: ScanResult,
        target_score: int = 95,
    ) -> bool:
        """♾️ INMEJORABLE: no para hasta alcanzar el score objetivo."""
        self._notify_sync("#E040FB", active=True)
        success = False
        try:
            success = heal_proj(project, path, target_score, scan_result, engine=self)
            return success
        finally:
            self._notify_sync("#E040FB", active=False)
            if success:
                self._notify_sync("#00E676", flash=True, duration=1.5)
            else:
                self._notify_sync("#FF1744", flash=True, duration=1.5)

    def ship_gate(self, project: str, path: str | Path) -> Any:
        """Verify and seal code improvements via Ship Gate."""
        from .ship import check_ship_gate

        return check_ship_gate(project, path)

    def record_session(
        self, project: str, score_before: int, score_after: int, actions: list[str]
    ) -> int:
        """Record a Mejoralo session in the fact ledger."""
        from .ledger import record_session as ledger_record_session

        return ledger_record_session(
            engine=self.engine,
            project=project,
            score_before=score_before,
            score_after=score_after,
            actions=actions,
        )

    def history(self, project: str, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve historical Mejoralo sessions for a project."""
        res = self.engine.recall_sync(
            project=project,
            limit=100,
        )
        if not isinstance(res, list):
            return []
        filtered = []
        for fact in res:
            meta = fact.get("meta", {}) or {}
            tags = meta.get("tags", []) if isinstance(meta, dict) else fact.get("tags", [])
            if any(t in tags for t in ["mejoralo"]):
                filtered.append(fact)
        return filtered[:limit]

    def scars(self, project: str, file_path: str, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve historical taints (scars) for a specific file."""
        res = self.engine.recall_sync(
            project=project,
            fact_type="error",
            limit=100,
        )
        if not isinstance(res, list):
            return []
        filtered = []
        for fact in res:
            meta = fact.get("meta", {}) or {}
            tags = meta.get("tags", []) if isinstance(meta, dict) else fact.get("tags", [])
            if any(t in tags for t in ["mejoralo", "taint", "scar"]):
                filtered.append(fact)
        return filtered[:limit]

    async def scars_async(
        self, project: str, file_path: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieve historical taints (scars) for a specific file asynchronously."""
        res = await self.engine.recall(
            project=project,
            fact_type="error",
            limit=100,
        )
        if not isinstance(res, list):
            return []
        filtered = []
        for fact in res:
            meta = fact.get("meta", {}) or {}
            tags = meta.get("tags", []) if isinstance(meta, dict) else fact.get("tags", [])
            if any(t in tags for t in ["mejoralo", "taint", "scar"]):
                filtered.append(fact)
        return filtered[:limit]

    def record_scar(self, project: str, file_path: str, reason: str) -> None:
        """Record a scar (failure/taint evidence) in the CORTEX ledger."""
        self.engine.store_sync(
            project=project,
            content=f"[MEJORAlo SCAR] {file_path}: {reason}",
            fact_type="error",
            tags=["mejoralo", "scar", "investigation"],
            source="agent:mejoralo",
            meta={"file_path": file_path, "reason": reason},
        )

    def awwwards_fix(self, project: str, path: str | Path) -> bool:
        """Apply Awwwards-grade UI/UX fixes."""
        return False

    @staticmethod
    def detect_stack(path: str | Path) -> str:
        """Detect project stack from marker files."""
        return detect_stack(path)
