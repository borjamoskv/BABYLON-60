"""Shared types and runtime interfaces between planner, issuer, approver, and executor."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from pydantic import BaseModel

from b60_guard.native import CommitOnlyBroker

GuardArm = Literal["A0", "A1", "A2-strict", "A2c", "A2-noBroker", "A2-HITL", "C+", "C-"]
ToolKind = Literal["read", "write"]


@dataclass(frozen=True)
class ToolSpec:
    """Immutable metadata and Ring-0 policy binding for an AgentDojo tool."""

    name: str
    description: str
    parameters_schema: dict[str, Any]
    parameters_model: type[BaseModel]
    code_hash: bytes
    kind: ToolKind
    effect: str | None
    scope: str


@dataclass(frozen=True)
class AdmissionResult:
    """Decision returned by an admitter before running a write tool."""

    allowed: bool
    evidence_id: bytes | None
    reason: str
    mode: str
    latency_ns: int = 0
    broker_used: bool = False


@dataclass(frozen=True)
class ApprovalDecision:
    """Outcome from an optional human-in-the-loop approver."""

    approved: bool
    evidence_id: bytes | None
    reason: str


@dataclass(frozen=True)
class ToolCallTrace:
    """Audit record for a single intercepted tool invocation."""

    tool_name: str
    kind: ToolKind
    effect: str | None
    raw_args: dict[str, Any]
    canon_bytes: bytes | None
    allowed: bool
    evidence_id: bytes | None
    reason: str
    nested_call_denied: bool = False
    hitl_requested: bool = False
    hitl_granted: bool = False
    latency_ns: int = 0
    broker_used: bool = False


class WriteAdmitter(Protocol):
    """Mediation gate evaluated by ``GuardedToolsExecutor`` for write calls."""

    def admit_write(self, tool: ToolSpec, normalized_args: Mapping[str, Any], canon_bytes: bytes) -> AdmissionResult: ...


class ApprovalHandler(Protocol):
    """Optional approval fallback invoked only when configured (e.g., ``A2-HITL``)."""

    is_interactive: bool

    def approve(self, tool: ToolSpec, normalized_args: dict[str, Any], reason: str) -> ApprovalDecision: ...


@dataclass
class GuardSession:
    """Per-task capability state attached to ``extra_args`` for a single pipeline run."""

    arm: GuardArm
    suite_name: str
    query: str
    tool_specs: dict[str, ToolSpec]
    commit_broker: CommitOnlyBroker | None
    admitter: WriteAdmitter | None
    approver: ApprovalHandler | None = None
    records: list[ToolCallTrace] = field(default_factory=list)
    plan_stats: dict[str, Any] = field(default_factory=dict)
