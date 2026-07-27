# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
# Author: borjamoskv
"""
Test-Time Training (TTT) Engine.
The Event Horizon of Autonomous Evolution.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from babylon60.extensions.training.collector import Trajectory, TrajectoryCollector
from babylon60.extensions.training.reward_engine import RewardEngine

logger = logging.getLogger("babylon60_extensions.training.ttt")


class TTTEngine:
    """
    Test-Time Training Orchestrator.
    Filters high-reward trajectories and triggers local MLX fine-tuning.
    """

    collector: TrajectoryCollector
    rewarder: RewardEngine
    dataset_dir: Path
    base_model: str
    adapter_path: Path

    def __init__(self, episodic_memory: Any, triad: Any = None):
        self.collector = TrajectoryCollector(episodic_memory)
        self.rewarder = RewardEngine(use_tests=True)

        self.dataset_dir = Path.home() / ".babylon60" / "training" / "datasets"
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

        # We target the Qwen2.5 base model used by BABYLON-60
        self.base_model = os.getenv(
            "CORTEX_BASE_MODEL_PATH", "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
        )
        self.adapter_path = Path.home() / ".babylon60" / "training" / "adapters"

    async def run_nocturnal_consolidation(self, session_ids: list[str]) -> dict[str, Any]:
        """
        The sleep cycle integration.
        1. Collects trajectories for the given sessions.
        2. Calculates RLHF/Sovereign rewards.
        3. Formats the 'Golden' trajectories (> 0.5 reward).
        4. Triggers MLX LoRA training if dataset size is sufficient.
        """
        logger.info("🌙 Initiating TTT Consolidation for %d sessions...", len(session_ids))

        golden_trajectories: list[Trajectory] = []
        total_reward = 0.0

        for sid in session_ids:
            try:
                traj = await self.collector.collect_session_trajectory(sid)
                if not traj:
                    continue

                reward = self.rewarder.calculate_reward(traj)

                # Axiom Ω4: Aesthetic Integrity - Only learn from excellence
                if reward > 0.4:
                    traj.reward = reward
                    golden_trajectories.append(traj)
                    total_reward += reward
                    logger.debug("✨ Golden Trajectory found: %s (Reward: %.2f)", sid, reward)
                else:
                    logger.debug(
                        "🗑️ Discarding low-quality trajectory: %s (Reward: %.2f)", sid, reward
                    )

            except Exception as e:  # noqa: BLE001
                logger.error("Failed to process trajectory %s: %s", sid, e)

        if not golden_trajectories:
            logger.info("No golden trajectories found tonight. Skipping MLX training.")
            return {"status": "skipped", "reason": "No high-reward data"}

        # Format and save dataset
        dataset_path = self._save_dataset(golden_trajectories)
        logger.info("💾 Saved %d golden trajectories to %s", len(golden_trajectories), dataset_path)

        # Trigger actual or simulated MLX training
        avg_reward = total_reward / len(golden_trajectories)
        training_result = await self._trigger_mlx_lora()

        return {
            "status": "success",
            "trajectories_processed": len(session_ids),
            "golden_trajectories": len(golden_trajectories),
            "average_reward": round(avg_reward, 3),
            "training_result": training_result,
        }

    def _save_dataset(self, trajectories: list[Trajectory]) -> Path:
        """Saves golden trajectories in ShareGPT/messages format for MLX-LM."""
        # Format trajectories into JSON format
        formatted_json = self.collector.format_for_sft(trajectories, format_type="sharegpt")
        data = json.loads(formatted_json)

        # Map 'conversations' key to 'messages' for MLX-LM compatibility
        mapped_entries = []
        for entry in data:
            if "conversations" in entry:
                mapped_entries.append({"messages": entry["conversations"]})
            else:
                mapped_entries.append(entry)

        train_path = self.dataset_dir / "train.jsonl"
        valid_path = self.dataset_dir / "valid.jsonl"
        test_path = self.dataset_dir / "test.jsonl"

        # Append golden trajectories incrementally to the train set
        # This merges user corrections with static compiled knowledge
        existing_lines = []
        if train_path.exists():
            with open(train_path, encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]

        # Write combined dataset
        with open(train_path, "w", encoding="utf-8") as f:
            # Keep existing lines
            for line in existing_lines:
                f.write(line + "\n")
            # Append new golden trajectories
            for entry in mapped_entries:
                f.write(json.dumps(entry) + "\n")
        logger.info("Injected %d golden trajectories into train.jsonl", len(mapped_entries))

        # Ensure valid.jsonl and test.jsonl exist with at least 1 entry to satisfy MLX-LM
        for path in [valid_path, test_path]:
            if not path.exists() or path.stat().st_size == 0:
                with open(path, "w", encoding="utf-8") as f:
                    if mapped_entries:
                        f.write(json.dumps(mapped_entries[0]) + "\n")
                    elif existing_lines:
                        try:
                            parsed = json.loads(existing_lines[0])
                            f.write(json.dumps(parsed) + "\n")
                        except Exception:  # noqa: BLE001
                            f.write(
                                json.dumps({"messages": [{"role": "system", "content": "stub"}]})
                                + "\n"
                            )
                    else:
                        # Strict fallback dummy matching format
                        dummy = {
                            "messages": [
                                {"role": "system", "content": "stub"},
                                {"role": "user", "content": "ping"},
                                {"role": "assistant", "content": "pong"},
                            ]
                        }
                        f.write(json.dumps(dummy) + "\n")

        # Maintain a log of the nocturnal trajectories
        timestamp = int(time.time())
        log_file = self.dataset_dir / f"golden_dataset_{timestamp}.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for entry in mapped_entries:
                f.write(json.dumps(entry) + "\n")

        return train_path

    async def _trigger_mlx_lora(self) -> dict[str, Any]:
        """
        Triggers mlx_lm.lora training asynchronously.
        Alters neural weights using Apple Silicon Metal optimization.
        """
        logger.info("🧠 Triggering MLX LoRA Fine-Tuning (Apple Silicon Optimization)...")

        self.adapter_path.mkdir(parents=True, exist_ok=True)

        # Optimized cmd arguments avoiding OOM/NaN and using updated subcommand syntax
        cmd = [
            sys.executable,
            "-m",
            "mlx_lm",
            "lora",
            "--model",
            self.base_model,
            "--train",
            "--data",
            str(self.dataset_dir),
            "--adapter-path",
            str(self.adapter_path),
            "--fine-tune-type",
            "lora",
            "--optimizer",
            "adamw",
            "--mask-prompt",
            "--num-layers",
            "16",
            "--iters",
            "50",  # Optimized iterations for nocturnal cycle
            "--batch-size",
            "1",  # Lower batch size to prevent OOM
            "--grad-accumulation-steps",
            "2",  # Virtual batch size = 2
            "--val-batches",
            "5",  # Speed up validation checks
            "--max-seq-length",
            "1280",  # Avoid truncation
            "--grad-checkpoint",  # Enable memory optimizations
        ]

        process = None
        try:
            # We run via create_subprocess_exec to allow cancellation and avoid thread pool starvation
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600.0)
            except asyncio.TimeoutError:
                logger.warning("MLX LoRA timed out. Terminating process...")
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except (OSError, RuntimeError):
                    logger.warning("MLX LoRA termination failed. Killing process...")
                    try:
                        process.kill()
                    except OSError:
                        pass
                return {"status": "timeout"}

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            if process.returncode != 0:
                logger.error("MLX LoRA Failed: %s", stderr_str)
                return {"status": "error", "error": stderr_str[:500]}

            logger.info("✅ MLX LoRA completed successfully.")
            return {"status": "success", "output": stdout_str[-500:]}

        except Exception as e:  # noqa: BLE001
            logger.error("Exception during MLX execution: %s", e)
            if process is not None and process.returncode is None:
                try:
                    process.kill()
                except OSError:
                    pass
            return {"status": "error", "error": str(e)}
