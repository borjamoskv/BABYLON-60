"""FL-MCP-01 mediation for Cortex effects; the Rust broker owns policy semantics.

Native code and the Python host are trusted. This is not process/OS confinement.
No grant, signature, policy mutation or build operation is exposed as an MCP tool.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from contextvars import Context, ContextVar
from dataclasses import dataclass
from functools import wraps
import importlib.util
from importlib.machinery import ExtensionFileLoader
import inspect
import json
import marshal
from pathlib import Path
import secrets
from threading import Lock, get_ident
from typing import Any, ClassVar, Protocol, TypeVar, cast

from blake3 import blake3

from babylon60.verification.verification_gate import VerificationGate


class NativeBroker(Protocol):
    """Typed interface implemented by the compiled kernel extension."""

    def revision(self) -> int: ...
    def update_policy(self, feature: str, global_policy: str) -> None: ...
    def discover(self, name: str, digest: bytes, effect: str) -> None: ...
    def authorize(self, name: str, digest: bytes, effect: str) -> None: ...
    def revoke(self, name: str) -> None: ...
    def issue(self, name: str, digest: bytes, effect: str, arguments: bytes) -> object: ...
    def validate(self, token: object, name: str, digest: bytes, effect: str, arguments: bytes) -> None: ...


HandlerResult = dict[str, object] | Awaitable[dict[str, object]]
Handler = Callable[[dict[str, object]], HandlerResult]
TaskValue = TypeVar("TaskValue")

# Only these audited diagnostics bypass effect dispatch. New tools are protected.
READ_ONLY_TOOLS = frozenset(
    {
        "bft_query_ledger",
        "bft_verify_merkle_root",
        "causal_evaluate_task_risk",
        "causal_verify_ledger",
        "bft_route_skill",
        "causal_register_sign_off",
        "skills.discover",
        "skills.inspect",
        "skills.propose_effect",
    }
)
EFFECTS = {
    "bft_append_event": "LedgerAppend",
    "bft_send_sovereign_mail": "LedgerAppend",
    "blackboard_dispatch": "LedgerAppend",
    "royal_rumble_dispatch": "NetTransmit",
    "detonate_ephemeral_mcp": "ProcSpawn",
    "work_run_checks": "ProcSpawn",
}


def canonical(value: object) -> bytes:
    """Snapshot strict JSON once; callers never pass their mutable dict to a handler."""
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    if len(data) > 64 * 1024:
        raise ValueError("MCP approval payload exceeds 64 KiB")
    return data


@dataclass
class _Invocation:
    dispatcher: EffectDispatcher
    name: str
    arguments: bytes
    thread: int
    task: asyncio.Task[object] | None = None
    active: bool = True


_invocation: ContextVar[_Invocation | None] = ContextVar("mcp_effect_invocation", default=None)


def _current_task() -> asyncio.Task[object] | None:
    try:
        return asyncio.current_task()
    except RuntimeError:
        return None


def _guard_handler(name: str, handler: Callable[..., object]) -> Callable[..., object]:
    def check(instance: object, arguments: dict[str, object]) -> None:
        dispatcher = getattr(instance, "effect_dispatcher", None)
        if not isinstance(dispatcher, EffectDispatcher):
            raise PermissionError("FL-MCP-01: direct effect handler access denied")
        dispatcher.require_invocation(name, arguments)

    if inspect.iscoroutinefunction(handler):
        @wraps(handler)
        async def guarded_async(instance: object, arguments: dict[str, object]) -> object:
            check(instance, arguments)
            return await cast(Awaitable[object], handler(instance, arguments))
        return guarded_async

    @wraps(handler)
    def guarded(instance: object, arguments: dict[str, object]) -> object:
        check(instance, arguments)
        return handler(instance, arguments)
    return guarded


class MediatedHandlers:
    """Guard ordinary direct calls, including overrides, at each effect entry point.

    Trusted Python host introspection or arbitrary raw I/O is not OS confinement.
    """

    EFFECT_HANDLERS: ClassVar[Mapping[str, str]] = {}
    OBSERVATION_HANDLERS: ClassVar[frozenset[str]] = frozenset()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for attribute, handler in tuple(cls.__dict__.items()):
            name = cls.EFFECT_HANDLERS.get(attribute)
            if name is None and attribute.startswith("_tool_") and attribute not in cls.OBSERVATION_HANDLERS:
                name = attribute  # Unclassified handlers cannot acquire an invocation.
            if name is not None and callable(handler):
                setattr(cls, attribute, _guard_handler(name, handler))


class EffectDispatcher:
    """Keep approval and policy mediation through synchronous or awaited completion."""

    def __init__(self, gate: VerificationGate, native_library: Path | None) -> None:
        self._gate = gate
        self._lock = Lock()
        self._session = secrets.token_hex(32)
        self._native: NativeBroker | None = None
        self._library_digest = ""
        if native_library is not None:
            # Explicit trusted deployment path; never load a library from MCP input.
            self._library_digest = blake3(native_library.read_bytes()).hexdigest()
            loader = ExtensionFileLoader("_babylon60_mcp", str(native_library))
            spec = importlib.util.spec_from_file_location("_babylon60_mcp", native_library, loader=loader)
            if spec is None or spec.loader is None:
                raise ValueError("Cannot load the MCP kernel extension")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            factory = cast(Callable[[], NativeBroker], getattr(module, "McpBroker"))
            self._native = factory()

    def update_external_policy(self, feature: str, global_policy: str) -> None:
        """Trusted host sync only; cannot create a grant."""
        self._reject_reentry()
        with self._lock:
            self._broker().update_policy(feature, global_policy)

    def revoke_tool(self, name: str) -> None:
        """Trusted host revocation, serialized with effects."""
        self._reject_reentry()
        with self._lock:
            self._broker().revoke(name)

    def _broker(self) -> NativeBroker:
        if self._native is None:
            raise PermissionError("FL-MCP-01: native capability broker unavailable; effect denied")
        return self._native

    def _reject_reentry(self) -> None:
        scope = _invocation.get()
        if scope is not None and scope.active and scope.dispatcher is self and scope.thread == get_ident():
            raise PermissionError("Effect code cannot reenter dispatch or change its own policy")

    def _identity(self, name: str, handler: Handler) -> bytes:
        handler = inspect.unwrap(handler)
        source = inspect.getsourcefile(handler)
        function = getattr(handler, "__func__", handler)
        code = getattr(function, "__code__", None)
        if source is None or code is None:
            raise PermissionError("Cannot bind MCP handler identity")
        return blake3(
            canonical(
                {
                    "tool": name,
                    "effect": EFFECTS.get(name, "ProcSpawn"),
                    "code": blake3(marshal.dumps(code)).hexdigest(),
                    "module": blake3(Path(source).read_bytes()).hexdigest(),
                    "mediator": blake3(Path(__file__).read_bytes()).hexdigest(),
                    "kernel": self._library_digest,
                }
            )
        ).digest()

    def require_invocation(self, name: str, arguments: Mapping[str, object]) -> None:
        """A copied context, another task or a later callback cannot inherit authority."""
        scope = _invocation.get()
        if (
            scope is None or not scope.active or scope.dispatcher is not self
            or scope.name != name or scope.arguments != canonical(arguments)
            or scope.thread != get_ident() or scope.task is not _current_task()
        ):
            raise PermissionError("FL-MCP-01: handler requires its active mediated invocation")

    async def _settle(self, value: Awaitable[object], scope: _Invocation) -> object:
        loop = asyncio.get_running_loop()
        scope.task = asyncio.current_task()
        children: set[asyncio.Task[object]] = set()
        previous_factory = loop.get_task_factory()

        def factory(
            event_loop: asyncio.AbstractEventLoop,
            coroutine: Coroutine[Any, Any, TaskValue],
            /,
            *,
            context: Context | None = None,
            **kwargs: Any,
        ) -> asyncio.Task[TaskValue]:
            # This is a private per-dispatch loop; no unrelated application tasks.
            task = asyncio.Task(coroutine, loop=event_loop, context=context, **kwargs)
            children.add(cast(asyncio.Task[object], task))
            return task

        loop.set_task_factory(factory)
        try:
            result = await value
            checked: set[asyncio.Task[object]] = set()
            while children - checked:
                batch = children - checked
                outcomes = await asyncio.gather(*batch, return_exceptions=True)
                checked.update(batch)
                for outcome in outcomes:
                    if isinstance(outcome, BaseException):
                        raise outcome
            return result
        finally:
            # On failure/cancellation, nothing escapes the approval transaction.
            while pending := {task for task in children if not task.done()}:
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
            for task in children:
                if not task.cancelled():
                    task.exception()
            loop.set_task_factory(previous_factory)

    def _invoke(
        self, name: str, data: bytes, handler: Handler, arguments: dict[str, object],
    ) -> dict[str, object]:
        scope = _Invocation(self, name, data, get_ident(), _current_task())
        token = _invocation.set(scope)
        try:
            value: object = handler(arguments)
            if inspect.isawaitable(value):
                failures: list[object] = []
                with asyncio.Runner() as runner:
                    runner.get_loop().set_exception_handler(
                        lambda _loop, context: failures.append(
                            context.get("exception") or context.get("message", "async callback failed")
                        )
                    )
                    value = runner.run(self._settle(value, scope))
                if failures:
                    raise RuntimeError(f"Asynchronous effect failed: {failures[0]}")
            if not isinstance(value, dict):
                raise TypeError("Effect handler must finish with a result object")
            return value
        finally:
            scope.active = False
            _invocation.reset(token)

    def dispatch(
        self,
        name: str,
        arguments: Mapping[str, object],
        authorization: object,
        handler: Handler,
    ) -> dict[str, object]:
        """Prepare is observation only. Execute requires an existing signed approval."""
        effect_started = False
        try:
            self._reject_reentry()
            with self._lock:
                broker = self._broker()
                if name not in EFFECTS:
                    raise PermissionError("Tool has no reviewed effect classification")
                if not isinstance(authorization, dict):
                    raise PermissionError("Exact-call approval required; prepare an approval task first")
                execution_id = authorization.get("execution_id")
                if not isinstance(execution_id, str) or not 1 <= len(execution_id) <= 128:
                    raise ValueError("An execution_id of 1..128 characters is required")
                if set(authorization) - {"execution_id", "mode"}:
                    raise ValueError("Unknown authorization fields")
                mode = authorization.get("mode", "execute")
                if mode not in {"prepare", "execute"}:
                    raise ValueError("Unknown authorization mode")
                data = canonical(arguments)
                snapshot = json.loads(data)
                digest = self._identity(name, handler)
                effect = EFFECTS.get(name, "ProcSpawn")
                broker.discover(name, digest, effect)
                task: dict[str, object] = {
                    "execution_id": execution_id,
                    "action": f"mcp:{name}",
                    "is_mutative": True,
                    "session": self._session,
                    "policy_revision": broker.revision(),
                    "tool_hash": digest.hex(),
                    "effect": effect,
                    "arguments": snapshot,
                }
                if mode == "prepare":
                    return {
                        "content": [{"type": "text", "text": canonical(task).decode()}],
                        "approval_task": task,
                        "isError": False,
                    }
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    pass
                else:
                    raise PermissionError("Execute MCP effects through the synchronous ingress, outside a running loop")
                # Neither availability nor an MCP-provided boolean can pass this gate.
                if not self._gate.is_allowed(task):
                    raise PermissionError("Missing, expired, revoked or mismatched operator attestation")
                broker.authorize(name, digest, effect)
                token = broker.issue(name, digest, effect, data)

                def effect_once() -> dict[str, object]:
                    nonlocal effect_started
                    broker.validate(token, name, digest, effect, data)
                    if self._identity(name, handler) != digest:
                        raise PermissionError("Handler changed after approval")
                    effect_started = True
                    return self._invoke(name, data, handler, snapshot)

                # The gate consumes durably, then locks approval writers through the effect.
                return self._gate.execute_once(task, effect_once)
        except (Exception, asyncio.CancelledError) as exc:
            status = "EFFECT_OUTCOME_UNKNOWN" if effect_started else "DENIED"
            return {"content": [{"type": "text", "text": f"FL-MCP-01 {status}: {exc}"}], "isError": True}
