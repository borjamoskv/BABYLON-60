# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from babylon60.extensions.episodic.base import Episode

logger = logging.getLogger("babylon60_extensions.training")


@dataclass
class Action:
    tool: str
    input: Any
    observation: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Trajectory:
    session_id: str
    project: str
    issue_description: str
    actions: list[Action] = field(default_factory=list)
    outcome: str = "unknown"  # success, failure, partial
    reward: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class TrajectoryCollector:
    """
    Collects agent trajectories from CORTEX episodes for training purposes.
    Inspired by Skywork and OpenHands methodologies.
    """

    def __init__(self, episodic_memory: Any):
        self.episodic = episodic_memory

    async def collect_session_trajectory(self, session_id: str) -> Trajectory | None:
        """
        Reconstructs a trajectory for a specific session by grouping episodes.
        """
        try:
            episodes: list[Episode] = await self.episodic.get_session_timeline(session_id)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to retrieve timeline for session %s: %s", session_id, e)
            return None

        if not episodes:
            return None

        if not isinstance(episodes, list):
            logger.error(
                "episodic.get_session_timeline returned non-list type for session %s: %s",
                session_id,
                type(episodes),
            )
            return None

        project = episodes[0].project or "unknown"
        issue_description = self._extract_issue_description(episodes)

        actions, metadata = self._process_episodes(episodes)
        outcome = self._determine_outcome(episodes)

        return Trajectory(
            session_id=session_id,
            project=project,
            issue_description=issue_description,
            actions=[a for a in actions if a.tool not in (None, "unknown")],
            outcome=outcome,
            metadata=metadata,
        )

    def _extract_issue_description(self, episodes: list[Episode]) -> str:
        """Finds the first instruction or intent."""
        for ep in episodes:
            if ep.event_type == "decision" and ep.intent:
                return ep.intent
        return episodes[0].content or "unknown"

    def _parse_timestamp(self, ts_str: str | None) -> datetime:
        """Parses an ISO timestamp string robustly, handling Python 3.10 limitations."""
        if not ts_str:
            return datetime.now(timezone.utc)
        try:
            normalized = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(
                "Failed to parse ISO timestamp '%s': %s. Defaulting to current UTC time.", ts_str, e
            )
            return datetime.now(timezone.utc)

    def _process_episodes(self, episodes: list[Episode]) -> tuple[list[Action], dict[str, Any]]:
        """Processes episodes to extract actions and aggregate metadata."""
        actions: list[Action] = []
        current_action: Action | None = None
        metadata: dict[str, Any] = {}

        for ep in episodes:
            meta_dict = ep.meta if isinstance(ep.meta, dict) else {}
            if meta_dict:
                try:
                    metadata.update(meta_dict)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Failed to update metadata dictionary with %s: %s", meta_dict, e)

            if ep.event_type == "decision":
                if current_action:
                    actions.append(current_action)

                current_action = Action(
                    tool=meta_dict.get("tool") or "unknown",
                    input=meta_dict.get("input") or {},
                    timestamp=self._parse_timestamp(ep.created_at),
                )

            elif ep.event_type in ("discovery", "insight", "error"):
                if current_action:
                    prefix = "ERROR: " if ep.event_type == "error" else ""
                    content_str = ep.content or ""
                    observation_part = f"{prefix}{content_str}"
                    if current_action.observation:
                        current_action.observation += f"\n{observation_part}"
                    else:
                        current_action.observation = observation_part
                else:
                    logger.warning(
                        "Observation episode (id=%s, type=%s) encountered before any decision.",
                        getattr(ep, "id", "unknown"),
                        ep.event_type,
                    )

        if current_action:
            actions.append(current_action)

        return actions, metadata

    def _determine_outcome(self, episodes: list[Episode]) -> str:
        """Determine outcome from milestone or last episodes."""
        for ep in reversed(episodes):
            if ep.event_type == "milestone":
                content_str = ep.content or ""
                return "success" if "success" in content_str.lower() else "partial"
            if ep.event_type == "error":
                return "failure"
        return "unknown"

    def format_for_sft(self, trajectories: list[Trajectory], format_type: str = "sharegpt") -> str:
        """
        Formats trajectories for Supervised Fine-Tuning.
        Supports 'sharegpt' (Qwen2.5 compatible) and 'openai' formats.
        """
        if format_type not in ("sharegpt", "openai"):
            raise ValueError(
                f"Unsupported SFT format type: {format_type}. Supported: 'sharegpt', 'openai'"
            )

        formatted_data = []
        for traj in trajectories:
            if not traj.actions:
                continue

            conversation = [
                {
                    "from": "system",
                    "value": f"Context: {traj.project}\nIssue: {traj.issue_description}",
                }
            ]

            for action in traj.actions:
                try:
                    action_input_str = json.dumps(action.input)
                except (TypeError, ValueError) as e:
                    logger.warning(
                        "Failed to serialize action input for tool %s: %s. Using raw string representation.",
                        action.tool,
                        e,
                    )
                    try:
                        action_input_str = json.dumps(str(action.input))
                    except (TypeError, ValueError):
                        action_input_str = '"{}"'

                conversation.append(
                    {"from": "human", "value": f"Action: {action.tool}({action_input_str})"}
                )
                if action.observation:
                    conversation.append({"from": "gpt", "value": action.observation})

            if format_type == "sharegpt":
                formatted_data.append({"conversations": conversation})
            elif format_type == "openai":
                formatted_data.append(
                    {
                        "messages": [
                            {
                                "role": "system"
                                if c["from"] == "system"
                                else ("user" if c["from"] == "human" else "assistant"),
                                "content": c["value"],
                            }
                            for c in conversation
                        ]
                    }
                )

        return json.dumps(formatted_data, indent=2)
