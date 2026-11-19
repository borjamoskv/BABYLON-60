"""Synthetic egress probes using real loopback HTTP and independent A/B inboxes."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import asdict, dataclass, field, replace
import hashlib
import json
import time

import httpx
import pytest
import pytest_asyncio

from babylon60.transducers.http import post_with_retry
from babylon60.transducers.cortex_export import (
    AuditUnavailable,
    CortexExportConnector,
    ExportDecision,
    ExportReceipt,
    ExportRequest,
    Recipient,
)


MARKER = "SYNTHETIC-CORTEX-EGRESS-ONLY-20261118"
RECORD = {"record_id": "synthetic-1", "content": MARKER}
RECORD_DIGEST = hashlib.sha256(httpx.Request("POST", "https://example.test", json=RECORD).content).hexdigest()


@dataclass
class Receivers:
    origin: str = ""
    inboxes: dict[str, list[bytes]] = field(default_factory=lambda: {"A": [], "B": []})
    mode: str = "confirm"

    def url(self, project: str) -> str:
        return f"{self.origin}/projects/{project}/records"

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=3)
            lines = head.decode("ascii").split("\r\n")
            method, path, _ = lines[0].split()
            headers = dict(line.lower().split(": ", 1) for line in lines[1:] if ": " in line)
            body = await reader.readexactly(int(headers["content-length"]))
            project = path.split("/")[2]
            assert method == "POST" and path == f"/projects/{project}/records"
            self.inboxes[project].append(body)
            status, extra = 200, ""
            ack = {
                "status": "received",
                "recipient": project,
                "export_id": headers.get("x-cortex-export-id"),
                "body_sha256": hashlib.sha256(body).hexdigest(),
            }
            if self.mode == "redirect" and project == "A":
                status, extra = 307, f"Location: {self.url('B')}\r\n"
            elif self.mode == "no_ack":
                ack = {"status": "accepted"}
            elif self.mode == "wrong_recipient":
                ack["recipient"] = "B"
            elif self.mode == "wrong_digest":
                ack["body_sha256"] = "0" * 64
            elif self.mode == "wrong_export_id":
                ack["export_id"] = "old-export"
            elif self.mode == "rate_limit":
                status = 429
            elif self.mode == "disconnect":
                return
            response = json.dumps(ack).encode()
            writer.write(
                f"HTTP/1.1 {status} Test\r\n{extra}Content-Type: application/json\r\n"
                f"Content-Length: {len(response)}\r\nConnection: close\r\n\r\n".encode()
                + response
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


@pytest_asyncio.fixture
async def receivers() -> AsyncIterator[Receivers]:
    witness = Receivers()
    server = await asyncio.start_server(witness.handle, "127.0.0.1", 0)
    witness.origin = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
    async with server:
        yield witness


@pytest.mark.parametrize("project", ["A", "B"])
async def test_baseline_http_adapter_has_no_recipient_policy(receivers: Receivers, project: str) -> None:
    """A positive control and B counterexample, not assertions of secure egress."""
    async with httpx.AsyncClient(trust_env=False) as client:
        await post_with_retry(client, receivers.url(project), {}, RECORD, max_retries=1)
    assert json.loads(receivers.inboxes[project][0]) == RECORD
    assert not receivers.inboxes["B" if project == "A" else "A"]


async def test_baseline_adapter_inherits_redirect_policy(receivers: Receivers) -> None:
    """The existing helper permits A -> B when its caller enables redirects."""
    receivers.mode = "redirect"
    async with httpx.AsyncClient(trust_env=False, follow_redirects=True) as client:
        await post_with_retry(client, receivers.url("A"), {}, RECORD, max_retries=1)
    assert json.loads(receivers.inboxes["A"][0]) == RECORD
    assert json.loads(receivers.inboxes["B"][0]) == RECORD


async def allow_a(request: ExportRequest) -> ExportDecision:
    allowed = (
        request.actor == "agent-reader"
        and request.record_id == "synthetic-1"
        and request.recipient.project == "A"
        and request.body_sha256 == RECORD_DIGEST
    )
    return ExportDecision(request, allowed, time.monotonic() + 10)


@dataclass
class Harness:
    connector: CortexExportConnector
    routes: dict[str, Recipient]
    journal: list[ExportReceipt]


def harness(
    receivers: Receivers,
    authorize: Callable[[ExportRequest], Awaitable[ExportDecision]] = allow_a,
    audit: Callable[[ExportReceipt], None] | None = None,
    *,
    actor: str = "agent-reader",
    timeout: float = 2,
) -> Harness:
    routes = {project: Recipient(receivers.origin, project) for project in ("A", "B")}
    journal: list[ExportReceipt] = []
    connector = CortexExportConnector(
        actor=actor,
        resolve=routes.__getitem__,
        authorize=authorize,
        audit=audit or journal.append,
        timeout=timeout,
        allow_loopback_http=True,
    )
    return Harness(connector, routes, journal)


async def export(h: Harness, destination: str = "A") -> ExportReceipt:
    return await h.connector.export(record_id="synthetic-1", record=RECORD, destination=destination)


async def test_authorized_a_receives_and_receipt_binds_exact_bytes(receivers: Receivers) -> None:
    h = harness(receivers)
    receipt = await export(h)
    assert [r.delivery for r in h.journal] == ["recorded_before_send_unconfirmed", "delivery_confirmed"]
    assert receipt.request.recipient == h.routes["A"]
    assert receipt.request.body_sha256 == hashlib.sha256(receivers.inboxes["A"][0]).hexdigest()
    assert json.loads(receivers.inboxes["A"][0]) == RECORD
    assert not receivers.inboxes["B"]
    assert MARKER not in json.dumps([asdict(r) for r in h.journal])


async def test_same_actor_record_service_b_is_denied_without_content_in_audit(receivers: Receivers) -> None:
    h = harness(receivers)
    receipt = await export(h, "B")
    assert receipt.authorization == "denied" and receipt.reason == "policy_denied"
    assert receipt.delivery == "not_dispatched"
    assert not any(receivers.inboxes.values())
    assert h.routes["A"].service == h.routes["B"].service
    assert MARKER not in json.dumps([asdict(r) for r in h.journal])


async def test_route_a_rebound_to_b_during_authorization_stops(receivers: Receivers) -> None:
    async def reroute(request: ExportRequest) -> ExportDecision:
        decision = await allow_a(request)
        h.routes["A"] = h.routes["B"]
        return decision

    h = harness(receivers, reroute)
    receipt = await export(h)
    assert receipt.reason == "recipient_changed" and receipt.delivery == "not_dispatched"
    assert not any(receivers.inboxes.values())


async def test_route_changes_in_presend_audit_also_stop(receivers: Receivers) -> None:
    def reroute(receipt: ExportReceipt) -> None:
        if receipt.authorization == "allowed":
            h.routes["A"] = h.routes["B"]

    h = harness(receivers, audit=reroute)
    assert (await export(h)).reason == "recipient_changed"
    assert not any(receivers.inboxes.values())


async def test_http_redirect_does_not_reuse_a_approval_for_b(receivers: Receivers) -> None:
    receivers.mode = "redirect"
    h = harness(receivers)
    receipt = await export(h)
    assert receipt.delivery == "response_received_unconfirmed"
    assert receipt.reason == "redirect_refused" and receipt.http_status == 307
    assert len(receivers.inboxes["A"]) == 1 and not receivers.inboxes["B"]


@pytest.mark.parametrize("field", ["actor", "record_id", "body_sha256", "recipient", "export_id"])
async def test_decision_cannot_authorize_a_different_request(receivers: Receivers, field: str) -> None:
    async def mismatched(request: ExportRequest) -> ExportDecision:
        other = replace(request, actor="different")
        if field == "record_id":
            other = replace(request, record_id="different")
        elif field == "body_sha256":
            other = replace(request, body_sha256="different")
        elif field == "recipient":
            other = replace(request, recipient=Recipient(receivers.origin, "B"))
        elif field == "export_id":
            other = replace(request, export_id="different")
        return ExportDecision(other, True, time.monotonic() + 10)

    h = harness(receivers, mismatched)
    assert (await export(h)).reason == "decision_binding_mismatch"
    assert not any(receivers.inboxes.values())


@pytest.mark.parametrize("expires_at", [0.0, float("nan"), float("inf")])
async def test_expired_or_invalid_decision_stops(receivers: Receivers, expires_at: float) -> None:
    async def expired(request: ExportRequest) -> ExportDecision:
        return ExportDecision(request, True, expires_at)

    assert (await export(harness(receivers, expired))).reason == "decision_expired"
    assert not any(receivers.inboxes.values())


async def test_old_approval_cannot_be_replayed(receivers: Receivers) -> None:
    decisions: list[ExportDecision] = []

    async def replay(request: ExportRequest) -> ExportDecision:
        if not decisions:
            decisions.append(await allow_a(request))
        return decisions[0]

    h = harness(receivers, replay)
    assert (await export(h)).delivery == "delivery_confirmed"
    assert (await export(h)).reason == "decision_binding_mismatch"
    assert len(receivers.inboxes["A"]) == 1


async def test_same_project_rerouted_to_different_service_stops(receivers: Receivers) -> None:
    async def reroute(request: ExportRequest) -> ExportDecision:
        h.routes["A"] = Recipient("https://different.example.test", "A")
        return await allow_a(request)

    h = harness(receivers, reroute)
    assert (await export(h)).reason == "recipient_changed"
    assert not any(receivers.inboxes.values())


async def test_decision_expiring_during_audit_stops(receivers: Receivers) -> None:
    async def short_lived(request: ExportRequest) -> ExportDecision:
        return ExportDecision(request, True, time.monotonic() + 0.01)

    def slow_audit(receipt: ExportReceipt) -> None:
        if receipt.authorization == "allowed":
            time.sleep(0.02)

    assert (await export(harness(receivers, short_lived, slow_audit))).reason == "decision_expired"
    assert not any(receivers.inboxes.values())


async def test_caller_mutation_during_policy_cannot_change_prepared_body(receivers: Receivers) -> None:
    record: dict[str, object] = dict(RECORD)

    async def mutate(request: ExportRequest) -> ExportDecision:
        record["content"] = ["CHANGED-AFTER-AUTHORIZATION"]
        return await allow_a(request)

    h = harness(receivers, mutate)
    receipt = await h.connector.export(record_id="synthetic-1", record=record, destination="A")
    assert receipt.delivery == "delivery_confirmed"
    assert json.loads(receivers.inboxes["A"][0]) == RECORD


async def test_fresh_request_cannot_substitute_content_under_an_allowed_record_id(receivers: Receivers) -> None:
    h = harness(receivers)
    receipt = await h.connector.export(record_id="synthetic-1", record={"content": "OTHER-RECORD"}, destination="A")
    assert receipt.reason == "policy_denied" and receipt.delivery == "not_dispatched"
    assert not any(receivers.inboxes.values())


@pytest.mark.parametrize("mode", ["no_ack", "wrong_recipient", "wrong_digest", "wrong_export_id"])
async def test_http_success_without_matching_ack_is_not_delivery(receivers: Receivers, mode: str) -> None:
    receivers.mode = mode
    receipt = await export(harness(receivers))
    assert receipt.delivery == "response_received_unconfirmed" and receipt.http_status == 200
    assert len(receivers.inboxes["A"]) == 1 and not receivers.inboxes["B"]


@pytest.mark.parametrize("mode", ["rate_limit", "disconnect"])
async def test_uncertain_send_is_not_retried(receivers: Receivers, mode: str) -> None:
    receivers.mode = mode
    receipt = await export(harness(receivers))
    assert receipt.delivery != "delivery_confirmed"
    assert len(receivers.inboxes["A"]) == 1


@pytest.mark.parametrize("timeout", [False, True])
async def test_authorization_error_or_timeout_fails_closed(receivers: Receivers, timeout: bool) -> None:
    async def unavailable(request: ExportRequest) -> ExportDecision:
        if timeout:
            await asyncio.sleep(1)
        raise RuntimeError(MARKER)

    h = harness(receivers, unavailable, timeout=0.02)
    receipt = await export(h)
    assert receipt.reason == "authorization_unavailable" and receipt.delivery == "not_dispatched"
    assert not any(receivers.inboxes.values())
    assert MARKER not in json.dumps([asdict(r) for r in h.journal])


async def test_presend_audit_failure_prevents_network_dispatch(receivers: Receivers) -> None:
    def unavailable(receipt: ExportReceipt) -> None:
        raise OSError(MARKER)

    with pytest.raises(AuditUnavailable) as error:
        await export(harness(receivers, audit=unavailable))
    assert MARKER not in str(error.value)
    assert not any(receivers.inboxes.values())


async def test_postsending_audit_failure_does_not_claim_no_delivery(receivers: Receivers) -> None:
    def fail_after_send(receipt: ExportReceipt) -> None:
        if receipt.delivery == "delivery_confirmed":
            raise OSError(MARKER)

    with pytest.raises(AuditUnavailable) as error:
        await export(harness(receivers, audit=fail_after_send))
    assert error.value.receipt.delivery == "delivery_confirmed"
    assert len(receivers.inboxes["A"]) == 1


async def test_actor_identity_is_supplied_by_host(receivers: Receivers) -> None:
    assert (await export(harness(receivers, actor="different-agent"))).reason == "policy_denied"
    assert not any(receivers.inboxes.values())


@pytest.mark.parametrize("project", ["../B", "A/B", "A?project=B", "A#B", "%42"])
def test_recipient_rejects_ambiguous_project_paths(project: str) -> None:
    with pytest.raises(ValueError):
        Recipient("https://example.test", project)


@pytest.mark.parametrize(
    "origin",
    [
        "https://user:password@example.test",
        "https://example.test/x",
        "https://example.test?project=B",
        "http://example.test#B",
    ],
)
def test_recipient_requires_unambiguous_origin(origin: str) -> None:
    with pytest.raises(ValueError):
        Recipient(origin, "A")


async def test_cleartext_loopback_requires_explicit_test_optin(receivers: Receivers) -> None:
    connector = CortexExportConnector(
        actor="agent-reader",
        resolve=lambda _: Recipient(receivers.origin, "A"),
        authorize=allow_a,
        audit=lambda _: None,
    )
    with pytest.raises(ValueError, match="HTTPS"):
        await connector.export(record_id="synthetic-1", record=RECORD, destination="A")
    assert not any(receivers.inboxes.values())


async def test_bounded_concurrent_campaign_with_warmup(receivers: Receivers) -> None:
    """One warmup pair then 20 concurrent A/B pairs; no throughput claim."""
    h = harness(receivers)
    assert (await export(h)).delivery == "delivery_confirmed"
    assert (await export(h, "B")).delivery == "not_dispatched"
    results = await asyncio.gather(*(export(h, destination) for _ in range(20) for destination in ("A", "B")))
    assert sum(r.delivery == "delivery_confirmed" for r in results) == 20
    assert sum(r.delivery == "not_dispatched" for r in results) == 20
    assert len(receivers.inboxes["A"]) == 21 and not receivers.inboxes["B"]
    assert len({r.request.export_id for r in results}) == 40
    assert MARKER not in json.dumps([asdict(r) for r in h.journal])
