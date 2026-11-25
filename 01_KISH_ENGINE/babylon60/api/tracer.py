"""
BABYLON-60 Ergonomic API — High-Level Tracer & Audit Engine (Sprints 2 & 4).
RFC-B60-2026-01-ADOPTION-ARCHITECTURE (Iceberg Pattern).

Provides a fluent, ergonomic API for autonomous agent observability, cryptographic
assurance, and EU AI Act compliance reporting with sub-millisecond overhead.
"""

from __future__ import annotations

import functools
import hashlib
import inspect
import json
import logging
import os
import tempfile
import threading
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, overload

from babylon60.api.assurance import AssuranceLevel
from babylon60.api.batch_accumulator import BatchMerkleAccumulator, _canonical_json
from babylon60.attestation.merkle_anchor import MerkleCausalAnchor
from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter

logger = logging.getLogger("babylon60.api.tracer")

F = TypeVar("F", bound=Callable[..., Any])

# Context variable tracking active session per async task or thread
_ACTIVE_SESSION_CTX: ContextVar[Optional["AuditSession"]] = ContextVar("b60_active_session", default=None)


class AuditSession:
    """
    Scattered-context execution audit session for an agent workflow.
    Guarantees causal tamper-evidence across sequential steps.
    """

    def __init__(
        self,
        tracer: "Tracer",
        session_id: str,
        assurance_level: Optional[AssuranceLevel] = None,
        operator_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.tracer: "Tracer" = tracer
        self.session_id: str = session_id
        self.assurance_level: AssuranceLevel = assurance_level or tracer.assurance_level
        self.operator_name: str = operator_name or tracer.operator_name
        self.metadata: Dict[str, Any] = metadata or {}

        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.events: List[Dict[str, Any]] = []

        # Buffer & Merkle accumulator
        algo = "sha3_256" if self.assurance_level == AssuranceLevel.AL3_SOVEREIGN else "sha256"
        self.accumulator: BatchMerkleAccumulator = BatchMerkleAccumulator(batch_size=100, algorithm=algo)

        # Hash chain anchor
        seed_bytes = f"{self.session_id}:{self.start_time}".encode("utf-8")
        self.prev_hash: str = hashlib.sha256(seed_bytes).hexdigest()

        self.is_closed: bool = False
        self.global_merkle_root: Optional[str] = None
        self.signature_info: Optional[Dict[str, Any]] = None
        self.hardware_anchor: Optional[Dict[str, Any]] = None
        self._bundle_dir: Optional[str] = None
        self._lock = threading.Lock()
        self._token: Optional[Any] = None

    @property
    def bundle_dir(self) -> str:
        """Directory path where this session's evidence bundle is stored."""
        if self._bundle_dir is None:
            base_dir = self.tracer.storage_dir or os.path.join(tempfile.gettempdir(), "b60_bundles")
            self._bundle_dir = os.path.join(base_dir, self.session_id)
            os.makedirs(self._bundle_dir, exist_ok=True)
        return self._bundle_dir

    def log_step(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Records an execution step within the session under the configured AssuranceLevel.

        - AL0_TRANSPARENT: In-memory SHA-256 hash (<0.05ms).
        - AL1_STANDARD: Incremental linear hash chain (<0.3ms).
        - AL2_COMPLIANCE: Micro-batch Merkle tree leaf accumulation.
        - AL3_SOVEREIGN: Per-step hardware measurement and maximum integrity.
        """
        now = time.time()
        iso_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now)) + f".{int((now % 1) * 1000):03d}Z"

        merged_payload = dict(payload or {})
        if kwargs:
            merged_payload.update(kwargs)

        merged_metadata = dict(metadata or {})

        with self._lock:
            step_index = len(self.events)

            step_data: Dict[str, Any] = {
                "session_id": self.session_id,
                "step_index": step_index,
                "action": action,
                "payload": merged_payload,
                "metadata": merged_metadata,
                "timestamp": iso_ts,
            }

            canonical_str = _canonical_json(step_data)
            step_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

            event_record: Dict[str, Any] = dict(step_data)
            event_record["hash"] = step_hash

            if self.assurance_level == AssuranceLevel.AL0_TRANSPARENT:
                # AL0: fast local hash only
                pass

            elif self.assurance_level == AssuranceLevel.AL1_STANDARD:
                # AL1: incremental linear hash chain
                chain_input = f"{self.prev_hash}:{step_hash}".encode("utf-8")
                self.prev_hash = hashlib.sha256(chain_input).hexdigest()
                event_record["chain_hash"] = self.prev_hash

            elif self.assurance_level == AssuranceLevel.AL2_COMPLIANCE:
                # AL2: incremental chain + batch Merkle accumulation
                chain_input = f"{self.prev_hash}:{step_hash}".encode("utf-8")
                self.prev_hash = hashlib.sha256(chain_input).hexdigest()
                event_record["chain_hash"] = self.prev_hash
                self.accumulator.add_leaf(step_hash)

            elif self.assurance_level == AssuranceLevel.AL3_SOVEREIGN:
                # AL3: full chain + Merkle + per-step hardware identity
                chain_input = f"{self.prev_hash}:{step_hash}".encode("utf-8")
                self.prev_hash = hashlib.sha3_256(chain_input).hexdigest()
                event_record["chain_hash"] = self.prev_hash
                self.accumulator.add_leaf(step_hash)

                anchor = MerkleCausalAnchor()
                hw_id = anchor.get_hardware_identity()
                event_record["hardware_uuid"] = hw_id.get("uuid", "GENERIC_HOST")
                event_record["enclave_type"] = hw_id.get("enclave_type", "GENERIC_HOST")

            self.events.append(event_record)
            return event_record

    def close(self) -> Dict[str, Any]:
        """
        Closes the session, seals the Merkle tree, produces cryptographic attestations,
        and saves the evidence bundle manifest.
        """
        with self._lock:
            if self.is_closed:
                return self.get_summary()

            self.end_time = time.time()
            self.is_closed = True

            # Compute final Merkle root
            if self.events:
                self.global_merkle_root = self.accumulator.finalize()
            else:
                empty_seed = f"EMPTY_SESSION:{self.session_id}:{self.start_time}".encode("utf-8")
                self.global_merkle_root = hashlib.sha256(empty_seed).hexdigest()

            # Cryptographic sealing based on assurance level
            if self.assurance_level in (AssuranceLevel.AL2_COMPLIANCE, AssuranceLevel.AL3_SOVEREIGN):
                self._sign_session_digest()

            if self.assurance_level == AssuranceLevel.AL3_SOVEREIGN:
                anchor = MerkleCausalAnchor()
                self.hardware_anchor = anchor.generate_hardware_pcr_quote(self.global_merkle_root)

            # Persist bundle manifest
            self._write_bundle_manifest()

            # Register completed session with tracer
            self.tracer._register_completed_session(self)

            return self.get_summary()

    def _sign_session_digest(self) -> None:
        """Signs the session root with Ed25519 (via seed or ephemeral key if allowed)."""
        summary_payload = {
            "session_id": self.session_id,
            "system_name": self.tracer.system_name,
            "global_merkle_root": self.global_merkle_root,
            "total_events": len(self.events),
            "assurance_level": self.assurance_level.value,
        }
        try:
            self.signature_info = EUAIActComplianceExporter.sign_certificate(summary_payload)
        except Exception as exc:
            # If signing is disallowed by policy, note it in metadata
            logger.debug("Session signing skipped or fallback: %s", exc)
            self.signature_info = {
                "algorithm": "Ed25519",
                "status": "UNSIGNED_NO_KEY",
                "error": str(exc),
            }

    def _write_bundle_manifest(self) -> None:
        """Writes manifest.json and events.json into the session bundle directory."""
        bundle_dir = self.bundle_dir
        manifest_path = os.path.join(bundle_dir, "manifest.json")
        events_path = os.path.join(bundle_dir, "events.json")

        manifest_data = {
            "global_hash": self.global_merkle_root,
            "session_id": self.session_id,
            "system_id": self.tracer.system_name,
            "system_name": self.tracer.system_name,
            "operator": self.operator_name,
            "operator_name": self.operator_name,
            "assurance_level": self.assurance_level.value,
            "events_count": len(self.events),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": ((self.end_time or time.time()) - self.start_time) * 1000,
            "signature": self.signature_info,
            "hardware_anchor": self.hardware_anchor,
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        with open(events_path, "w", encoding="utf-8") as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)

    def get_summary(self) -> Dict[str, Any]:
        """Returns structured session summary."""
        duration_ms = ((self.end_time or time.time()) - self.start_time) * 1000
        return {
            "session_id": self.session_id,
            "system_name": self.tracer.system_name,
            "operator_name": self.operator_name,
            "assurance_level": self.assurance_level.value,
            "total_events": len(self.events),
            "global_merkle_root": self.global_merkle_root,
            "duration_ms": duration_ms,
            "is_closed": self.is_closed,
            "bundle_dir": self.bundle_dir,
            "signature": self.signature_info,
            "hardware_anchor": self.hardware_anchor,
        }

    def __enter__(self) -> "AuditSession":
        self._token = _ACTIVE_SESSION_CTX.set(self)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if exc_type is not None:
                self.log_step(
                    action="exception_raised",
                    payload={"type": exc_type.__name__, "message": str(exc_val)},
                )
            self.close()
        finally:
            if self._token is not None:
                _ACTIVE_SESSION_CTX.reset(self._token)


class Tracer:
    """
    High-level ergonomic Tracer for BABYLON-60 (Iceberg Pattern).

    Usage in 3 lines:
        >>> import babylon60 as b60
        >>> tracer = b60.Tracer()
        >>> with tracer.audit() as s: s.log_step("prompt", {"user": "hi"})
    """

    def __init__(
        self,
        system_name: str = "BabylonAgent",
        assurance_level: Union[AssuranceLevel, str] = AssuranceLevel.AL2_COMPLIANCE,
        operator_name: str = "Sovereign Operator",
        storage_dir: Optional[str] = None,
        ledger_path: Optional[str] = None,
    ) -> None:
        self.system_name: str = system_name
        self.assurance_level: AssuranceLevel = AssuranceLevel.parse(assurance_level)
        self.operator_name: str = operator_name
        self.storage_dir: Optional[str] = storage_dir
        self.ledger_path: Optional[str] = ledger_path

        self._active_sessions: Dict[str, AuditSession] = {}
        self._completed_sessions: Dict[str, AuditSession] = {}
        self._lock = threading.Lock()

    def audit(
        self,
        session_id: Optional[str] = None,
        assurance_level: Optional[Union[AssuranceLevel, str]] = None,
        operator_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditSession:
        """
        Creates and returns an AuditSession context manager.

        Example:
            with tracer.audit(session_id="s123") as session:
                session.log_step("input", {"text": "hello"})
        """
        if not session_id:
            session_id = f"b60_sess_{hashlib.sha256(os.urandom(16)).hexdigest()[:12]}"

        lvl = AssuranceLevel.parse(assurance_level) if assurance_level is not None else self.assurance_level
        op = operator_name or self.operator_name

        session = AuditSession(
            tracer=self,
            session_id=session_id,
            assurance_level=lvl,
            operator_name=op,
            metadata=metadata,
        )

        with self._lock:
            self._active_sessions[session_id] = session

        return session

    def _register_completed_session(self, session: AuditSession) -> None:
        with self._lock:
            self._active_sessions.pop(session.session_id, None)
            self._completed_sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[AuditSession]:
        """Retrieves an active or completed session by ID."""
        with self._lock:
            return self._active_sessions.get(session_id) or self._completed_sessions.get(session_id)

    def get_latest_session(self) -> Optional[AuditSession]:
        """Returns the most recently recorded session."""
        with self._lock:
            if self._active_sessions:
                return list(self._active_sessions.values())[-1]
            if self._completed_sessions:
                return list(self._completed_sessions.values())[-1]
            return None

    @overload
    def watch(
        self,
        fn_or_action: F,
        *,
        action: Optional[str] = None,
        session_id: Optional[str] = None,
        record_args: bool = True,
        record_result: bool = True,
    ) -> F: ...

    @overload
    def watch(
        self,
        fn_or_action: Optional[str] = None,
        *,
        action: Optional[str] = None,
        session_id: Optional[str] = None,
        record_args: bool = True,
        record_result: bool = True,
    ) -> Callable[[F], F]: ...

    def watch(
        self,
        fn_or_action: Optional[Union[Callable[..., Any], str]] = None,
        *,
        action: Optional[str] = None,
        session_id: Optional[str] = None,
        record_args: bool = True,
        record_result: bool = True,
    ) -> Any:
        """
        Decorator that audits function execution and logs inputs, outputs, and runtime.
        Works both as `@tracer.watch` and `@tracer.watch(action="my_action")`.
        Supports both synchronous functions and async coroutines.
        """
        if callable(fn_or_action):
            # Used as bare decorator `@tracer.watch`
            func = fn_or_action
            return self._wrap_callable(
                func=func,
                action_name=action or func.__name__,
                session_id=session_id,
                record_args=record_args,
                record_result=record_result,
            )

        # Used with arguments `@tracer.watch(action="...")`
        action_name = fn_or_action or action

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            resolved_action = action_name or func.__name__
            return self._wrap_callable(
                func=func,
                action_name=resolved_action,
                session_id=session_id,
                record_args=record_args,
                record_result=record_result,
            )

        return decorator

    def _wrap_callable(
        self,
        func: Callable[..., Any],
        action_name: str,
        session_id: Optional[str],
        record_args: bool,
        record_result: bool,
    ) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                active = _ACTIVE_SESSION_CTX.get()
                owns_session = False
                session = active
                if session is None:
                    session = self.audit(session_id=session_id)
                    owns_session = True

                t0 = time.time()
                payload: Dict[str, Any] = {}
                if record_args:
                    payload["args"] = [self._sanitize_arg(a) for a in args]
                    payload["kwargs"] = {k: self._sanitize_arg(v) for k, v in kwargs.items()}

                if owns_session:
                    session.__enter__()
                try:
                    res = await func(*args, **kwargs)
                    if record_result:
                        payload["result"] = self._sanitize_arg(res)
                    payload["duration_ms"] = (time.time() - t0) * 1000
                    session.log_step(action=action_name, payload=payload)
                    return res
                except Exception as exc:
                    payload["exception"] = f"{exc.__class__.__name__}: {str(exc)}"
                    payload["duration_ms"] = (time.time() - t0) * 1000
                    session.log_step(action=f"{action_name}_error", payload=payload)
                    raise
                finally:
                    if owns_session:
                        session.__exit__(None, None, None)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            active = _ACTIVE_SESSION_CTX.get()
            owns_session = False
            session = active
            if session is None:
                session = self.audit(session_id=session_id)
                owns_session = True

            t0 = time.time()
            payload: Dict[str, Any] = {}
            if record_args:
                payload["args"] = [self._sanitize_arg(a) for a in args]
                payload["kwargs"] = {k: self._sanitize_arg(v) for k, v in kwargs.items()}

            if owns_session:
                session.__enter__()
            try:
                res = func(*args, **kwargs)
                if record_result:
                    payload["result"] = self._sanitize_arg(res)
                payload["duration_ms"] = (time.time() - t0) * 1000
                session.log_step(action=action_name, payload=payload)
                return res
            except Exception as exc:
                payload["exception"] = f"{exc.__class__.__name__}: {str(exc)}"
                payload["duration_ms"] = (time.time() - t0) * 1000
                session.log_step(action=f"{action_name}_error", payload=payload)
                raise
            finally:
                if owns_session:
                    session.__exit__(None, None, None)

        return sync_wrapper

    @staticmethod
    def _sanitize_arg(val: Any) -> Any:
        """Truncates or stringifies objects safely to prevent un-serializable errors."""
        if isinstance(val, (int, float, bool, type(None))):
            return val
        if isinstance(val, str):
            return val if len(val) <= 1000 else val[:1000] + "...[TRUNCATED]"
        if isinstance(val, (list, tuple)):
            return [Tracer._sanitize_arg(x) for x in val[:50]]
        if isinstance(val, dict):
            return {str(k): Tracer._sanitize_arg(v) for k, v in list(val.items())[:50]}
        return repr(val)

    def export_compliance_report(
        self,
        output_path: str,
        locale: str = "es",
        theme: str = "legal",
        session_id: Optional[str] = None,
        validity_days: int = 90,
    ) -> str:
        """
        Exports a cryptographically sealed EU AI Act compliance report (Articles 9-15)
        connected to the session's forensic evidence bundle.

        Args:
            output_path: Target path for the report (.html, .md, or .json).
            locale: Language code ("es", "en", "de", "fr", "it"). Default is "es".
            theme: Presentation theme ("legal", "dark", "light"). Default is "legal".
            session_id: Target session ID. Defaults to the latest session.
            validity_days: Certificate validity period in days.

        Returns:
            The absolute path of the generated report.
        """
        session: Optional[AuditSession] = None
        if session_id:
            session = self.get_session(session_id)

        if session is None:
            session = self.get_latest_session()

        if session is None:
            # If no sessions exist, instantiate and close an initial audit session
            with self.audit(session_id="init_compliance_session") as s:
                s.log_step("system_initialization", {"system": self.system_name, "status": "NOMINAL"})
            session = self.get_latest_session()

        assert session is not None
        if not session.is_closed:
            session.close()

        bundle_path = session.bundle_dir
        exporter = EUAIActComplianceExporter(
            artifact_bundle_path=bundle_path,
            ledger_path=self.ledger_path,
        )

        cert = exporter.generate_certificate(
            system_id=self.system_name,
            operator_name=self.operator_name,
            locale=locale,
            validity_days=validity_days,
        )

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = out_path.suffix.lower()

        if suffix in (".html", ".htm"):
            exported_path = exporter.export_html_report(cert, str(out_path), locale=locale)
            # If theme == "legal", refine HTML styling for court/audit grade presentation
            if theme == "legal":
                self._apply_legal_theme_to_html(exported_path)
            return exported_path

        if suffix in (".md", ".markdown"):
            return exporter.export_markdown_report(cert, str(out_path), locale=locale)

        if suffix == ".json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(cert, f, indent=2, ensure_ascii=False)
            return str(out_path)

        # Default fallback to HTML
        exported_path = exporter.export_html_report(cert, str(out_path) + ".html", locale=locale)
        return exported_path

    @staticmethod
    def _apply_legal_theme_to_html(html_file: str) -> None:
        """Injects clean legal/regulatory CSS styles into the exported HTML document."""
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            legal_css = """
        /* THEME: LEGAL COMPLIANCE GRADE */
        :root {
            --bg-color: #0f141c;
            --card-bg: rgba(22, 30, 46, 0.95);
            --accent: #38bdf8;
            --text: #f1f5f9;
            --border: rgba(56, 189, 248, 0.2);
        }
        .container {
            border: 2px solid #38bdf8 !important;
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.15) !important;
        }
            """
            if "</style>" in content:
                content = content.replace("</style>", f"{legal_css}\n    </style>")
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception as exc:
            logger.debug("Failed to apply legal theme overrides: %s", exc)


# -----------------------------------------------------------------------------
# Global default tracer and standalone watch decorator
# -----------------------------------------------------------------------------

_DEFAULT_TRACER: Optional[Tracer] = None
_DEFAULT_TRACER_LOCK = threading.Lock()


def _get_default_tracer() -> Tracer:
    global _DEFAULT_TRACER
    with _DEFAULT_TRACER_LOCK:
        if _DEFAULT_TRACER is None:
            _DEFAULT_TRACER = Tracer(
                system_name="DefaultAgent",
                assurance_level=AssuranceLevel.AL2_COMPLIANCE,
            )
        return _DEFAULT_TRACER


@overload
def watch(
    fn_or_action: F,
    *,
    action: Optional[str] = None,
    session_id: Optional[str] = None,
    record_args: bool = True,
    record_result: bool = True,
) -> F: ...


@overload
def watch(
    fn_or_action: Optional[str] = None,
    *,
    action: Optional[str] = None,
    session_id: Optional[str] = None,
    record_args: bool = True,
    record_result: bool = True,
) -> Callable[[F], F]: ...


def watch(
    fn_or_action: Optional[Union[Callable[..., Any], str]] = None,
    *,
    action: Optional[str] = None,
    session_id: Optional[str] = None,
    record_args: bool = True,
    record_result: bool = True,
) -> Any:
    """
    Standalone function decorator that logs execution through the active or default Tracer.

    Examples:
        >>> from babylon60 import watch
        >>> @watch
        ... def process_prompt(prompt):
        ...     return f"Echo: {prompt}"
        ...
        >>> @watch(action="custom_action")
        ... def compute_metric(x, y):
        ...     return x + y
    """
    active_session = _ACTIVE_SESSION_CTX.get()
    tracer = active_session.tracer if active_session is not None else _get_default_tracer()
    return tracer.watch(
        fn_or_action,
        action=action,
        session_id=session_id,
        record_args=record_args,
        record_result=record_result,
    )
