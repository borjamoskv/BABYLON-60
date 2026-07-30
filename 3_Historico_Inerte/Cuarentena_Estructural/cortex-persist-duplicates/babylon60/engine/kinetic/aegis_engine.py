# [C5-REAL] Exergy-Maximized
"""
Autonomous Aegis Engine (P0 Security Shield).

Validates the physical presence of security guards (Git hooks, Gitleaks)
and actively injects them if missing to prevent context leakage or secrets compromise
by agents operating in new/isolated worktrees.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("babylon60.engine.kinetic.aegis")


class AegisEngine:
    """Kinetic Engine that enforces the physical security perimeter."""

    @staticmethod
    def ensure_aegis_active() -> None:
        """
        Synchronous check of the P0 perimeter.
        Invoked during CLI boot sequence to guarantee isolation.
        """
        git_dir = Path(".git")
        if not git_dir.exists() or not git_dir.is_dir():
            # Not in a git repository or at the root, Aegis cannot bind.
            return

        hook_path = git_dir / "hooks" / "pre-commit"
        if hook_path.exists():
            return  # Aegis is already active

        # Aegis is inactive. Forcing thermodynamic colapse.
        logger.warning("C5-REAL: Aegis Engine detected inactive perimeter. Injecting P0 hooks...")

        try:
            # Install pre-commit
            subprocess.run(["pre-commit", "install"], check=True, capture_output=True, text=True)
            # Install pre-push
            subprocess.run(
                ["pre-commit", "install", "--hook-type", "pre-push"],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("C5-REAL: Aegis Engine successfully crystallized P0 hooks.")
        except FileNotFoundError:
            logger.error("C5-REAL: Aegis Engine failed. 'pre-commit' binary not found in PATH.")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"C5-REAL: Aegis Engine failed to inject hooks. Exit code: {e.returncode}. Error: {e.stderr.strip()}"
            )
