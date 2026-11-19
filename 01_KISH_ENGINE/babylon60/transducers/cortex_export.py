"""Recipient-bound exports over the existing HTTP adapter; no process confinement.

The host supplies actor identity, recipient routing, policy and an audit sink.
Only an isolated test may enable cleartext loopback HTTP. A service must route
``/projects/{project}/records`` to that project and acknowledge the export ID,
recipient and exact body digest. An acknowledgement is a service assertion,
not independent proof of storage, a signature or downstream confinement.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
import hashlib
import math
import re
import time
from typing import Literal
import uuid

import httpx

from babylon60.transducers.http import post_with_retry


_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")


@dataclass(frozen=True)
class Recipient:
    """Trusted application identity; service is an origin, never a caller URL."""

    service: str
    project: str

    def __post_init__(self) -> None:
        url = httpx.URL(self.service)
        if (
            url.scheme not in {"http", "https"}
            or not url.host
            or url.userinfo
            or url.query
            or url.fragment
            or url.path != "/"
            or not _ID.fullmatch(self.project)
        ):
            raise ValueError("invalid recipient origin or project")
        object.__setattr__(self, "service", str(url).rstrip("/"))

    @property
    def endpoint(self) -> str:
        return f"{self.service}/projects/{self.project}/records"


@dataclass(frozen=True)
class ExportRequest:
    actor: str
    record_id: str
    export_id: str
    recipient: Recipient
    body_sha256: str
    method: Literal["POST"] = "POST"


@dataclass(frozen=True)
class ExportDecision:
    request: ExportRequest
    allowed: bool
    # Local monotonic deadline; this is an in-process policy interface, not a token wire format.
    expires_at: float


@dataclass(frozen=True)
class ExportReceipt:
    request: ExportRequest
    authorization: Literal["allowed", "denied", "error"]
    reason: str
    delivery: Literal[
        "not_dispatched",
        "recorded_before_send_unconfirmed",
        "dispatch_attempted_unconfirmed",
        "response_received_unconfirmed",
        "delivery_confirmed",
    ]
    http_status: int | None = None


class AuditUnavailable(RuntimeError):
    def __init__(self, receipt: ExportReceipt) -> None:
        super().__init__("export audit sink unavailable; inspect receipt.delivery")
        self.receipt = receipt


class _StopExport(Exception):
    def __init__(self, receipt: ExportReceipt) -> None:
        self.receipt = receipt


class CortexExportConnector:
    """One explicitly opted-in connector; does not alter MCP reads or other HTTP clients.

    Routes and actor must come from trusted host configuration, not tool arguments.
    The resolver is checked again after awaiting policy; the prepared request is
    then sent without another route lookup, redirects, ambient proxies or retries.
    The synchronous audit callback must persist entries if durability is required.
    """

    def __init__(
        self,
        *,
        actor: str,
        resolve: Callable[[str], Recipient],
        authorize: Callable[[ExportRequest], Awaitable[ExportDecision]],
        audit: Callable[[ExportReceipt], None],
        timeout: float = 5.0,
        allow_loopback_http: bool = False,
    ) -> None:
        if not _ID.fullmatch(actor) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("invalid actor or timeout")
        self._actor = actor
        self._resolve = resolve
        self._authorize = authorize
        self._audit = audit
        self._timeout = timeout
        self._allow_loopback_http = allow_loopback_http

    def _record(self, receipt: ExportReceipt) -> ExportReceipt:
        try:
            self._audit(receipt)
        except Exception:
            # Do not copy exception text: a sink may include protected values.
            raise AuditUnavailable(receipt) from None
        return receipt

    async def export(self, *, record_id: str, record: Mapping[str, object], destination: str) -> ExportReceipt:
        if not _ID.fullmatch(record_id):
            raise ValueError("invalid record identifier")
        recipient = self._resolve(destination)
        url = httpx.URL(recipient.endpoint)
        if url.scheme != "https" and not (self._allow_loopback_http and url.host in {"127.0.0.1", "::1"}):
            raise ValueError("recipient requires HTTPS")
        export_id = uuid.uuid4().hex
        context: ExportRequest | None = None
        dispatched = False
        response_status: int | None = None

        async def guard(request: httpx.Request) -> None:
            nonlocal context, dispatched
            # HTTPX has already serialized the body. Caller mutations during the
            # asynchronous decision cannot change these bytes or their digest.
            context = ExportRequest(
                self._actor, record_id, export_id, recipient, hashlib.sha256(request.content).hexdigest()
            )

            def stop(reason: str, *, error: bool = False) -> None:
                assert context is not None
                raise _StopExport(
                    self._record(ExportReceipt(context, "error" if error else "denied", reason, "not_dispatched"))
                )

            try:
                decision = await asyncio.wait_for(self._authorize(context), timeout=self._timeout)
            except Exception:
                stop("authorization_unavailable", error=True)
                return
            if not isinstance(decision, ExportDecision) or decision.request != context:
                stop("decision_binding_mismatch")
            if decision.allowed is not True:
                stop("policy_denied")
            if (
                not isinstance(decision.expires_at, (int, float))
                or not math.isfinite(decision.expires_at)
                or decision.expires_at <= time.monotonic()
            ):
                stop("decision_expired")
            # Persist the intent before the final route/deadline check so even
            # a route change during audit cannot transfer the approval to B.
            self._record(ExportReceipt(context, "allowed", "policy_allowed", "recorded_before_send_unconfirmed"))
            try:
                current = self._resolve(destination)
            except Exception:
                stop("route_unavailable", error=True)
                return
            if current != recipient or request.url != url or request.method != "POST":
                stop("recipient_changed")
            if decision.expires_at <= time.monotonic():
                stop("decision_expired")
            dispatched = True

        async def observe_response(response: httpx.Response) -> None:
            nonlocal response_status
            response_status = response.status_code

        try:
            async with httpx.AsyncClient(
                trust_env=False,
                follow_redirects=False,
                timeout=self._timeout,
                event_hooks={"request": [guard], "response": [observe_response]},
            ) as client:
                ack = await post_with_retry(
                    client,
                    recipient.endpoint,
                    {"X-Cortex-Export-ID": export_id},
                    record,
                    provider="cortex-export",
                    max_retries=1,
                )
        except _StopExport as exc:
            return exc.receipt
        except (httpx.HTTPError, ValueError):
            # No retry: the receiver may already have accepted the body.
            if context is None or not dispatched:
                raise
            return self._record(
                ExportReceipt(
                    context,
                    "allowed",
                    "redirect_refused"
                    if response_status is not None and 300 <= response_status < 400
                    else "transport_or_response_unconfirmed",
                    "response_received_unconfirmed"
                    if response_status is not None
                    else "dispatch_attempted_unconfirmed",
                    response_status,
                )
            )
        assert context is not None
        confirmed = (
            ack.get("status") == "received"
            and ack.get("recipient") == recipient.project
            and ack.get("export_id") == export_id
            and ack.get("body_sha256") == context.body_sha256
        )
        return self._record(
            ExportReceipt(
                context,
                "allowed",
                "recipient_acknowledged" if confirmed else "acknowledgement_missing_or_mismatched",
                "delivery_confirmed" if confirmed else "response_received_unconfirmed",
                response_status,
            )
        )
