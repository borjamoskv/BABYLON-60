"""PyO3 broker bridge: effect mapping, explicit scopes and single-use commit.

Requires the kernel built with ``--features python``::

    cargo build --locked -p babylon60_root --lib --features python --target-dir target/py
    BABYLON60_TEST_CAPABILITY_LIBRARY=target/py/debug/libbabylon60.dylib uv run --locked pytest tests/test_mcp_python_effect_scope.py -q
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from importlib.machinery import ExtensionFileLoader
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest


class _McpToken(Protocol):
    @property
    def token_id(self) -> bytes: ...


class _McpBroker(Protocol):
    def discover(self, name: str, hash: bytes, effect: str, scope: str | None = None) -> None: ...

    def authorize(self, name: str, hash: bytes, effect: str, scope: str | None = None) -> None: ...

    def revoke(self, name: str) -> None: ...

    def issue(
        self,
        name: str,
        hash: bytes,
        effect: str,
        args: bytes,
        scope: str | None = None,
        resource: str | None = None,
    ) -> _McpToken: ...

    def validate(
        self,
        token: _McpToken,
        name: str,
        hash: bytes,
        effect: str,
        args: bytes,
        scope: str | None = None,
        resource: str | None = None,
    ) -> None: ...

    def commit_once(
        self,
        token: _McpToken,
        name: str,
        hash: bytes,
        effect: str,
        args: bytes,
        scope: str | None = None,
        resource: str | None = None,
    ) -> bytes: ...


EFFECTS = (
    "FsRead",
    "FsMutate",
    "FsDelete",
    "FsChmod",
    "FsRename",
    "NetTransmit",
    "ProcSpawn",
    "ProcTerminate",
    "KeyDestroy",
    "LedgerAppend",
)
SCOPE = "agentdojo://banking/send_money"
HASH = hashlib.sha256(b"agentdojo_send_money_v1").digest()
ARGS = b'{"amount":100,"recipient":"GB29NWBK60161331926819"}'


@pytest.fixture(scope="module")
def native() -> ModuleType:
    value = os.environ.get("BABYLON60_TEST_CAPABILITY_LIBRARY")
    if value is None:
        pytest.skip("build kernel with --features python and set BABYLON60_TEST_CAPABILITY_LIBRARY")
    library = Path(value).absolute()
    assert library.is_file(), library
    loader = ExtensionFileLoader("_babylon60_mcp", str(library))
    spec = importlib.util.spec_from_file_location("_babylon60_mcp", library, loader=loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def granted(native: ModuleType, scope: str | None = SCOPE) -> _McpBroker:
    broker = cast(_McpBroker, native.McpBroker())
    broker.discover("send_money", HASH, "NetTransmit", scope)
    broker.authorize("send_money", HASH, "NetTransmit", scope)
    return broker


def test_historical_positional_api_keeps_default_scope(native: ModuleType) -> None:
    broker = native.McpBroker()
    broker.discover("ledger_append", HASH, "LedgerAppend")
    broker.authorize("ledger_append", HASH, "LedgerAppend")
    token = broker.issue("ledger_append", HASH, "LedgerAppend", b"x")
    broker.validate(token, "ledger_append", HASH, "LedgerAppend", b"x")
    # Reusable validation is the historical contract.
    broker.validate(token, "ledger_append", HASH, "LedgerAppend", b"x")


@pytest.mark.parametrize("effect", EFFECTS)
def test_every_effect_kind_is_mapped(native: ModuleType, effect: str) -> None:
    broker = native.McpBroker()
    broker.discover("tool", HASH, effect, "agentdojo://suite/tool")
    broker.authorize("tool", HASH, effect, "agentdojo://suite/tool")
    token = broker.issue("tool", HASH, effect, b"a", "agentdojo://suite/tool")
    assert len(broker.commit_once(token, "tool", HASH, effect, b"a", "agentdojo://suite/tool")) == 32


def test_unknown_effect_and_empty_scope_are_rejected(native: ModuleType) -> None:
    broker = native.McpBroker()
    with pytest.raises(ValueError, match="Unknown MCP effect"):
        broker.discover("tool", HASH, "Teleport")
    with pytest.raises(ValueError, match="Empty resource scope"):
        broker.discover("tool", HASH, "NetTransmit", "")


def test_resource_outside_scope_cannot_be_issued(native: ModuleType) -> None:
    broker = granted(native)
    broker.issue("send_money", HASH, "NetTransmit", ARGS, SCOPE, SCOPE + "/GB29")
    with pytest.raises(PermissionError):
        broker.issue("send_money", HASH, "NetTransmit", ARGS, SCOPE, "agentdojo://banking/update_password")


def test_commit_once_rejects_replay_and_failed_commit_does_not_consume(native: ModuleType) -> None:
    broker = granted(native)
    token = broker.issue("send_money", HASH, "NetTransmit", ARGS, SCOPE)
    assert len(token.token_id) == 32

    with pytest.raises(PermissionError, match="ConfigurationDrift"):
        broker.commit_once(token, "send_money", HASH, "NetTransmit", b'{"recipient":"ATTACKER"}', SCOPE)

    evidence = broker.commit_once(token, "send_money", HASH, "NetTransmit", ARGS, SCOPE)
    assert isinstance(evidence, bytes) and len(evidence) == 32

    with pytest.raises(PermissionError, match="NonceAlreadyConsumed"):
        broker.commit_once(token, "send_money", HASH, "NetTransmit", ARGS, SCOPE)


def test_hash_mismatch_and_revocation_reject_commit(native: ModuleType) -> None:
    broker = granted(native)
    token = broker.issue("send_money", HASH, "NetTransmit", ARGS, SCOPE)
    with pytest.raises(PermissionError, match="ToolIdentityMismatch"):
        broker.commit_once(token, "send_money", hashlib.sha256(b"tampered").digest(), "NetTransmit", ARGS, SCOPE)
    broker.revoke("send_money")
    with pytest.raises(PermissionError):
        broker.commit_once(token, "send_money", HASH, "NetTransmit", ARGS, SCOPE)


def test_token_cannot_be_constructed_from_python(native: ModuleType) -> None:
    with pytest.raises(TypeError):
        native.McpToken()


def test_blake3_digest_matches_known_vector(native: ModuleType) -> None:
    empty_expected = bytes.fromhex("af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262")
    assert native.blake3_digest(b"") == empty_expected
    assert len(native.blake3_digest(b"agentdojo_send_money_v1")) == 32
