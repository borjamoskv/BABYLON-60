"""Independent adversarial identity controls; all stores are fixture-owned."""

from __future__ import annotations

import importlib
import json
import os
from types import SimpleNamespace
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from babylon60.crypto import identity, keys


@pytest.fixture(autouse=True)
def own_stores(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CORTEX_DB_PATH", str(tmp_path / "store"))
    monkeypatch.setenv("CORTEX_TESTING", "1")
    monkeypatch.setattr(keys, "keyring", None)
    monkeypatch.setattr(keys.KeyManager, "_fallback_keyring", {})
    monkeypatch.setattr(identity, "ARGON2_MEMORY_COST", 1024)
    monkeypatch.setattr(identity, "ARGON2_TIME_COST", 1)
    monkeypatch.setattr(identity, "ARGON2_PARALLELISM", 1)


def test_identity_temporary_collision_preserves_foreign_inode(monkeypatch, tmp_path):
    directory = tmp_path / "identity"
    directory.mkdir()
    token = uuid.UUID(int=79)
    foreign = directory / f".master-seed-{token.hex}.tmp"
    foreign.write_bytes(b"foreign-owned-fixture")
    before = foreign.stat().st_ino
    monkeypatch.setattr(identity.uuid, "uuid4", lambda: token)
    with pytest.raises(FileExistsError):
        identity.L0IdentityForge(directory).forge_identity("fixture-passphrase")
    assert foreign.read_bytes() == b"foreign-owned-fixture"
    assert foreign.stat().st_ino == before
    assert not (directory / "master_seed.enc").exists()


def test_identity_directory_sync_failure_has_no_false_success(monkeypatch, tmp_path):
    forge = identity.L0IdentityForge(tmp_path / "identity")
    original = os.fsync
    calls = []

    def fail_first_directory(fd):
        calls.append(fd)
        if len(calls) == 2:
            raise OSError("fixture publication directory sync failed")
        return original(fd)

    with monkeypatch.context() as patch:
        patch.setattr(identity.os, "fsync", fail_first_directory)
        with pytest.raises(OSError, match="publication directory sync"):
            forge.forge_identity("fixture-passphrase")
    assert len(calls) >= 2
    assert forge.load_identity("fixture-passphrase").seed_bytes
    assert sorted(p.name for p in forge.storage_dir.iterdir()) == ["master_seed.enc"]


@pytest.mark.parametrize("dangling", [False, True])
def test_identity_load_never_follows_seed_symlink(tmp_path, dangling):
    forge = identity.L0IdentityForge(tmp_path / "identity")
    forge.storage_dir.mkdir()
    victim = tmp_path / "victim"
    if not dangling:
        victim.write_bytes(b"preserve-victim")
    forge.seed_path.symlink_to(victim)
    with pytest.raises(OSError):
        forge.load_identity("fixture-passphrase")
    assert forge.seed_path.is_symlink()
    assert not victim.exists() if dangling else victim.read_bytes() == b"preserve-victim"


def test_identity_rejects_symlink_storage_directory(tmp_path):
    victim = tmp_path / "actual-directory"
    victim.mkdir()
    alias = tmp_path / "alias-directory"
    alias.symlink_to(victim, target_is_directory=True)
    with pytest.raises(OSError):
        identity.L0IdentityForge(alias).forge_identity("fixture-passphrase")
    assert list(victim.iterdir()) == []


def test_revoke_persists_even_when_backend_delete_fails(monkeypatch):
    private = {}

    class FixtureKeyring:
        @staticmethod
        def set_password(service, actor, value):
            private[service, actor] = value

        @staticmethod
        def get_password(service, actor):
            return private.get((service, actor))

        @staticmethod
        def delete_password(service, actor):
            raise RuntimeError("fixture keyring refuses deletion")

    monkeypatch.setattr(keys, "keyring", FixtureKeyring)
    owner = keys.KeyManager("independent-revocation")
    owner.generate_and_store_key("actor")
    stale = keys.KeyManager("independent-revocation")
    assert stale.get_private_key_b64("actor") is not None
    assert owner.revoke_key("actor")
    assert private
    assert stale.get_private_key_b64("actor") is None
    assert keys.KeyManager("independent-revocation").is_revoked("actor")


def test_failed_revocation_reports_error_and_keeps_old_metadata(monkeypatch):
    owner = keys.KeyManager("independent-failed-revoke")
    owner.generate_and_store_key("actor")
    previous = owner.db_path.read_bytes()

    def fail_replace(*args, **kwargs):
        raise OSError("fixture metadata publication blocked")

    with monkeypatch.context() as patch:
        patch.setattr(keys.os, "replace", fail_replace)
        with pytest.raises(OSError, match="metadata publication blocked"):
            owner.revoke_key("actor")
    assert owner.db_path.read_bytes() == previous
    assert not keys.KeyManager("independent-failed-revoke").is_revoked("actor")
    assert owner.get_private_key_b64("actor") is not None


def test_private_key_mismatch_is_not_usable(monkeypatch):
    owner = keys.KeyManager("independent-mismatch")
    owner.generate_and_store_key("actor")
    other = keys.KeyManager("independent-other")
    other.generate_and_store_key("actor")
    keys.KeyManager._fallback_keyring[owner.service_name]["actor"] = keys.KeyManager._fallback_keyring[other.service_name]["actor"]
    assert owner.get_private_key_b64("actor") is None


def test_corrupt_identity_fails_before_quote_or_timestamp(monkeypatch, tmp_path):
    module = importlib.import_module("scripts.c5_l1_ledger.seal_bounty_aeon")
    monkeypatch.setattr(module, "_ROOT", tmp_path)
    calls = []
    monkeypatch.setattr(module, "extract_claims_for_sealing", lambda _: [{
        "domain": "fixture", "claim_id": "fixture-claim", "advisory_id": "fixture-advisory",
        "payload_hash": "1" * 64, "attestation_merkle_root": "2" * 64,
    }])
    monkeypatch.setattr(module, "MerkleCausalAnchor", lambda: SimpleNamespace(
        generate_hardware_pcr_quote=lambda _: calls.append("quote") or {
            "hardware_enclave": "SOFTWARE_FIXTURE", "pcr_value": "0" * 64,
            "platform": "fixture", "hardware_uuid": "fixture-uuid",
        },
    ))
    monkeypatch.setattr(module, "RFC3161Client", lambda: SimpleNamespace(
        request_timestamp=lambda _: calls.append("timestamp") or None,
    ))

    class CorruptForge:
        def __init__(self, **kwargs):
            pass

        def load_identity(self, passphrase):
            raise json.JSONDecodeError("fixture corrupt identity", "!", 0)

        def forge_identity(self, passphrase):
            calls.append("forge")
            raise AssertionError("corrupt identities cannot be replaced")

    monkeypatch.setattr(module, "L0IdentityForge", CorruptForge)
    with pytest.raises(json.JSONDecodeError):
        module.seal_bounty_aeon("fixture-db", "FIXTURE-FAILURE", str(tmp_path / "output"))
    assert not calls
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("failure", ["bad-json", "wrong-passphrase"])
def test_actual_seed_failure_preserves_identity_and_avoids_external_calls(monkeypatch, tmp_path, failure):
    module = importlib.import_module("scripts.c5_l1_ledger.seal_bounty_aeon")
    monkeypatch.setattr(module, "_ROOT", tmp_path)
    forge = identity.L0IdentityForge(tmp_path / ".babylon60/identity")
    forge.forge_identity("different-fixture-passphrase")
    if failure == "bad-json":
        forge.seed_path.write_bytes(b"{fixture-invalid-json")
    previous = forge.seed_path.read_bytes()
    calls = []
    monkeypatch.setattr(module, "extract_claims_for_sealing", lambda _: [{
        "domain": "fixture", "claim_id": "fixture-real-seed", "advisory_id": "fixture-advisory",
        "payload_hash": "1" * 64, "attestation_merkle_root": "2" * 64,
    }])
    monkeypatch.setattr(module, "MerkleCausalAnchor", lambda: calls.append("quote") or None)
    monkeypatch.setattr(module, "RFC3161Client", lambda: calls.append("timestamp") or None)
    with pytest.raises((ValueError, json.JSONDecodeError)):
        module.seal_bounty_aeon("fixture-db", "FIXTURE-REAL-SEED", str(tmp_path / "output"))
    assert calls == []
    assert forge.seed_path.read_bytes() == previous
    assert not (tmp_path / "output").exists()


def test_metadata_multithread_bursts_keep_all_public_keys_and_revocations():
    for round_number in range(5):
        name = f"independent-burst-{round_number}"
        owner = keys.KeyManager(name)
        expected = {f"revoked-{i}": owner.generate_and_store_key(f"revoked-{i}") for i in range(6)}
        barrier = threading.Barrier(9)

        def writer(index):
            stale = keys.KeyManager(name)
            barrier.wait(timeout=10)
            public = stale.generate_and_store_key(f"writer-{index}")
            return f"writer-{index}", public

        def revoker():
            stale = keys.KeyManager(name)
            barrier.wait(timeout=10)
            for i in range(6):
                assert stale.revoke_key(f"revoked-{i}")

        with ThreadPoolExecutor(max_workers=9) as pool:
            work = [pool.submit(writer, i) for i in range(8)]
            revocation = pool.submit(revoker)
            for future in work:
                actor, public = future.result(timeout=10)
                expected[actor] = public
            revocation.result(timeout=10)
        fresh = keys.KeyManager(name)
        assert len(json.loads(fresh.db_path.read_text())) == 14
        assert all(fresh.get_public_key_b64(actor) == value for actor, value in expected.items())
        assert all(fresh.is_revoked(f"revoked-{i}") for i in range(6))
        assert all(fresh.get_private_key_b64(f"revoked-{i}") is None for i in range(6))
