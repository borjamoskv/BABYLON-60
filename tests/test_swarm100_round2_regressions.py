"""Security regressions for round 2; only disposable data and software keys."""

import copy
import hashlib
import importlib.util
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from threading import Barrier, Event
from types import SimpleNamespace

import aiosqlite
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from babylon60.autodidact.crystal_compiler import CrystalCompiler
from babylon60.autodidact.types import Justification, JustifiedStatement, Modality, Statement
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger
from babylon60.compliance_exporter.m0_evidence_pack import M0EvidencePackCompiler
from babylon60.crypto.aes import CortexEncrypter
from babylon60.crypto.shredder import CryptoShredder
from babylon60.memory.governance import GovernanceViolationError, MemoryGovernanceEngine
from babylon60.verifier.cli import main, parse_crl_arg
from babylon60.verifier.standalone_verify import (
    build_cortex_merkle_tree,
    canonical_json,
    verify_compliance_certificate,
    verify_offline_evidence,
)

ROOT = Path(__file__).absolute().parents[1]


def signed_certificate(root):
    certificate = {
        "certificate_id": "revoked-fixture",
        "system_identifier": "fixture",
        "operator": "fixture",
        "issued_at": "2026-01-01T00:00:00+00:00",
        "valid_until": "2099-01-01T00:00:00+00:00",
        "global_merkle_root": root,
        "articles_compliance": {},
    }
    key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    signature = key.sign(canonical_json(certificate).encode())
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    certificate["signature"] = {"public_key": public.hex(), "signature": signature.hex(), "algorithm": "Ed25519"}
    return certificate


@pytest.fixture
def compiler(tmp_path):
    claims = tmp_path / "claims.toml"
    claims.write_text('[claim.INV_OMEGA_complete_mediation]\nstatus="verified_local"\n')
    return M0EvidencePackCompiler(repo_root=tmp_path, claims_toml_path=claims, signing_seed_hex="ab" * 32)


def test_v01_no_unobserved_campaigns(compiler, tmp_path):
    pack = tmp_path / "pack"
    manifest = compiler.compile_pack(pack)
    results = json.loads((pack / "evidence/nemesis-results.json").read_text())
    assert results["campaigns"] == {}
    assert manifest["metrics"]["supported_within_scope"] == 0
    assert manifest["metrics"]["untested"] == 1
    assert manifest["ledger_summary"]["evidence_origin"] == "SYNTHETIC_DEMONSTRATION"


@pytest.mark.parametrize("invalid", ["claims", "ledger", "valid_inputs"])
def test_v02_existing_output_is_never_deleted(compiler, tmp_path, invalid):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "sentinel"
    sentinel.write_bytes(b"preserve previous output")
    kwargs = {}
    if invalid == "claims":
        compiler.claims_toml_path = tmp_path / "missing.toml"
    elif invalid == "ledger":
        kwargs["existing_ledger_path"] = tmp_path / "missing.sqlite"
    with pytest.raises((ValueError, FileExistsError, FileNotFoundError)):
        compiler.compile_pack(output, **kwargs)
    assert sentinel.read_bytes() == b"preserve previous output"


@pytest.mark.parametrize("content", ["{malformed", "{}", "null", '{"revocations":"cert"}', "[17]", '[""]'])
def test_v03_crl_rejects_bad_file(tmp_path, content):
    crl = tmp_path / "revoked.json"
    crl.write_text(content)
    with pytest.raises(ValueError):
        parse_crl_arg(str(crl))


def test_v03_crl_missing_file_and_controls(tmp_path):
    with pytest.raises((ValueError, OSError)):
        parse_crl_arg(str(tmp_path / "missing.json"))
    assert parse_crl_arg("cert-a,cert-b") == ["cert-a", "cert-b"]
    for data in ([], ["cert-a"], {"revocations": ["cert-a"]}):
        crl = tmp_path / "crl.json"
        crl.write_text(json.dumps(data))
        assert parse_crl_arg(str(crl)) == ([] if data == [] else ["cert-a"])


def test_v03_cli_rejects_crl_without_traceback(tmp_path, capsys):
    cert = tmp_path / "cert.json"
    cert.write_text("{}")
    crl = tmp_path / "crl.json"
    crl.write_text("{bad")
    assert main(["--cert", str(cert), "--crl", str(crl), "--json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert not result["valid"]
    assert "CRL" in result["detail"]


def test_v03_signed_revoked_certificate_remains_rejected(tmp_path, capsys):
    cert = tmp_path / "cert.json"
    cert.write_text(json.dumps(signed_certificate("0" * 64)))
    assert main(["--cert", str(cert), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["signature_valid"]
    crl = tmp_path / "crl.json"
    for data in ('["revoked-fixture"]', "{malformed"):
        crl.write_text(data)
        assert main(["--cert", str(cert), "--crl", str(crl), "--json"]) == 1
        assert not json.loads(capsys.readouterr().out)["valid"]


@pytest.mark.parametrize("envelope", [False, True])
def test_v04_payload_hash_must_commit_content(tmp_path, envelope):
    payload = {"payload": {"amount": 10}}
    digest = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
    event = {**payload, "entry_hash": digest}
    ledger = tmp_path / "ledger.json"
    root = build_cortex_merkle_tree([digest])

    def write():
        ledger.write_text(json.dumps({"events": [event]} if envelope else [event]))

    write()
    assert verify_offline_evidence(ledger, root)["verified"]
    certificate = signed_certificate(root)
    assert verify_compliance_certificate(certificate, ledger)["valid"]
    event["payload"]["amount"] = 999999
    write()
    assert not verify_offline_evidence(ledger, root)["verified"]
    assert not verify_compliance_certificate(certificate, ledger)["valid"]


@pytest.mark.parametrize(
    "data",
    [{}, [17], {"events": [None]}, {"leaves": ["bad"]}, {"leaves": ["a" * 64], "events": [{"payload": "unbound"}]}],
)
def test_v04_invalid_json_shape_rejected(tmp_path, data):
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps(data))
    assert not verify_offline_evidence(ledger)["verified"]


def test_v04_hash_only_scope_is_explicit(tmp_path):
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"leaves": ["a" * 64]}))
    result = verify_offline_evidence(ledger, build_cortex_merkle_tree(["a" * 64]))
    assert result["verified"]
    assert result["verification_scope"] == "HASH_COMMITMENTS_ONLY"


def engines(path, separate=False):
    pair = [
        MemoryGovernanceEngine(path, ledger=CortexPersistLedger(path.with_name("ledger.sqlite")) if separate else None)
        for _ in range(2)
    ]
    for engine in pair:
        engine.register_principal_key("fixture", "operator", b"fixture-principal-key")
    return pair


@pytest.mark.parametrize("first", ["add", "revoke"])
@pytest.mark.parametrize("separate", [False, True])
def test_v05_serializes_closure_and_insertion(tmp_path, monkeypatch, first, separate):
    a, b = engines(tmp_path / "governance.sqlite", separate)
    parent = a.add_record(tenant_id="fixture", principal="operator", content="parent")
    entered, competing_started, release = Event(), Event(), Event()
    engine = a if first == "add" else b
    original = engine.ledger.append_event

    def pause(event, **kwargs):
        entered.set()
        assert release.wait(4)
        return original(event, **kwargs)

    monkeypatch.setattr(engine.ledger, "append_event", pause)

    def add():
        try:
            return a.add_record(tenant_id="fixture", principal="operator", content="child", parents=[parent.record_id])
        except GovernanceViolationError:
            return None

    def revoke():
        return b.revoke_record(record_id=parent.record_id, tenant_id="fixture", principal="operator")

    def second():
        competing_started.set()
        return (revoke if first == "add" else add)()

    with ThreadPoolExecutor(max_workers=2) as pool:
        one = pool.submit(add if first == "add" else revoke)
        assert entered.wait(4)
        two = pool.submit(second)
        assert competing_started.wait(4)
        # The competing transaction cannot finish while the first writer is paused.
        try:
            from concurrent.futures import TimeoutError

            with pytest.raises(TimeoutError):
                two.result(timeout=0.1)
        finally:
            release.set()
        one.result(timeout=8)
        two.result(timeout=8)
    with closing(sqlite3.connect(a.db_path)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM cortex_memory_records WHERE status='ACTIVE'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM cortex_memory_blobs").fetchone()[0] == 0
    assert a.ledger.verify_integrity()


def test_v05_record_and_receipt_rollback_together(tmp_path, monkeypatch):
    a, _ = engines(tmp_path / "governance.sqlite")
    original = a.ledger.append_event

    def fail_after_append(event, **kwargs):
        original(event, **kwargs)
        raise RuntimeError("injected failure after ledger insert")

    monkeypatch.setattr(a.ledger, "append_event", fail_after_append)
    with pytest.raises(RuntimeError):
        a.add_record(tenant_id="fixture", principal="operator", content="never committed")
    with closing(sqlite3.connect(a.db_path)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM cortex_memory_records").fetchone()[0] == 0


def test_v05_revocation_receipt_rollback_together(tmp_path, monkeypatch):
    a, _ = engines(tmp_path / "governance.sqlite")
    parent = a.add_record(tenant_id="fixture", principal="operator", content="retained")
    original = a.ledger.append_event

    def fail_after_append(event, **kwargs):
        original(event, **kwargs)
        raise RuntimeError("injected revocation failure")

    monkeypatch.setattr(a.ledger, "append_event", fail_after_append)
    with pytest.raises(RuntimeError):
        a.revoke_record(record_id=parent.record_id, tenant_id="fixture", principal="operator")
    assert a.get_record(parent.record_id, tenant_id="fixture").content == "retained"
    with closing(sqlite3.connect(a.db_path)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0] == 1


def test_v05_concurrent_revocation_stress_with_warmup(tmp_path):
    """5 warmup rounds, then 20 rounds of 6 concurrent derivations and revocation."""
    a, b = engines(tmp_path / "stress.sqlite")
    with ThreadPoolExecutor(max_workers=7) as pool:
        for iteration in range(25):
            parent = a.add_record(tenant_id="fixture", principal="operator", content=f"parent {iteration}")
            start = Barrier(7)

            def derive(index):
                start.wait(timeout=5)
                try:
                    a.add_record(
                        tenant_id="fixture",
                        principal="operator",
                        content=f"child {iteration}:{index}",
                        parents=[parent.record_id],
                    )
                except GovernanceViolationError:
                    pass  # A completed revocation must reject derivation.

            def revoke():
                start.wait(timeout=5)
                b.revoke_record(record_id=parent.record_id, tenant_id="fixture", principal="operator")

            pending = [pool.submit(derive, i) for i in range(6)] + [pool.submit(revoke)]
            for future in pending:
                future.result(timeout=10)
            with closing(sqlite3.connect(a.db_path)) as conn:
                assert (
                    conn.execute("SELECT COUNT(*) FROM cortex_memory_records WHERE status='ACTIVE'").fetchone()[0] == 0
                )
                assert conn.execute("SELECT COUNT(*) FROM cortex_memory_blobs").fetchone()[0] == 0
    assert a.ledger.verify_integrity()


@pytest.mark.parametrize(
    "field,value", [("content", "five sides"), ("modality", "deontic"), ("obligations", ["provenance"])]
)
def test_v06_recompute_statement_content(field, value):
    compiler = CrystalCompiler()
    statement = JustifiedStatement(Statement("three sides", Modality.EPISTEMIC), Justification("Observation"))
    crystal = compiler.compile("fixture", "fixture", [statement]).to_dict()
    assert compiler.verify_crystal_integrity(crystal)[0]
    tampered = copy.deepcopy(crystal)
    tampered["statements"][0][field] = value
    assert not compiler.verify_crystal_integrity(tampered)[0]


def test_v06_markdown_root_is_not_integrity(tmp_path):
    path = tmp_path / "crystal.md"
    path.write_text("Merkle Root (SHA-256): `" + "a" * 64 + "`")
    assert not CrystalCompiler.verify_crystal_integrity(str(path))[0]


def test_v08_shredding_does_not_claim_success_for_recoverable_ciphertext(tmp_path, monkeypatch):
    key = bytes(range(32))
    encrypter = CortexEncrypter(key, strict_mode=True)
    monkeypatch.setattr("babylon60.crypto.aes._default_encrypter_instance", encrypter)
    ciphertext = encrypter.encrypt_str("public fixture", "fixture")
    with closing(sqlite3.connect(tmp_path / "shred.sqlite")) as conn:
        shredder = CryptoShredder(conn)
        result = shredder.shred_fact(42, "fixture")
        assert not result.success
        assert "UNSUPPORTED" in result.error
        assert not shredder.is_shredded(42, "fixture")
        assert not shredder.audit_shredding()["compliant"]
    assert CortexEncrypter(key, strict_mode=True).decrypt_str(ciphertext, "fixture") == "public fixture"


@pytest.mark.asyncio
async def test_v08_async_shredding_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr("babylon60.crypto.aes._default_encrypter_instance", CortexEncrypter(bytes(range(32))))
    async with aiosqlite.connect(tmp_path / "shred.sqlite") as conn:
        shredder = CryptoShredder(conn)
        await shredder._ensure_schema_async()
        result = await shredder.shred_fact_async(42, "fixture")
        assert not result.success
        assert not await shredder.is_shredded_async(42, "fixture")


def test_v08_historical_marker_is_not_proof_of_erasure(tmp_path, monkeypatch):
    def forbid_operator_key():
        raise AssertionError("Erasure refusal must not resolve operator credentials")

    monkeypatch.setattr("babylon60.crypto.aes.get_default_encrypter", forbid_operator_key)
    with closing(sqlite3.connect(tmp_path / "shred.sqlite")) as conn:
        shredder = CryptoShredder(conn)
        conn.execute("INSERT INTO shredded_keys (fact_id, tenant_id) VALUES (42, 'fixture')")
        conn.commit()
        result = shredder.shred_fact(42, "fixture")
        assert not result.success and not result.was_already_shredded
        assert not shredder.audit_shredding()["compliant"]


def load_script(path):
    spec = importlib.util.spec_from_file_location("round2_script", ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def consolidation(tmp_path, monkeypatch):
    module = load_script("scripts/c5_cortex/consolidate_dbs.py")
    root, central = tmp_path / "repo", tmp_path / "central"
    root.mkdir()
    central.mkdir()
    monkeypatch.setattr(module, "REPO_ROOT", root)
    monkeypatch.setattr(module, "CENTRAL_DIR", central)
    return module


def make_db(path, value):
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE witness (value TEXT)")
        conn.execute("INSERT INTO witness VALUES (?)", (value,))
        conn.commit()


def rows(path):
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute("SELECT value FROM witness").fetchall()


def test_v09_divergent_and_unknown_databases_survive(consolidation):
    source = consolidation.REPO_ROOT / "cortex.db"
    dest = consolidation.CENTRAL_DIR / "cortex.db"
    other = consolidation.REPO_ROOT / "unrecognized.db"
    make_db(source, "source")
    make_db(dest, "destination")
    make_db(other, "unrecognized")
    consolidation.consolidate_dbs()
    assert source.exists() and other.exists()
    assert rows(source) == [("source",)]
    assert rows(dest) == [("destination",)]
    assert rows(other) == [("unrecognized",)]


def test_v10_backup_includes_committed_wal_and_retains_source(consolidation):
    source = consolidation.REPO_ROOT / "cortex.db"
    dest = consolidation.CENTRAL_DIR / "cortex.db"
    with closing(sqlite3.connect(source)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute("CREATE TABLE witness (value TEXT)")
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("INSERT INTO witness VALUES ('wal-only')")
        conn.commit()
        consolidation.consolidate_dbs()
        assert rows(dest) == [("wal-only",)]
        assert source.exists()
        conn.execute("INSERT INTO witness VALUES ('later')")
        conn.commit()
        assert rows(source) == [("wal-only",), ("later",)]


def test_v10_destination_race_preserves_both_databases(consolidation, monkeypatch):
    source = consolidation.REPO_ROOT / "cortex.db"
    dest = consolidation.CENTRAL_DIR / "cortex.db"
    make_db(source, "source")
    link = consolidation.os.link

    def race(src, dst):
        make_db(dest, "racing destination")
        link(src, dst)

    monkeypatch.setattr(consolidation.os, "link", race)
    consolidation.consolidate_dbs()
    assert rows(source) == [("source",)]
    assert rows(dest) == [("racing destination",)]


def test_v10_invalid_database_is_not_published(consolidation):
    source = consolidation.REPO_ROOT / "cortex.db"
    source.write_bytes(b"not sqlite")
    with pytest.raises(sqlite3.DatabaseError):
        consolidation.consolidate_dbs()
    assert source.read_bytes() == b"not sqlite"
    assert not (consolidation.CENTRAL_DIR / "cortex.db").exists()


@pytest.fixture(params=[
    "tools/skill_library/global/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py",
    "tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py",
])
def browser(tmp_path, monkeypatch, request):
    module = load_script(request.param)
    profile = tmp_path / "Chrome" / "Default"
    (profile / "Extensions").mkdir(parents=True)
    monkeypatch.setattr(module, "CHROME_BASE", str(profile.parent))
    return module, profile


@pytest.mark.parametrize("kind", ["relative", "absolute", "invalid", "symlink"])
def test_v11_purge_confines_deletion(browser, tmp_path, kind):
    module, profile = browser
    victim = profile / "victim"
    victim.mkdir()
    sentinel = victim / "sentinel"
    sentinel.write_text("preserve")
    ext_id = {"relative": "../victim", "absolute": str(victim), "invalid": ".", "symlink": "a" * 32}[kind]
    if kind == "symlink":
        (profile / "Extensions").rmdir()
        (profile / "Extensions").symlink_to(victim, target_is_directory=True)
        (victim / ext_id).mkdir()
        (victim / ext_id / "child").write_text("preserve")
    with pytest.raises((ValueError, OSError)):
        module.cmd_purge(SimpleNamespace(id=ext_id))
    assert sentinel.read_text() == "preserve"
    if kind == "symlink":
        assert (victim / ext_id / "child").exists()


def test_v11_valid_extension_purge(browser):
    module, profile = browser
    ext_id = "a" * 32
    target = profile / "Extensions" / ext_id
    target.mkdir()
    (target / "manifest.json").write_text("{}")
    prefs = profile / "Secure Preferences"
    prefs.write_text(json.dumps({"extensions": {"settings": {ext_id: {}, "b" * 32: {"keep": True}}}}))
    standard = profile / "Preferences"
    standard.write_text(json.dumps({"extensions": {"install_signature": {"ids": [ext_id, "b" * 32]}}}))
    module.cmd_purge(SimpleNamespace(id=ext_id))
    assert not target.exists()
    assert json.loads(prefs.read_text())["extensions"]["settings"] == {"b" * 32: {"keep": True}}
    assert json.loads(standard.read_text())["extensions"]["install_signature"]["ids"] == ["b" * 32]
    assert len(list(profile.glob("*.c5_bak-*"))) == 2


@pytest.mark.parametrize("target_name", ["extension", "preferences", "profile"])
def test_v11_rejects_symlink_targets(browser, tmp_path, target_name):
    module, profile = browser
    ext_id = "a" * 32
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("preserve")
    if target_name == "extension":
        (profile / "Extensions" / ext_id).symlink_to(outside, target_is_directory=True)
    elif target_name == "preferences":
        (profile / "Preferences").symlink_to(sentinel)
    else:
        (profile / "Extensions").rmdir()
        profile.rmdir()
        profile.symlink_to(outside, target_is_directory=True)
    with pytest.raises((ValueError, OSError)):
        module.cmd_purge(SimpleNamespace(id=ext_id))
    assert sentinel.read_text() == "preserve"
