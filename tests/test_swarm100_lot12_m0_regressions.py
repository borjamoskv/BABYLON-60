"""C0175: signed M0 envelopes must cover every required evidence file."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from babylon60.compliance_exporter.m0_evidence_pack import (
    M0EvidencePackCompiler,
    _sign_ed25519_bytes,
)
from babylon60.verifier.standalone_verify import canonical_json, verify_m0_evidence_pack

SEED = "00" * 32
CONTENT_FILES = (
    "manifest.json",
    "claims.json",
    "scope.json",
    "environment.json",
    "evidence/ledger_l0.sqlite",
    "evidence/execution-trace.jsonl",
    "evidence/nemesis-results.json",
    "evidence/formal-proofs.json",
    "compliance/regulatory-matrix.json",
    "compliance/auditor-report.pdf",
    "README.md",
)


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    claims = tmp_path / "CLAIMS.toml"
    claims.write_text('[claim.fixture]\nstatus="untested"\n')
    compiler = M0EvidencePackCompiler(
        repo_root=tmp_path,
        claims_toml_path=claims,
        signing_seed_hex=SEED,
    )
    destination = tmp_path / "pack"
    compiler.compile_pack(destination)
    assert verify_m0_evidence_pack(destination)["valid"] is True
    return destination


def resign(pack: Path, digests: Any, checksums: bytes | None = None, *, omit_field: bool = False) -> None:
    """Sign a deliberately malformed envelope using only this fixture's key."""
    metadata_path = pack / "verification/verifier-metadata.json"
    metadata = json.loads(metadata_path.read_text())
    envelope = metadata["signing_envelope"]
    if omit_field:
        envelope.pop("file_digests", None)
    else:
        envelope["file_digests"] = digests
    if checksums is None:
        entries = digests.items() if isinstance(digests, dict) else ()
        checksums = "".join(f"{digest}  {name}\n" for name, digest in sorted(entries)).encode()
    (pack / "verification/checksums.sha256").write_bytes(checksums)
    envelope["checksums_sha256_digest"] = hashlib.sha256(checksums).hexdigest()
    payload = canonical_json(envelope).encode()
    public_key, signature = _sign_ed25519_bytes(payload, SEED)
    metadata["public_key"] = public_key
    metadata["signed_envelope_sha256"] = hashlib.sha256(payload).hexdigest()
    metadata_path.write_text(json.dumps(metadata))
    (pack / "verification/signature.sig").write_text(signature + "\n")


def digests_for(pack: Path) -> dict[str, str]:
    return json.loads((pack / "verification/verifier-metadata.json").read_text())["signing_envelope"]["file_digests"]


@pytest.mark.parametrize("omitted", CONTENT_FILES)
def test_c0175_every_required_content_digest_is_mandatory(pack: Path, omitted: str) -> None:
    digests = digests_for(pack)
    del digests[omitted]
    resign(pack, digests)
    result = verify_m0_evidence_pack(pack)
    assert result["valid"] is False
    assert result["checksums_valid"] is False


def test_c0175_missing_digest_field_rejected(pack: Path) -> None:
    resign(pack, {}, omit_field=True)
    assert verify_m0_evidence_pack(pack)["valid"] is False


@pytest.mark.parametrize("digests", [None, [], "invalid", 4, True])
def test_c0175_malformed_digest_map_returns_rejection(pack: Path, digests: Any) -> None:
    resign(pack, digests)
    assert verify_m0_evidence_pack(pack)["valid"] is False


@pytest.mark.parametrize("digest", [None, False, 42, [], {}, "g" * 64, "0" * 63, "0" * 65])
def test_c0175_invalid_digest_values_return_rejection(pack: Path, digest: Any) -> None:
    digests: dict[str, Any] = digests_for(pack)
    digests["environment.json"] = digest
    resign(pack, digests)
    assert verify_m0_evidence_pack(pack)["valid"] is False


@pytest.mark.parametrize("key", ["../outside", "/outside", "a/../../outside", "evidence/../claims.json"])
def test_c0175_unsafe_extra_paths_rejected_before_read(pack: Path, key: str, monkeypatch: pytest.MonkeyPatch) -> None:
    from babylon60.verifier import standalone_verify

    digests = digests_for(pack)
    digests[key] = "0" * 64
    resign(pack, digests)
    original = standalone_verify._sha256_file_standalone

    def confined(path: Path) -> str:
        assert path.is_relative_to(pack) and ".." not in path.parts
        return original(path)

    monkeypatch.setattr(standalone_verify, "_sha256_file_standalone", confined)
    assert verify_m0_evidence_pack(pack)["valid"] is False


def test_c0175_signed_non_utf8_checksums_return_rejection(pack: Path) -> None:
    resign(pack, digests_for(pack), checksums=b"\xff\xfe")
    assert verify_m0_evidence_pack(pack)["valid"] is False


def test_c0175_duplicate_checksums_rejected(pack: Path) -> None:
    digests = digests_for(pack)
    lines = "".join(f"{digest}  {name}\n" for name, digest in sorted(digests.items()))
    lines += f"{'0' * 64}  claims.json\n{digests['claims.json']}  claims.json\n"
    resign(pack, digests, checksums=lines.encode())
    assert verify_m0_evidence_pack(pack)["valid"] is False


def test_c0175_complete_pack_remains_accepted(pack: Path) -> None:
    result = verify_m0_evidence_pack(pack)
    assert result["valid"] is True
    assert result["signature_valid"] is True
    assert result["checksums_valid"] is True


def test_c0175_modified_required_content_rejected(pack: Path) -> None:
    (pack / "README.md").write_text("tampered evidence description")
    assert verify_m0_evidence_pack(pack)["valid"] is False
