# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babylon60.extensions.training.collector import Trajectory

logger = logging.getLogger("babylon60_extensions.training.reward")


class RewardEngine:
    """
    Assigns rewards to trajectories based on various signals.
    Follows reinforcement learning principles with test-based rewards.
    """

    def __init__(self, use_tests: bool = True):
        self.use_tests = use_tests

    def calculate_reward(self, trajectory: Trajectory) -> float:
        """
        Calculates a reward score between -1.0 and 1.0.
        Robust validation, NaN containment, and logic consistency checks enforced.
        Author: borjamoskv
        """
        if trajectory is None:
            logger.error("Trajectory object is None. Aborting reward calculation.")
            return -1.0

        # Extract fields with safe defaults to prevent AttributeErrors
        outcome = getattr(trajectory, "outcome", "unknown")
        actions = getattr(trajectory, "actions", [])
        metadata = getattr(trajectory, "metadata", {})

        # Enforce correct types
        if not isinstance(outcome, str):
            outcome = "unknown"
        if not isinstance(metadata, dict):
            metadata = {}

        reward = 0.0

        # 1. Base outcome reward
        if outcome == "success":
            reward += 0.5
        elif outcome == "failure":
            reward -= 0.5

        # 2. Efficiency penalty (fewer steps are better)
        # Small penalty per step to encourage conciseness
        num_actions = len(actions) if hasattr(actions, "__len__") else 0
        step_penalty = num_actions * 0.01
        if not math.isfinite(step_penalty) or step_penalty < 0:
            step_penalty = 0.1
        reward -= min(step_penalty, 0.1)

        # 3. Test-based verification (Primary Reward)
        if self.use_tests and outcome == "success":
            tests_passed = bool(metadata.get("tests_passed", False))
            tests_run = bool(metadata.get("tests_run", False))

            # If the metadata indicates tests passed, we give a major boost
            if tests_passed:
                reward += 0.5
            elif tests_run:
                # Tests ran but failed, yet outcome was reported as success.
                # Penalize contradiction to prevent false success claims (reward hacking).
                reward -= 0.5

        # 4. Sentiment / Quality signals
        try:
            avg_confidence = float(metadata.get("avg_confidence", 0.0))
        except (TypeError, ValueError):
            avg_confidence = 0.0

        if not math.isfinite(avg_confidence):
            avg_confidence = 0.0

        if avg_confidence > 0.8:
            reward += 0.1

        # Clip reward safely to [-1, 1], guaranteeing finite return value
        if not math.isfinite(reward) or math.isnan(reward):
            logger.error(f"Calculated reward was non-finite ({reward}). Safety resetting to 0.0.")
            reward = 0.0

        # Clip reward to [-1, 1]
        return max(min(reward, 1.0), -1.0)
