"""Exercise the real HTTP parser/handler without listeners or license signing."""

import io
import json
import secrets
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from blake3 import blake3

from scripts import zero_touch_onboarding_daemon as onboarding

TEST_TOKEN = blake3(b"public test fixture: onboarding HTTP authorization v1").hexdigest()
HOST = "127.0.0.1:8060"
BODY = json.dumps({"client_name": "AUDIT TEST ONLY", "client_vat": "DE000000000", "tier": "pilot"}).encode()


class MemorySocket:
    def __init__(self, request: bytes) -> None:
        self.input = io.BytesIO(request)
        self.output = bytearray()
        self.timeout: float | None = None

    def settimeout(self, seconds: float) -> None:
        self.timeout = seconds

    def makefile(self, *args, **kwargs):
        return self.input

    def sendall(self, data: bytes) -> None:
        self.output.extend(data)


@pytest.fixture
def service(monkeypatch):
    authority = onboarding.OnboardingSession(bytes.fromhex(TEST_TOKEN))
    server = SimpleNamespace(authorization=authority, expected_host=HOST)
    provision = Mock(return_value={"status": "TEST_DISPATCH_ONLY_NO_LICENSE"})
    monkeypatch.setattr(onboarding, "process_zero_touch_pilot_order", provision)
    monkeypatch.setattr(onboarding.ZeroTouchHttpHandler, "log_message", lambda *args: None)
    return server, provision


def request(server, headers, body=BODY, *, method="POST", path=onboarding.ORDER_PATH, extra=()):
    header_lines = list(headers.items()) + list(extra)
    raw = f"{method} {path} HTTP/1.0\r\n".encode()
    raw += b"".join(f"{key}: {value}\r\n".encode("latin-1") for key, value in header_lines)
    sock = MemorySocket(raw + b"\r\n" + body)
    onboarding.ZeroTouchHttpHandler(sock, ("127.0.0.1", 12345), server)
    head, payload = bytes(sock.output).split(b"\r\n\r\n", 1)
    assert sock.timeout == 5
    return int(head.split()[1]), json.loads(payload)


def signed(server, body=BODY, **kwargs):
    return onboarding.order_request_headers(TEST_TOKEN, server.authorization.session_id, HOST, body, **kwargs)


def test_exact_authenticated_order_dispatches_once(service):
    server, provision = service
    headers = signed(server)
    status, response = request(server, headers)
    assert status == 200
    assert response == {"status": "TEST_DISPATCH_ONLY_NO_LICENSE"}
    provision.assert_called_once_with(json.loads(BODY))
    assert TEST_TOKEN not in json.dumps(headers)
    assert request(server, headers)[0] == 403
    provision.assert_called_once()


def test_original_unauthenticated_request_cannot_create_effect_canary(service, tmp_path):
    server, provision = service
    canary = tmp_path / "provisioning-dispatch-canary"

    def observed_effect(payload):
        canary.write_text("TEST DISPATCH ONLY; NO LICENSE")
        return {"status": "TEST_DISPATCH_ONLY_NO_LICENSE"}

    provision.side_effect = observed_effect
    audit_headers = {
        "Host": HOST, "Content-Length": str(len(BODY)),
        "Origin": "https://untrusted.example", "Content-Type": "text/plain",
    }
    assert request(server, audit_headers)[0] == 403
    assert not canary.exists()
    provision.assert_not_called()
    # Positive control proves the independent witness detects a dispatched effect.
    assert request(server, signed(server))[0] == 200
    assert canary.read_text() == "TEST DISPATCH ONLY; NO LICENSE"


@pytest.mark.parametrize("field,value", [
    ("Authorization", None),
    ("Authorization", "BLAKE3 " + "00" * 32),
    ("Host", "untrusted.example:8060"),
    ("Origin", "https://untrusted.example"),
    ("Origin", "null"),
    ("Content-Type", "text/plain"),
    ("Content-Type", "application/x-www-form-urlencoded"),
    ("Content-Length", "-1"),
    ("Content-Length", "invalid"),
    ("Content-Length", str(onboarding.MAX_BODY_BYTES + 1)),
    ("Transfer-Encoding", "chunked"),
    ("X-Babylon-Session", "00" * 16),
    ("X-Babylon-Timestamp", "not-a-timestamp"),
    ("X-Babylon-Nonce", "short"),
])
def test_rejects_untrusted_request_before_provisioning(service, field, value):
    server, provision = service
    headers = signed(server)
    if value is None:
        headers.pop(field)
    else:
        headers[field] = value
    status, response = request(server, headers)
    assert status == 403
    assert response == {"error": "Request rejected"}
    provision.assert_not_called()


def test_non_ascii_authorization_is_rejected_by_real_http_parser(service):
    server, provision = service
    headers = signed(server)
    headers["Authorization"] = "BLAKE3 " + "é" * 64
    assert request(server, headers)[0] == 403
    provision.assert_not_called()


@pytest.mark.parametrize("name", ["Host", "Authorization", "Content-Length", "Content-Type", "Origin"])
def test_rejects_repeated_security_headers(service, name):
    server, provision = service
    headers = signed(server)
    headers["Origin"] = f"http://{HOST}"
    status, _ = request(server, headers, extra=[(name, headers[name])])
    assert status == 403
    provision.assert_not_called()


def test_body_modification_does_not_reach_provisioner(service):
    server, provision = service
    body = BODY.replace(b'"pilot"', b'"enterprise"')
    headers = signed(server)
    headers["Content-Length"] = str(len(body))
    assert request(server, headers, body)[0] == 403
    provision.assert_not_called()
    # A rejected MAC cannot burn the valid request's nonce.
    assert request(server, signed(server))[0] == 200


@pytest.mark.parametrize("age", [61, -1])
def test_expired_and_future_requests_are_rejected(service, monkeypatch, age):
    server, provision = service
    monkeypatch.setattr(onboarding.time, "time", lambda: 1000)
    headers = signed(server, timestamp=1000 - age)
    assert request(server, headers)[0] == 403
    provision.assert_not_called()


def test_request_at_ttl_boundary_is_accepted(service, monkeypatch):
    server, provision = service
    monkeypatch.setattr(onboarding.time, "time", lambda: 1000)
    assert request(server, signed(server, timestamp=940))[0] == 200
    provision.assert_called_once()


def test_new_process_session_invalidates_old_request(service):
    server, provision = service
    old_headers = signed(server)
    server.authorization = onboarding.OnboardingSession(bytes.fromhex(TEST_TOKEN))
    assert request(server, old_headers)[0] == 403
    provision.assert_not_called()
    assert request(server, signed(server))[0] == 200


def test_failed_provisioning_consumes_authorization_and_hides_details(service):
    server, provision = service
    provision.side_effect = RuntimeError("private canary /some/internal/path")
    headers = signed(server)
    status, response = request(server, headers)
    assert status == 500
    assert "private canary" not in json.dumps(response)
    assert request(server, headers)[0] == 403
    provision.assert_called_once()


@pytest.mark.parametrize("body", [b"[]", b"not-json", b'{}', b'{"client_name":1,"client_vat":"x"}'])
def test_invalid_order_schema_is_rejected_before_provisioner(service, body):
    server, provision = service
    assert request(server, signed(server, body), body)[0] == 403
    provision.assert_not_called()


def test_incomplete_body_is_rejected(service):
    server, provision = service
    assert request(server, signed(server), BODY[:-1])[0] == 403
    provision.assert_not_called()


def test_capacity_rejects_without_effect_instead_of_evicting_live_nonce(service):
    server, provision = service
    server.authorization._consumed = {str(index): 2**40 for index in range(4096)}
    assert request(server, signed(server))[0] == 403
    provision.assert_not_called()


def test_health_exposes_only_public_challenge_and_checks_origin(service):
    server, provision = service
    status, response = request(server, {"Host": HOST}, b"", method="GET", path="/api/v1/health")
    assert status == 200
    assert response["session_id"] == server.authorization.session_id
    assert TEST_TOKEN not in json.dumps(response)
    assert request(server, {"Host": HOST, "Origin": "https://untrusted.example"}, b"", method="GET", path="/api/v1/health")[0] == 403
    provision.assert_not_called()


def test_server_without_authority_rejects_before_provisioning(service):
    server, provision = service
    assert request(SimpleNamespace(expected_host=HOST), signed(server))[0] == 403
    provision.assert_not_called()


@pytest.mark.parametrize("token", ["", "00" * 32, "not-hex", "aa" * 31])
def test_serve_requires_configured_key_before_opening_listener(monkeypatch, token):
    monkeypatch.setenv("BABYLON_ONBOARDING_SESSION_TOKEN", token)
    monkeypatch.setattr(onboarding.sys, "argv", ["onboarding", "--serve"])
    listener = Mock()
    monkeypatch.setattr(onboarding, "OnboardingHTTPServer", listener)
    with pytest.raises(SystemExit) as failure:
        onboarding.run_cli()
    assert failure.value.code == 2
    listener.assert_not_called()


def test_authentication_non_replay_stress_with_warmup(service):
    server, provision = service
    assert request(server, signed(server))[0] == 200  # warmup
    for _ in range(40):
        headers = signed(server, nonce=secrets.token_hex(16))
        assert request(server, headers)[0] == 200
        assert request(server, headers)[0] == 403
    assert provision.call_count == 41
