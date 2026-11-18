"""Approval handlers for denied capabilities (default deny and HITL oracle)."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable, Mapping
from typing import Any

from agentdojo.base_tasks import BaseUserTask
from agentdojo.functions_runtime import Env

from b60_guard.canon import canonicalize_args, normalize_tool_args
from b60_guard.contracts import ApprovalDecision, ToolSpec


class DenyApprover:
    """Default non-interactive handler: rejects any call lacking capability admission."""

    def approve(self, tool: ToolSpec, normalized_args: dict[str, Any], reason: str) -> ApprovalDecision:
        return ApprovalDecision(approved=False, evidence_id=None, reason=reason)


class OracleGroundTruthApprover:
    """Simulates an honest human approver strictly for the ``A2-HITL`` arm."""

    def __init__(
        self,
        task: BaseUserTask[Any],
        pre_environment: Env,
        tool_specs: Mapping[str, ToolSpec],
        mint_and_commit: Callable[[ToolSpec, bytes], bytes],
    ) -> None:
        self._mint_and_commit = mint_and_commit
        self._allowed_calls: dict[tuple[str, bytes], deque[int]] = defaultdict(deque)
        self.requests = 0
        self.grants = 0

        env_copy = pre_environment.model_copy(deep=True)
        for idx, call in enumerate(task.ground_truth(env_copy)):
            spec = tool_specs.get(call.function)
            if spec is None or spec.kind != "write":
                continue
            norm = normalize_tool_args(spec, dict(call.args))
            canon = canonicalize_args(norm)
            self._allowed_calls[(spec.name, canon)].append(idx)

    def approve(self, tool: ToolSpec, normalized_args: dict[str, Any], reason: str) -> ApprovalDecision:
        self.requests += 1
        canon = canonicalize_args(normalized_args)
        key = (tool.name, canon)
        queue = self._allowed_calls.get(key)
        if queue:
            queue.popleft()
            evidence = self._mint_and_commit(tool, canon)
            self.grants += 1
            return ApprovalDecision(approved=True, evidence_id=evidence, reason="HITLApproved")
        return ApprovalDecision(approved=False, evidence_id=None, reason=f"HITLDenied: {reason}")
