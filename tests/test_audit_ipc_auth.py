"""Isolated H08 regressions: no native runtime, external I/O or production secrets."""

from __future__ import annotations

import hashlib
import secrets
import struct

import cbor2
from blake3 import blake3
import pytest

from babylon60.bft import bounty_ring_dispatcher as dispatch_module
from babylon60.bft.exergy_binary_ipc import (
    IPC_MAC_KEY_ENV,
    MAC_SIZE,
    MAGIC_HEADER,
    MAX_FRAME_SIZE,
    VERSION,
    pack_agent_message,
    require_ipc_mac_key,
    unpack_agent_message,
)
from babylon60.transducers.bounty_feed_transducer import BountyAdvisory, BountyDomain, BountyFeedTransducer


@pytest.fixture
def key() -> bytes:
    return secrets.token_bytes(32)


def test_unconfigured_channel_rejects_before_encoding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(IPC_MAC_KEY_ENV, raising=False)
    with pytest.raises(ValueError, match="provisioned"):
        pack_agent_message("sender", "recipient", {}, 1)
    with pytest.raises(ValueError, match="provisioned"):
        unpack_agent_message(b"untrusted")
    with pytest.raises(ValueError, match="provisioned"):
        dispatch_module.BountyRingDispatcher()


@pytest.mark.parametrize("encoded", ["", "0" * 63, "0" * 64, "x" * 64, "  " * 32])
def test_invalid_environment_key_is_rejected(monkeypatch: pytest.MonkeyPatch, encoded: str) -> None:
    monkeypatch.setenv(IPC_MAC_KEY_ENV, encoded)
    with pytest.raises(ValueError, match="32-byte"):
        require_ipc_mac_key()


def test_explicit_and_environment_secrets_interoperate(key: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(IPC_MAC_KEY_ENV, key.hex())
    frame = pack_agent_message("sender", "recipient", {"z": 1, "a": 2}, 9, mac_key=key)
    assert unpack_agent_message(frame) == ("sender", "recipient", {"z": 1, "a": 2}, 9)
    assert frame == pack_agent_message("sender", "recipient", {"a": 2, "z": 1}, 9)
    with pytest.raises(ValueError, match="MAC invalido"):
        unpack_agent_message(frame, mac_key=secrets.token_bytes(32))


def test_public_legacy_mac_cannot_authenticate(key: bytes) -> None:
    # Reproduce the original forge with its publicly known key, never a production credential.
    payload = cbor2.dumps({"advisory_id": "forged"})
    sender = b"bounty_feed_transducer"
    recipient = b"bounty_ring_dispatcher"
    header = struct.pack(">6sBHHQI", MAGIC_HEADER, 1, len(sender), len(recipient), 1, len(payload))
    body = header + sender + recipient + payload
    legacy_key = hashlib.sha256(b"BABYLON-60-B60IPC-MAC-KEY-V1").digest()
    forged = body + hashlib.blake2b(body, key=legacy_key, digest_size=8).digest()
    with pytest.raises(ValueError):
        unpack_agent_message(forged, mac_key=key)


@pytest.mark.parametrize("offset", [7, 15, 24, -1])
def test_modified_header_body_or_mac_is_rejected(key: bytes, offset: int) -> None:
    frame = bytearray(pack_agent_message("sender", "recipient", {"event": "audit"}, 1, mac_key=key))
    frame[offset] ^= 1
    with pytest.raises(ValueError):
        unpack_agent_message(bytes(frame), mac_key=key)


@pytest.mark.parametrize("payload", [cbor2.dumps([]), cbor2.dumps({1: "value"}), cbor2.dumps({}) + b"\x00"])
def test_authenticated_invalid_cbor_shape_is_rejected(key: bytes, payload: bytes) -> None:
    body = struct.pack(">6sBHHQI", MAGIC_HEADER, VERSION, 1, 1, 1, len(payload)) + b"AB" + payload
    frame = body + blake3(body, key=key).digest()
    with pytest.raises(ValueError, match="exactly one map"):
        unpack_agent_message(frame, mac_key=key)


def test_frame_size_limit(key: bytes) -> None:
    with pytest.raises(ValueError, match="size limit"):
        pack_agent_message("A", "B", {"blob": b"x" * MAX_FRAME_SIZE}, 1, mac_key=key)
    with pytest.raises(ValueError, match="size limit"):
        unpack_agent_message(b"x" * (MAX_FRAME_SIZE + 1), mac_key=key)
    frame = pack_agent_message("A", "B", {}, 1, mac_key=key)
    assert len(frame[-MAC_SIZE:]) == 32


def test_noncanonical_signed_cbor_is_rejected(key: bytes) -> None:
    payload = cbor2.dumps({"z": 1, "a": 2}, canonical=False)
    body = struct.pack(">6sBHHQI", MAGIC_HEADER, VERSION, 1, 1, 1, len(payload)) + b"AB" + payload
    with pytest.raises(ValueError, match="canonical CBOR"):
        unpack_agent_message(body + blake3(body, key=key).digest(), mac_key=key)


class RecordingManifest:
    """Test-only observation of attempted publication; never calls a native library."""

    def __init__(self) -> None:
        self.published: list[tuple[int, bytes]] = []
        self.accepting = True

    def publish(self, tick: int, digest: bytes) -> bool:
        if not self.accepting:
            return False
        self.published.append((tick, digest))
        return True


def test_dispatch_rejects_identity_replay_and_bad_schema_before_publication(
    key: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = RecordingManifest()
    monkeypatch.setattr(dispatch_module, "SharedManifestFFIWriter", lambda: manifest)
    dispatcher = dispatch_module.BountyRingDispatcher(mac_key=key)
    payload = {"advisory_id": "audit", "domain": BountyDomain.DOMAIN_EVM.value}
    frame = pack_agent_message("bounty_feed_transducer", "bounty_ring_dispatcher", payload, 1, mac_key=key)
    assert dispatcher.dispatch_frame(frame) is not None
    assert dispatcher.dispatch_frame(frame) is None
    for sender, recipient in [("attacker", "bounty_ring_dispatcher"), ("bounty_feed_transducer", "other")]:
        forged = pack_agent_message(sender, recipient, payload, 2, mac_key=key)
        assert dispatcher.dispatch_frame(forged) is None
    other_channel = pack_agent_message(
        "bounty_feed_transducer",
        "bounty_ring_dispatcher",
        payload,
        2,
        mac_key=secrets.token_bytes(32),
    )
    assert dispatcher.dispatch_frame(other_channel) is None
    malformed = pack_agent_message(
        "bounty_feed_transducer",
        "bounty_ring_dispatcher",
        {"domain": "not-a-domain"},
        2,
        mac_key=key,
    )
    assert dispatcher.dispatch_frame(malformed) is None
    assert manifest.published == [(1, blake3(frame).digest())]
    assert dispatcher.telemetry.total_dispatched == 1
    assert dispatcher.telemetry.total_corrupted_dropped == 5


def test_failed_publication_does_not_dispatch_or_consume_tick(key: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = RecordingManifest()
    manifest.accepting = False
    monkeypatch.setattr(dispatch_module, "SharedManifestFFIWriter", lambda: manifest)
    dispatcher = dispatch_module.BountyRingDispatcher(mac_key=key)
    frame = pack_agent_message("bounty_feed_transducer", "bounty_ring_dispatcher", {}, 1, mac_key=key)
    assert dispatcher.dispatch_frame(frame) is None
    assert dispatcher.telemetry.total_dispatched == 0
    manifest.accepting = True
    assert dispatcher.dispatch_frame(frame) is not None


def test_provisioned_transducer_dispatcher_bounded_stress(key: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = RecordingManifest()
    monkeypatch.setattr(dispatch_module, "SharedManifestFFIWriter", lambda: manifest)
    transducer = BountyFeedTransducer(mac_key=key)
    dispatcher = dispatch_module.BountyRingDispatcher(mac_key=key, queue_capacity=32)
    advisory = BountyAdvisory(
        "audit", "isolated_test", "Audit", "test", BountyDomain.DOMAIN_GENERAL, "low", "", "", "test-only"
    )
    for _ in range(16):  # Warmup; no latency or hardware certification claimed.
        assert dispatcher.dispatch_frame(transducer.pack_advisory_to_b60ipc(advisory)) is not None
    for _ in range(1000):
        assert dispatcher.dispatch_frame(transducer.pack_advisory_to_b60ipc(advisory)) is not None
    assert dispatcher.telemetry.total_dispatched == 1016
    assert dispatcher.get_queue_depths()["general"] == 32


def test_transducer_pins_provisioned_channel_key(key: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BABYLON60_IPC_MAC_KEY", key.hex())
    transducer = BountyFeedTransducer()
    # A channel captures configuration on creation, just like its dispatcher.
    monkeypatch.setenv("BABYLON60_IPC_MAC_KEY", secrets.token_hex(32))
    advisory = BountyAdvisory(
        "audit", "isolated_test", "Audit", "test", BountyDomain.DOMAIN_GENERAL, "low", "", "", "test-only"
    )
    frame = transducer.pack_advisory_to_b60ipc(advisory)
    assert unpack_agent_message(frame, mac_key=key)[2] == advisory.to_dict()


def test_transducer_rejects_missing_key_before_accepting_feed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BABYLON60_IPC_MAC_KEY", raising=False)
    with pytest.raises(ValueError, match="provisioned"):
        BountyFeedTransducer()
