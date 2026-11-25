"""Shared Rekor anchor and the documented hash-registry boundary."""

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from babylon60.bft.cortex_crypto_kernel import publish_rekor_anchor
from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent
from babylon60.crypto.rekor_client import RekorClient
from babylon60.primitives.canonical import compute_tx_hash


def test_compute_tx_hash_is_not_sha256_hex() -> None:
    digest = compute_tx_hash("GENESIS", "project", "store", "{}", "2020-01-01T00:00:00+00:00")
    assert re.fullmatch(r"[0-9a-f]{64}", digest) is None
    assert digest


def test_shared_anchor_rejects_a_missing_or_invalid_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BABYLON60_SIGNING_SEED", raising=False)
    with pytest.raises(ValueError, match="ephemeral"):
        publish_rekor_anchor(b"{}", MagicMock(), None)
    with pytest.raises(ValueError, match="hex-encoded"):
        publish_rekor_anchor(b"{}", MagicMock(), "zz")
    with pytest.raises(ValueError, match="32 bytes"):
        publish_rekor_anchor(b"{}", MagicMock(), "00" * 31)


def test_both_ledgers_publish_through_the_shared_anchor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bytes] = []

    def publish(head_json: bytes, _client: object, _seed: str | None) -> dict[str, object]:
        calls.append(head_json)
        return {"shared": True}

    monkeypatch.setattr("babylon60.bft.cortex_persist_ledger.publish_rekor_anchor", publish)
    monkeypatch.setattr("babylon60.bft.ledger_actor.publish_rekor_anchor", publish)
    client = MagicMock(spec=RekorClient)
    ledger = CortexPersistLedger(tmp_path / "sync.db")
    ledger.append_event(CortexEvent("T", {"n": 1}, "taint"))
    assert ledger.anchor_to_rekor(rekor_client=client, seed_hex="11" * 32) == {"shared": True}

    async def actor_anchor() -> dict[str, object] | None:
        actor = BFTLedgerActor(tmp_path / "actor.db")
        await actor.start()
        await actor.append(LedgerEvent("s", "e", "T", {"n": 1}, "taint", "db", "table", "pk"))
        try:
            return await actor.anchor_to_rekor(rekor_client=client, seed_hex="22" * 32)
        finally:
            await actor.stop()

    import asyncio

    assert asyncio.run(actor_anchor()) == {"shared": True}
    assert len(calls) == 2
    assert client.anchor_payload.called is False
