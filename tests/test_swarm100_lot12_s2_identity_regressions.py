"""Lote12 identity regressions: disposable paths and software keys only."""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import multiprocessing
import os
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from babylon60.crypto import identity, keys


@pytest.fixture(autouse=True)
def confined_identity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CORTEX_DB_PATH", str(tmp_path / "state"))
    monkeypatch.setenv("CORTEX_TESTING", "1")
    monkeypatch.delenv("BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64", raising=False)
    monkeypatch.setattr(keys, "keyring", None)
    monkeypatch.setattr(keys.KeyManager, "_fallback_keyring", {})
    # Exercise the actual KDF/AEAD, with a smaller test-only work factor.
    monkeypatch.setattr(identity, "ARGON2_MEMORY_COST", 1024)
    monkeypatch.setattr(identity, "ARGON2_TIME_COST", 1)
    monkeypatch.setattr(identity, "ARGON2_PARALLELISM", 1)


def test_c0337_existing_identity_is_never_replaced(tmp_path: Path) -> None:
    forge = identity.L0IdentityForge(tmp_path / "identity")
    original = forge.forge_identity("fixture-passphrase")
    encrypted = forge.seed_path.read_bytes()
    with pytest.raises(FileExistsError):
        forge.forge_identity("different-fixture-passphrase")
    assert forge.seed_path.read_bytes() == encrypted
    assert forge.load_identity("fixture-passphrase") == original


def test_c0337_existing_seed_symlink_preserves_target(tmp_path: Path) -> None:
    forge = identity.L0IdentityForge(tmp_path / "identity")
    forge.storage_dir.mkdir()
    victim = tmp_path / "neighbor.txt"
    victim.write_bytes(b"preserve-neighbor")
    forge.seed_path.symlink_to(victim)
    with pytest.raises(OSError):
        forge.forge_identity("fixture-passphrase")
    assert victim.read_bytes() == b"preserve-neighbor"
    assert forge.seed_path.is_symlink()


def test_c0345_stale_managers_preserve_keys_and_revocation() -> None:
    first = keys.KeyManager("fixture-stale")
    stale = keys.KeyManager("fixture-stale")
    public_a = first.generate_and_store_key("actor-a")
    public_b = stale.generate_and_store_key("actor-b")
    assert first.revoke_key("actor-a")
    fresh = keys.KeyManager("fixture-stale")
    assert fresh.get_public_key_b64("actor-a") == public_a
    assert fresh.get_public_key_b64("actor-b") == public_b
    assert fresh.is_revoked("actor-a")
    assert stale.is_revoked("actor-a")
    assert stale.get_private_key_b64("actor-a") is None


def test_c0345_stale_writer_does_not_restore_revocation() -> None:
    first = keys.KeyManager("fixture-revoked")
    first.generate_and_store_key("actor-a")
    stale = keys.KeyManager("fixture-revoked")
    assert first.revoke_key("actor-a")
    stale.generate_and_store_key("actor-b")
    assert keys.KeyManager("fixture-revoked").is_revoked("actor-a")


def test_c0337_concurrent_creators_have_one_complete_winner(tmp_path: Path) -> None:
    for round_number in range(5):  # two warmup rounds and three checked bursts
        directory = tmp_path / f"burst-{round_number}"
        barrier = threading.Barrier(6)

        def create(_index):
            barrier.wait(timeout=5)
            try:
                return identity.L0IdentityForge(directory).forge_identity("fixture-passphrase")
            except FileExistsError:
                return None

        with ThreadPoolExecutor(max_workers=6) as pool:
            outcomes = list(pool.map(create, range(6)))
        winners = [value for value in outcomes if value is not None]
        assert len(winners) == 1
        assert identity.L0IdentityForge(directory).load_identity("fixture-passphrase") == winners[0]
        assert sorted(p.name for p in directory.iterdir()) == ["master_seed.enc"]
        assert directory.joinpath("master_seed.enc").stat().st_mode & 0o777 == 0o600


def test_c0337_failed_write_publishes_no_partial_seed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    forge = identity.L0IdentityForge(tmp_path / "identity")
    def fail_sync(_fd):
        raise OSError("fixture sync failure")

    monkeypatch.setattr(identity.os, "fsync", fail_sync)
    with pytest.raises(OSError, match="fixture sync failure"):
        forge.forge_identity("fixture-passphrase")
    assert not forge.seed_path.exists()
    assert list(forge.storage_dir.iterdir()) == []


def test_c0337_wrong_passphrase_preserves_original(tmp_path: Path) -> None:
    forge = identity.L0IdentityForge(tmp_path / "identity")
    original = forge.forge_identity("fixture-passphrase")
    before = forge.seed_path.read_bytes()
    with pytest.raises(ValueError, match="Decryption Failed"):
        forge.load_identity("wrong-fixture-passphrase")
    assert forge.seed_path.read_bytes() == before
    assert forge.load_identity("fixture-passphrase") == original


def _metadata_process_writer(directory, actor, barrier):
    os.environ["CORTEX_DB_PATH"] = directory
    os.environ["CORTEX_TESTING"] = "1"
    keys.keyring = None
    manager = keys.KeyManager("fixture-process")
    barrier.wait(timeout=15)
    barrier.wait(timeout=15)
    manager.generate_and_store_key(actor)


def test_c0345_process_writers_preserve_revocations_and_each_other(tmp_path: Path) -> None:
    context = multiprocessing.get_context("spawn")
    for round_number in range(3):  # one warmup plus two independently reopened bursts
        store = tmp_path / f"process-store-{round_number}"
        os.environ["CORTEX_DB_PATH"] = str(store)
        owner = keys.KeyManager("fixture-process")
        owner.generate_and_store_key("revoked-anchor")
        barrier = context.Barrier(5)
        workers = [context.Process(target=_metadata_process_writer, args=(str(store), f"actor-{i}", barrier)) for i in range(4)]
        for process in workers:
            process.start()
        try:
            barrier.wait(timeout=15)
            assert owner.revoke_key("revoked-anchor")
            barrier.wait(timeout=15)
            for process in workers:
                process.join(timeout=15)
                assert process.exitcode == 0
        finally:
            for process in workers:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=5)
        final = keys.KeyManager("fixture-process")
        assert final.is_revoked("revoked-anchor")
        assert all(final.get_public_key_b64(f"actor-{i}") for i in range(4))
        assert len(json.loads(final.db_path.read_text())) == 5


def test_c0345_replace_failure_preserves_complete_previous_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = keys.KeyManager("fixture-io-error")
    manager.generate_and_store_key("actor-a")
    before = manager.db_path.read_bytes()
    def fail_replace(*_args, **_kwargs):
        raise OSError("fixture replacement failure")

    monkeypatch.setattr(keys.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replacement failure"):
        manager.generate_and_store_key("actor-b")
    assert manager.db_path.read_bytes() == before
    assert manager.get_private_key_b64("actor-b") is None
    assert not list(manager.db_path.parent.glob("*.tmp"))


def test_c0345_failed_rotation_cannot_return_mismatched_private_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = keys.KeyManager("fixture-rotation-error")
    old_public = manager.generate_and_store_key("actor-a")
    def fail_replace(*_args, **_kwargs):
        raise OSError("fixture replacement failure")

    monkeypatch.setattr(keys.os, "replace", fail_replace)
    with pytest.raises(OSError):
        manager.generate_and_store_key("actor-a")
    assert manager.get_public_key_b64("actor-a") == old_public
    assert manager.get_private_key_b64("actor-a") is None


def test_c0345_corrupt_metadata_rejects_without_overwriting() -> None:
    manager = keys.KeyManager("fixture-corrupt")
    manager.db_path.write_bytes(b"{corrupt")
    with pytest.raises(json.JSONDecodeError):
        manager.generate_and_store_key("actor-a")
    assert manager.db_path.read_bytes() == b"{corrupt"


def test_c0345_symlink_metadata_preserves_neighbor(tmp_path: Path) -> None:
    manager = keys.KeyManager("fixture-symlink")
    neighbor = tmp_path / "neighbor"
    neighbor.write_bytes(b"preserve")
    manager.db_path.symlink_to(neighbor)
    with pytest.raises(OSError):
        manager.generate_and_store_key("actor-a")
    assert neighbor.read_bytes() == b"preserve"


def configured_sealer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    module = importlib.import_module("scripts.c5_l1_ledger.seal_bounty_aeon")
    monkeypatch.setattr(module, "_ROOT", tmp_path)
    monkeypatch.setattr(module, "extract_claims_for_sealing", lambda _: [{
        "domain": "fixture", "claim_id": "fixture-1", "advisory_id": "fixture-advisory",
        "payload_hash": "1" * 64, "attestation_merkle_root": "2" * 64,
    }])
    class Tree:
        root = "a" * 64
        tree_levels = [[root]]

        def __init__(self, _leaves):
            pass

        def get_inclusion_proof(self, _index):
            return []

        @staticmethod
        def verify_inclusion_proof(*_args):
            return True

    monkeypatch.setattr(module, "ConformalMerkleTree", Tree)
    monkeypatch.setattr(module, "MerkleCausalAnchor", lambda: SimpleNamespace(
        generate_hardware_pcr_quote=lambda _: {
            "hardware_enclave": "SOFTWARE_FIXTURE", "pcr_value": "b" * 64,
            "platform": "fixture", "hardware_uuid": "fixture-only",
        }
    ))
    monkeypatch.setattr(module, "RFC3161Client", lambda: SimpleNamespace(request_timestamp=lambda _: None))
    return module


@pytest.mark.parametrize("error", [ValueError("decryption failed"), json.JSONDecodeError("corrupt", "!", 0)])
def test_c0533_identity_load_error_never_forges_or_publishes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: Exception,
) -> None:
    module = configured_sealer(monkeypatch, tmp_path)
    marker = tmp_path / "original-identity"
    marker.write_bytes(b"original-identity-bytes")
    class Forge:
        def __init__(self, **_kwargs):
            pass

        def load_identity(self, _passphrase):
            raise error

        def forge_identity(self, _passphrase):
            marker.write_bytes(b"identity-replaced")
            raise AssertionError("forging was not permitted")

    monkeypatch.setattr(module, "L0IdentityForge", Forge)
    def forbidden_dispatch():
        raise AssertionError("identity error must abort before quote/TSA dispatch")

    monkeypatch.setattr(module, "MerkleCausalAnchor", forbidden_dispatch)
    monkeypatch.setattr(module, "RFC3161Client", forbidden_dispatch)
    with pytest.raises(type(error)):
        module.seal_bounty_aeon("fixture-db", "FIXTURE-AEON", str(tmp_path / "output"))
    assert marker.read_bytes() == b"original-identity-bytes"
    assert not (tmp_path / "output").exists()


def test_c0533_missing_identity_can_be_created_exclusively(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    module = configured_sealer(monkeypatch, tmp_path)
    payload = identity.L0IdentityForge(tmp_path / "fixture-key").forge_identity("fixture-passphrase")
    calls = []
    class Forge:
        def __init__(self, **_kwargs):
            pass

        def load_identity(self, _passphrase):
            raise FileNotFoundError("missing fixture identity")

        def forge_identity(self, _passphrase):
            calls.append("create")
            return payload

    monkeypatch.setattr(module, "L0IdentityForge", Forge)
    artifact = module.seal_bounty_aeon("fixture-db", "FIXTURE-AEON", str(tmp_path / "output"))
    assert calls == ["create"]
    assert base64.b64decode(artifact["sovereign_identity"]["l0_public_key_b64"]) == base64.b64decode(payload.public_key_b64)


def test_producer_v2_manifest_authenticates_complete_body_with_external_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from babylon60.attestation import conformal_tree

    module = configured_sealer(monkeypatch, tmp_path)
    monkeypatch.setattr(conformal_tree, "MerkleCausalAnchor", lambda: SimpleNamespace(
        get_hardware_identity=lambda: {"uuid": "fixture-only"}
    ))
    module.seal_bounty_aeon("fixture-db", "FIXTURE-AEON", str(tmp_path / "output"))
    path = tmp_path / "output" / "fixture_aeon.json"
    artifact = json.loads(path.read_text())
    public_key = artifact["sovereign_identity"]["l0_public_key_b64"]
    trusted = conformal_tree.AeonVerifier.verify_manifest(path, expected_public_key_b64=public_key)
    assert trusted["overall_valid"]
    assert trusted["verification_scope"] == "AUTHENTICATED_MANIFEST_ONLY"
    assert not trusted["hardware_attestation_verified"]
    assert not conformal_tree.AeonVerifier.verify_manifest(path)["overall_valid"]
    artifact["total_claims_sealed"] += 1
    path.write_text(json.dumps(artifact))
    assert not conformal_tree.AeonVerifier.verify_manifest(path, expected_public_key_b64=public_key)["overall_valid"]
