"""Deterministic capability issuer and constraint compilers for all experimental arms."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter, ValidationError

from b60_guard.canon import (
    bind_use_index,
    canonicalize_args,
    literal_grounded_in_query,
    normalize_unicode,
)
from b60_guard.contracts import (
    AdmissionResult,
    ApprovalHandler,
    GuardArm,
    GuardSession,
    ToolSpec,
    WriteAdmitter,
)
from b60_guard.native import CommitOnlyBroker, NativeBroker, new_native_broker
from b60_guard.planner import AnyArg, IntentPlan, LiteralArg, ToolIntent


def _coerce_field_value(tool: ToolSpec, field_name: str, value: Any) -> Any:
    field_info = tool.parameters_model.model_fields.get(field_name)
    if field_info is None or field_info.annotation is None:
        return normalize_unicode(value)
    try:
        coerced = TypeAdapter(field_info.annotation).validate_python(value)
    except ValidationError:
        return normalize_unicode(value)
    return normalize_unicode(coerced)


def sanitize_plan_with_query(
    plan: IntentPlan,
    query: str,
    tool_specs: Mapping[str, ToolSpec],
) -> tuple[list[ToolIntent], dict[str, Any]]:
    """Downgrade ungrounded string/numeric literals to ``AnyArg`` and collect plan stats."""
    sanitized: list[ToolIntent] = []
    literal_args = 0
    any_args = 0
    downgraded = 0
    ignored_non_write = 0

    for intent in plan.intents:
        spec = tool_specs.get(intent.tool)
        if spec is None or spec.kind != "write":
            ignored_non_write += 1
            continue
        new_args: dict[str, LiteralArg | AnyArg] = {}
        for key, arg in intent.args.items():
            if isinstance(arg, LiteralArg):
                if literal_grounded_in_query(arg.literal, query):
                    new_args[key] = arg
                    literal_args += 1
                else:
                    new_args[key] = AnyArg(any=True)
                    any_args += 1
                    downgraded += 1
            else:
                new_args[key] = arg
                any_args += 1
        sanitized.append(ToolIntent(tool=intent.tool, args=new_args, max_uses=intent.max_uses))

    stats = {
        "write_intents": len(sanitized),
        "literal_args": literal_args,
        "any_args": any_args,
        "downgraded_ungrounded": downgraded,
        "ignored_non_write": ignored_non_write,
    }
    return sanitized, stats


def _authorize_write_tools(broker: NativeBroker, tool_names: set[str], tool_specs: Mapping[str, ToolSpec]) -> None:
    for name in sorted(tool_names):
        spec = tool_specs[name]
        assert spec.effect is not None
        broker.discover(spec.name, spec.code_hash, spec.effect, spec.scope)
        broker.authorize(spec.name, spec.code_hash, spec.effect, spec.scope)


class DenyAllAdmitter:
    """Positive control C+: denies every write attempt without authorizing any tool."""

    def admit_write(self, tool: ToolSpec, normalized_args: Mapping[str, Any], canon_bytes: bytes) -> AdmissionResult:
        return AdmissionResult(
            allowed=False,
            evidence_id=None,
            reason=f"PolicyDenied (C+ deny-all): {tool.name}",
            mode="C+",
            broker_used=True,
        )


class AuditOnlyAdmitter:
    """Negative control C-: logs calls through the session without blocking execution."""

    def admit_write(self, tool: ToolSpec, normalized_args: Mapping[str, Any], canon_bytes: bytes) -> AdmissionResult:
        return AdmissionResult(
            allowed=True,
            evidence_id=None,
            reason="AuditOnly (C-)",
            mode="C-",
            broker_used=False,
        )


class PreIssuedAdmitter:
    """A2-strict / A2-HITL admitter holding ONLY ``CommitOnlyBroker`` and pre-issued tokens."""

    def __init__(
        self,
        commit_broker: CommitOnlyBroker,
        preissued: list[tuple[str, bytes, object, bytes]],
    ) -> None:
        self._commit_broker = commit_broker
        self._unused_by_key: dict[tuple[str, bytes], deque[tuple[object, bytes]]] = defaultdict(deque)
        self._unused_by_tool: dict[str, list[tuple[object, bytes]]] = defaultdict(list)
        self._consumed_by_key: dict[tuple[str, bytes], list[tuple[object, bytes]]] = defaultdict(list)
        for tool_name, canon_bytes, token, bound_bytes in preissued:
            entry = (token, bound_bytes)
            self._unused_by_key[(tool_name, canon_bytes)].append(entry)
            self._unused_by_tool[tool_name].append(entry)

    def admit_write(self, tool: ToolSpec, normalized_args: Mapping[str, Any], canon_bytes: bytes) -> AdmissionResult:
        assert tool.effect is not None
        key = (tool.name, canon_bytes)
        t0 = time.perf_counter_ns()

        queue = self._unused_by_key.get(key)
        if queue:
            token, bound_bytes = queue.popleft()
            self._unused_by_tool[tool.name].remove((token, bound_bytes))
            try:
                evidence = self._commit_broker.commit_once(
                    token,
                    tool.name,
                    tool.code_hash,
                    tool.effect,
                    bound_bytes,
                    tool.scope,
                    tool.scope,
                )
            except PermissionError as exc:
                dt = time.perf_counter_ns() - t0
                return AdmissionResult(
                    allowed=False,
                    evidence_id=None,
                    reason=str(exc),
                    mode="A2-strict",
                    latency_ns=dt,
                    broker_used=True,
                )
            self._consumed_by_key[key].append((token, bound_bytes))
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=True,
                evidence_id=evidence,
                reason="Committed",
                mode="A2-strict",
                latency_ns=dt,
                broker_used=True,
            )

        # If unused tokens exist for this tool with different arguments, probe Rust to surface ConfigurationDrift
        # without consuming the legitimate unused token.
        tool_unused = self._unused_by_tool.get(tool.name)
        if tool_unused:
            probe_token, _ = tool_unused[0]
            try:
                self._commit_broker.commit_once(
                    probe_token,
                    tool.name,
                    tool.code_hash,
                    tool.effect,
                    bind_use_index(canon_bytes, 0),
                    tool.scope,
                    tool.scope,
                )
            except PermissionError as exc:
                dt = time.perf_counter_ns() - t0
                return AdmissionResult(
                    allowed=False,
                    evidence_id=None,
                    reason=str(exc),
                    mode="A2-strict",
                    latency_ns=dt,
                    broker_used=True,
                )

        # If this exact call exhausted its issued tokens, probe Rust to surface NonceAlreadyConsumed.
        consumed = self._consumed_by_key.get(key)
        if consumed:
            old_token, old_bound = consumed[0]
            try:
                self._commit_broker.commit_once(
                    old_token,
                    tool.name,
                    tool.code_hash,
                    tool.effect,
                    old_bound,
                    tool.scope,
                    tool.scope,
                )
            except PermissionError as exc:
                dt = time.perf_counter_ns() - t0
                return AdmissionResult(
                    allowed=False,
                    evidence_id=None,
                    reason=str(exc),
                    mode="A2-strict",
                    latency_ns=dt,
                    broker_used=True,
                )

        dt = time.perf_counter_ns() - t0
        return AdmissionResult(
            allowed=False,
            evidence_id=None,
            reason=f"PolicyDenied: no pre-issued token for {tool.name}",
            mode="A2-strict",
            latency_ns=dt,
            broker_used=True,
        )


@dataclass
class _CompiledRule:
    tool_name: str
    literal_checks: dict[str, Any]
    default_checks: dict[str, Any]
    max_uses: int
    uses: int = 0

    def matches(self, normalized_args: Mapping[str, Any]) -> bool:
        for k, expected in self.literal_checks.items():
            if normalized_args.get(k) != expected:
                return False
        for k, expected in self.default_checks.items():
            if normalized_args.get(k) != expected:
                return False
        return True


def _compile_rules(intents: list[ToolIntent], tool_specs: Mapping[str, ToolSpec]) -> dict[str, list[_CompiledRule]]:
    compiled: dict[str, list[_CompiledRule]] = defaultdict(list)
    for intent in intents:
        spec = tool_specs.get(intent.tool)
        if spec is None or spec.kind != "write":
            continue
        fields = spec.parameters_model.model_fields
        literal_checks: dict[str, Any] = {}
        default_checks: dict[str, Any] = {}
        valid_rule = True
        for fname, finfo in fields.items():
            if fname in intent.args:
                arg = intent.args[fname]
                if isinstance(arg, LiteralArg):
                    literal_checks[fname] = _coerce_field_value(spec, fname, arg.literal)
            else:
                if finfo.is_required():
                    valid_rule = False
                    break
                default_val = finfo.get_default(call_default_factory=True)
                default_checks[fname] = normalize_unicode(default_val)
        if valid_rule:
            compiled[intent.tool].append(
                _CompiledRule(
                    tool_name=intent.tool,
                    literal_checks=literal_checks,
                    default_checks=default_checks,
                    max_uses=intent.max_uses,
                )
            )
    return compiled


class ConstraintAdmitter:
    """A2c / A2-noBroker deterministic argument constraint checker."""

    def __init__(
        self,
        rules_by_tool: dict[str, list[_CompiledRule]],
        native_broker: NativeBroker | None,
        mode: str,
    ) -> None:
        self._rules = rules_by_tool
        self._broker = native_broker
        self._mode = mode

    def admit_write(self, tool: ToolSpec, normalized_args: Mapping[str, Any], canon_bytes: bytes) -> AdmissionResult:
        t0 = time.perf_counter_ns()
        rules = self._rules.get(tool.name)
        if not rules:
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=False,
                evidence_id=None,
                reason=f"PolicyDenied: {tool.name} not planned",
                mode=self._mode,
                latency_ns=dt,
                broker_used=self._broker is not None,
            )

        matched_rules = [r for r in rules if r.matches(normalized_args)]
        if not matched_rules:
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=False,
                evidence_id=None,
                reason=f"ConfigurationDrift: argument constraint mismatch for {tool.name}",
                mode=self._mode,
                latency_ns=dt,
                broker_used=self._broker is not None,
            )

        selected = next((r for r in matched_rules if r.uses < r.max_uses), None)
        if selected is None:
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=False,
                evidence_id=None,
                reason=f"NonceAlreadyConsumed: intent use budget exhausted for {tool.name}",
                mode=self._mode,
                latency_ns=dt,
                broker_used=self._broker is not None,
            )

        use_idx = selected.uses
        selected.uses += 1
        if self._broker is None:
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=True,
                evidence_id=None,
                reason="Allowed (noBroker)",
                mode=self._mode,
                latency_ns=dt,
                broker_used=False,
            )

        assert tool.effect is not None
        bound_bytes = bind_use_index(canon_bytes, use_idx)
        try:
            token = self._broker.issue(tool.name, tool.code_hash, tool.effect, bound_bytes, tool.scope, tool.scope)
            evidence = self._broker.commit_once(
                token, tool.name, tool.code_hash, tool.effect, bound_bytes, tool.scope, tool.scope
            )
        except PermissionError as exc:
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=False,
                evidence_id=None,
                reason=str(exc),
                mode=self._mode,
                latency_ns=dt,
                broker_used=True,
            )
        dt = time.perf_counter_ns() - t0
        return AdmissionResult(
            allowed=True,
            evidence_id=evidence,
            reason="Committed (A2c)",
            mode=self._mode,
            latency_ns=dt,
            broker_used=True,
        )


class ToolLevelAdmitter:
    """Ablation arm A1: authorizes tool names from plan without argument constraints."""

    def __init__(self, native_broker: NativeBroker, authorized_tools: set[str]) -> None:
        self._broker = native_broker
        self._authorized_tools = authorized_tools
        self._counters: dict[str, int] = defaultdict(int)

    def admit_write(self, tool: ToolSpec, normalized_args: Mapping[str, Any], canon_bytes: bytes) -> AdmissionResult:
        t0 = time.perf_counter_ns()
        if tool.name not in self._authorized_tools:
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=False,
                evidence_id=None,
                reason=f"PolicyDenied: tool {tool.name} not authorized in A1 plan",
                mode="A1",
                latency_ns=dt,
                broker_used=True,
            )
        assert tool.effect is not None
        use_idx = self._counters[tool.name]
        self._counters[tool.name] += 1
        bound_bytes = bind_use_index(canon_bytes, use_idx)
        try:
            token = self._broker.issue(tool.name, tool.code_hash, tool.effect, bound_bytes, tool.scope, tool.scope)
            evidence = self._broker.commit_once(
                token, tool.name, tool.code_hash, tool.effect, bound_bytes, tool.scope, tool.scope
            )
        except PermissionError as exc:
            dt = time.perf_counter_ns() - t0
            return AdmissionResult(
                allowed=False,
                evidence_id=None,
                reason=str(exc),
                mode="A1",
                latency_ns=dt,
                broker_used=True,
            )
        dt = time.perf_counter_ns() - t0
        return AdmissionResult(
            allowed=True,
            evidence_id=evidence,
            reason="Committed (A1)",
            mode="A1",
            latency_ns=dt,
            broker_used=True,
        )


def _issue_fully_literal_tokens(
    native_broker: NativeBroker,
    sanitized: list[ToolIntent],
    tool_specs: Mapping[str, ToolSpec],
) -> tuple[list[tuple[str, bytes, object, bytes]], int]:
    preissued: list[tuple[str, bytes, object, bytes]] = []
    skipped_with_any = 0
    for intent in sanitized:
        spec = tool_specs[intent.tool]
        if any(isinstance(arg, AnyArg) for arg in intent.args.values()):
            skipped_with_any += 1
            continue
        literal_payload = {k: arg.literal for k, arg in intent.args.items() if isinstance(arg, LiteralArg)}
        try:
            validated = normalize_unicode(spec.parameters_model.model_validate(literal_payload).model_dump())
        except ValidationError:
            skipped_with_any += 1
            continue
        canon_bytes = canonicalize_args(validated)
        assert spec.effect is not None
        for k in range(intent.max_uses):
            bound_bytes = bind_use_index(canon_bytes, k)
            token = native_broker.issue(spec.name, spec.code_hash, spec.effect, bound_bytes, spec.scope, spec.scope)
            preissued.append((spec.name, canon_bytes, token, bound_bytes))
    return preissued, skipped_with_any


def make_hitl_mint_callback(
    native_broker: NativeBroker,
) -> Callable[[ToolSpec, bytes], bytes]:
    """Build a per-session HITL mint-and-commit callback for ``A2-HITL`` approvers only."""
    counters: dict[tuple[str, bytes], int] = defaultdict(int)

    def mint_and_commit(tool: ToolSpec, canon_bytes: bytes) -> bytes:
        assert tool.effect is not None
        native_broker.discover(tool.name, tool.code_hash, tool.effect, tool.scope)
        native_broker.authorize(tool.name, tool.code_hash, tool.effect, tool.scope)
        key = (tool.name, canon_bytes)
        idx = counters[key]
        counters[key] += 1
        bound_bytes = bind_use_index(canon_bytes, idx)
        token = native_broker.issue(tool.name, tool.code_hash, tool.effect, bound_bytes, tool.scope, tool.scope)
        return native_broker.commit_once(
            token, tool.name, tool.code_hash, tool.effect, bound_bytes, tool.scope, tool.scope
        )

    return mint_and_commit


def build_guard_session(
    arm: GuardArm,
    suite_name: str,
    query: str,
    tool_specs: Mapping[str, ToolSpec],
    plan: IntentPlan,
    *,
    broker_factory: Callable[[], NativeBroker] = new_native_broker,
    approver_factory: Callable[[Callable[[ToolSpec, bytes], bytes]], ApprovalHandler] | None = None,
    approver: ApprovalHandler | None = None,
) -> GuardSession:
    """Compile a fresh per-task ``GuardSession`` according to the selected experimental arm."""
    sanitized, stats = sanitize_plan_with_query(plan, query, tool_specs)
    planned_tools = {intent.tool for intent in sanitized}

    if arm == "A0":
        return GuardSession(
            arm=arm,
            suite_name=suite_name,
            query=query,
            tool_specs=dict(tool_specs),
            commit_broker=None,
            admitter=None,
            approver=None,
            plan_stats=stats,
        )

    if arm == "C+":
        native_broker = broker_factory()
        commit_broker = CommitOnlyBroker(native_broker.commit_once)
        return GuardSession(
            arm=arm,
            suite_name=suite_name,
            query=query,
            tool_specs=dict(tool_specs),
            commit_broker=commit_broker,
            admitter=DenyAllAdmitter(),
            approver=None,
            plan_stats=stats,
        )

    if arm == "C-":
        native_broker = broker_factory()
        _authorize_write_tools(native_broker, planned_tools, tool_specs)
        commit_broker = CommitOnlyBroker(native_broker.commit_once)
        return GuardSession(
            arm=arm,
            suite_name=suite_name,
            query=query,
            tool_specs=dict(tool_specs),
            commit_broker=commit_broker,
            admitter=AuditOnlyAdmitter(),
            approver=None,
            plan_stats=stats,
        )

    if arm == "A1":
        native_broker = broker_factory()
        _authorize_write_tools(native_broker, planned_tools, tool_specs)
        return GuardSession(
            arm=arm,
            suite_name=suite_name,
            query=query,
            tool_specs=dict(tool_specs),
            commit_broker=CommitOnlyBroker(native_broker.commit_once),
            admitter=ToolLevelAdmitter(native_broker, planned_tools),
            approver=approver,
            plan_stats=stats,
        )

    if arm in ("A2-strict", "A2-HITL"):
        native_broker = broker_factory()
        _authorize_write_tools(native_broker, planned_tools, tool_specs)
        preissued, skipped = _issue_fully_literal_tokens(native_broker, sanitized, tool_specs)
        stats["preissued_tokens"] = len(preissued)
        stats["skipped_non_literal_intents"] = skipped
        commit_broker = CommitOnlyBroker(native_broker.commit_once)
        admitter: WriteAdmitter = PreIssuedAdmitter(commit_broker, preissued)
        resolved_approver = approver
        if arm == "A2-HITL" and approver_factory is not None:
            resolved_approver = approver_factory(make_hitl_mint_callback(native_broker))
        # Do not retain native_broker in A2-strict.
        return GuardSession(
            arm=arm,
            suite_name=suite_name,
            query=query,
            tool_specs=dict(tool_specs),
            commit_broker=commit_broker,
            admitter=admitter,
            approver=resolved_approver,
            plan_stats=stats,
        )

    if arm == "A2c":
        native_broker = broker_factory()
        _authorize_write_tools(native_broker, planned_tools, tool_specs)
        rules = _compile_rules(sanitized, tool_specs)
        return GuardSession(
            arm=arm,
            suite_name=suite_name,
            query=query,
            tool_specs=dict(tool_specs),
            commit_broker=CommitOnlyBroker(native_broker.commit_once),
            admitter=ConstraintAdmitter(rules, native_broker, mode="A2c"),
            approver=approver,
            plan_stats=stats,
        )

    if arm == "A2-noBroker":
        rules = _compile_rules(sanitized, tool_specs)
        return GuardSession(
            arm=arm,
            suite_name=suite_name,
            query=query,
            tool_specs=dict(tool_specs),
            commit_broker=None,
            admitter=ConstraintAdmitter(rules, None, mode="A2-noBroker"),
            approver=approver,
            plan_stats=stats,
        )

    raise ValueError(f"Unsupported guard arm: {arm}")
