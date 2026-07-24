# [C5-REAL] Exergy-Maximized
"""
Autonomous Training Daemon (Sleep Cycle).
Tracks daily session trajectories, triggers Test-Time Training (TTT),
verifies output LoRA adapters, and registers them.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any

from babylon60.extensions.training.ttt_engine import TTTEngine
from babylon60.extensions.training.verifier import AdapterVerifier

logger = logging.getLogger("babylon60_extensions.training.daemon")


class AutonomousTrainingDaemon:
    """
    Nocturnal training daemon. Runs in the background, consolidation phase.
    """

    def __init__(
        self,
        episodic_memory: Any,
        interval_seconds: int = 3600,
        base_model: str | None = None,
    ) -> None:
        self.episodic_memory = episodic_memory
        self.interval_seconds = interval_seconds
        self.verifier = AdapterVerifier()
        self.ttt_engine = TTTEngine(episodic_memory)

        self.base_model = base_model or self.ttt_engine.base_model

        self.training_dir = Path.home() / ".babylon60" / "training"
        self.training_dir.mkdir(parents=True, exist_ok=True)

        self.consolidated_sessions_file = self.training_dir / "consolidated_sessions.json"
        self.verified_adapter_file = self.training_dir / "verified_adapter.json"
        self.adapter_history_file = self.training_dir / "adapter_history.json"
        self.archive_dir = self.training_dir / "adapters" / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.is_running = False
        self._task: asyncio.Task | None = None

    async def get_all_session_ids(self) -> list[str]:
        """Queries episodic memory for all distinct session IDs."""
        try:
            if hasattr(self.episodic_memory, "_conn"):
                conn = self.episodic_memory._conn
                is_async = False
                import inspect
                from unittest.mock import AsyncMock, MagicMock

                import aiosqlite

                if isinstance(conn, aiosqlite.Connection):
                    is_async = True
                elif hasattr(conn, "execute") and hasattr(conn.execute, "return_value"):
                    retval = conn.execute.return_value
                    if hasattr(retval, "__aenter__") and (
                        inspect.iscoroutinefunction(retval.__aenter__)
                        or isinstance(retval.__aenter__, (AsyncMock, MagicMock))
                    ):
                        is_async = True

                if is_async:
                    async with conn.execute("SELECT DISTINCT session_id FROM episodes") as cursor:
                        if inspect.iscoroutinefunction(cursor.fetchall) or isinstance(
                            cursor.fetchall, AsyncMock
                        ):
                            rows = await cursor.fetchall()
                        else:
                            rows = cursor.fetchall()
                        return [row[0] for row in rows if row[0]]
                else:

                    def _query():
                        cursor = conn.execute("SELECT DISTINCT session_id FROM episodes")
                        return [row[0] for row in cursor.fetchall() if row[0]]

                    return await asyncio.to_thread(_query)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to query distinct session IDs: %s", e)
        return []

    def load_consolidated_sessions(self) -> set[str]:
        """Loads session IDs that have already been consolidated."""
        if not self.consolidated_sessions_file.exists():
            return set()
        try:
            with open(self.consolidated_sessions_file, encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to load consolidated sessions: %s", e)
            return set()

    def save_consolidated_sessions(self, sessions: set[str]) -> None:
        """Saves consolidated session IDs."""
        try:
            with open(self.consolidated_sessions_file, "w", encoding="utf-8") as f:
                json.dump(list(sessions), f, indent=2)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to save consolidated sessions: %s", e)

    def register_verified_adapter(self, adapter_path: Path, metrics: dict[str, Any]) -> None:
        """Registers the verified adapter and archives it for rollback lineage."""
        try:
            history = []
            if self.adapter_history_file.exists():
                try:
                    with open(self.adapter_history_file, encoding="utf-8") as f:
                        history = json.load(f)
                except Exception as e:  # noqa: BLE001
                    logger.error("Failed to read adapter history: %s", e)

            next_version = len(history) + 1
            archive_subdir = self.archive_dir / f"adapters_v{next_version}"
            archive_subdir.mkdir(parents=True, exist_ok=True)

            active_weights_safetensors = adapter_path / "adapters.safetensors"
            active_weights_npz = adapter_path / "weights.npz"
            active_config = adapter_path / "adapter_config.json"

            if active_weights_safetensors.exists():
                shutil.copy2(active_weights_safetensors, archive_subdir / "adapters.safetensors")
            elif active_weights_npz.exists():
                shutil.copy2(active_weights_npz, archive_subdir / "weights.npz")
            if active_config.exists():
                shutil.copy2(active_config, archive_subdir / "adapter_config.json")

            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            entry = {
                "version": next_version,
                "archive_path": str(archive_subdir.resolve()),
                "compiled_at": timestamp,
                "base_model": self.base_model,
                "performance_metrics": metrics,
                "status": "verified",
            }
            history.append(entry)

            with open(self.adapter_history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

            registry_data = {
                "active_version": next_version,
                "adapter_path": str(adapter_path.resolve()),
                "base_model": self.base_model,
                "compiled_at": timestamp,
                "performance_metrics": metrics,
                "status": "verified",
            }
            with open(self.verified_adapter_file, "w", encoding="utf-8") as f:
                json.dump(registry_data, f, indent=2)

            logger.info(
                "🎉 Archived and registered verified adapter version v%d at %s",
                next_version,
                adapter_path,
            )
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to register and archive verified adapter: %s", e)

    async def run_cycle(self) -> dict[str, Any]:
        """
        Executes a single cycle of the training daemon.
        1. Compile the static knowledge dataset (workflows, vault, directivas).
        2. Fetch all session IDs.
        3. Identify unconsolidated sessions.
        4. Trigger TTTEngine nocturnal consolidation (merges dynamic + static).
        5. Verify output adapter structure and safety.
        6. Register & archive verified adapter.
        """
        logger.info("🌙 Running autonomous training cycle...")

        try:
            from babylon60.extensions.training.moskv1_dataset_compiler import MOSKV1DatasetCompiler

            workspace_path = Path(__file__).resolve().parents[3]
            logger.info("🔧 Pre-compiling static dataset from workspace: %s", workspace_path)

            compiler = MOSKV1DatasetCompiler(workspace_path, min_exergy=0.45)
            compiler.compile_full_dataset()
            logger.info("✅ Pre-compilation complete.")
        except Exception as ce:  # noqa: BLE001
            logger.error(
                "Failed pre-compiling static dataset: %s. Continuing with existing files.", ce
            )

        all_sessions = await self.get_all_session_ids()
        consolidated = self.load_consolidated_sessions()

        unconsolidated = [sid for sid in all_sessions if sid not in consolidated]

        if not unconsolidated:
            logger.info("💤 No new sessions to consolidate.")
            return {"status": "idle", "processed_sessions": 0}

        logger.info("🧪 Found %d new sessions for consolidation.", len(unconsolidated))

        try:
            result = await self.ttt_engine.run_nocturnal_consolidation(unconsolidated)

            if result.get("status") == "success":
                adapter_path = self.ttt_engine.adapter_path
                verify_res = self.verifier.verify_adapter(adapter_path, self.base_model)

                if verify_res.get("success"):
                    metrics = {
                        "average_reward": result.get("average_reward", 0.0),
                        "golden_trajectories": result.get("golden_trajectories", 0),
                        "verifier_metrics": verify_res.get("metrics", {}),
                    }
                    self.register_verified_adapter(adapter_path, metrics)

                    new_consolidated = consolidated.union(unconsolidated)
                    self.save_consolidated_sessions(new_consolidated)

                    return {
                        "status": "success",
                        "processed_sessions": len(unconsolidated),
                        "adapter": str(adapter_path),
                        "metrics": metrics,
                    }
                logger.error("❌ Adapter verification failed: %s", verify_res.get("error"))
                return {
                    "status": "verification_failed",
                    "error": verify_res.get("error"),
                    "processed_sessions": 0,
                }
            if result.get("status") == "skipped":
                new_consolidated = consolidated.union(unconsolidated)
                self.save_consolidated_sessions(new_consolidated)
                logger.info("⏭️ Consolidation skipped: %s", result.get("reason"))
                return {
                    "status": "skipped",
                    "reason": result.get("reason"),
                    "processed_sessions": len(unconsolidated),
                }
            logger.error("❌ Consolidation pipeline failed: %s", result.get("error"))
            return {
                "status": "failed",
                "error": result.get("error"),
                "processed_sessions": 0,
            }

        except Exception as e:  # noqa: BLE001
            logger.error("Exception during training cycle: %s", e)
            return {"status": "error", "error": str(e), "processed_sessions": 0}

    async def start(self) -> None:
        """Starts the background loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("🚀 Autonomous Training Daemon started.")

    async def stop(self) -> None:
        """Stops the background loop."""
        if not self.is_running:
            return
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as exc:  # noqa: BLE001
                logger.warning("Suppressed exception: %s", exc)
        logger.info("🛑 Autonomous Training Daemon stopped.")

    async def _loop(self) -> None:
        """Main loop that calls run_cycle periodically."""
        while self.is_running:
            try:
                await self.run_cycle()
            except Exception as e:  # noqa: BLE001
                logger.error("Error in daemon loop: %s", e)
            await asyncio.sleep(self.interval_seconds)
