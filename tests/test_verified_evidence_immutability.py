"""Regresiones: verified_evidence inmutable, idempotente y sin colisiones de normalización."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_KISH_ENGINE"))

from babylon60.kernel.grounding_interceptor import (  # noqa: E402
    EvidenceIntegrityConflictError,
    EvidenceRecord,
    GroundingRegistry,
)

D1 = "a" * 64
D2 = "b" * 64


def rec(etype: str, ident: str, digest: str) -> EvidenceRecord:
    return EvidenceRecord(
        entity_type=etype,
        identifier=ident,
        sha256_digest=digest,
        canonical_title="t",
        source="s",
        verified_at="2026-11-13T00:00:00Z",
    )


def rows(db: Path) -> list[tuple[str, str]]:
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT key, sha256_digest FROM verified_evidence ORDER BY key").fetchall()


@pytest.fixture
def db(tmp_path: Path) -> Path:
    return tmp_path / "evidence.db"


def test_same_identifier_same_digest_is_idempotent(db: Path) -> None:
    reg = GroundingRegistry(str(db))
    reg.register(rec("DOI", "10.1000/XYZ", D1))
    reg.register(rec("DOI", "https://doi.org/10.1000/xyz", D1))
    GroundingRegistry(str(db)).register(rec("DOI", "doi:10.1000/Xyz", D1))
    assert rows(db) == [("DOI:10.1000/xyz", D1)]


def test_same_identifier_different_digest_raises_and_preserves_original(db: Path) -> None:
    reg = GroundingRegistry(str(db))
    reg.register(rec("ARXIV", "2401.12345v1", D1))
    with pytest.raises(EvidenceIntegrityConflictError):
        reg.register(rec("ARXIV", "arXiv:2401.12345v1", D2))
    with pytest.raises(EvidenceIntegrityConflictError):
        GroundingRegistry(str(db)).register(rec("ARXIV", "2401.12345V1", D2))
    assert rows(db) == [("ARXIV:2401.12345v1", D1)]
    found = reg.lookup("ARXIV", "2401.12345v1")
    assert found is not None and found.sha256_digest == D1


def test_patent_kind_codes_do_not_collide(db: Path) -> None:
    reg = GroundingRegistry(str(db))
    reg.register(rec("PATENT", "US123A1", D1))
    reg.register(rec("PATENT", "US123B2", D2))
    assert rows(db) == [("PATENT:US-123-A1", D1), ("PATENT:US-123-B2", D2)]
    found_a = reg.lookup("PATENT", "US 123 A1")
    found_b = reg.lookup("PATENT", "US123B2")
    assert found_a is not None and found_a.sha256_digest == D1
    assert found_b is not None and found_b.sha256_digest == D2


def test_arxiv_versions_do_not_collide(db: Path) -> None:
    reg = GroundingRegistry(str(db))
    reg.register(rec("ARXIV", "arXiv:2401.12345v1", D1))
    reg.register(rec("ARXIV", "arXiv:2401.12345v2", D2))
    assert rows(db) == [("ARXIV:2401.12345v1", D1), ("ARXIV:2401.12345v2", D2)]


@pytest.mark.parametrize(
    "stmt",
    [
        "UPDATE verified_evidence SET sha256_digest = 'cc'",
        "DELETE FROM verified_evidence",
        "INSERT OR REPLACE INTO verified_evidence VALUES "
        "('DOI:10.1000/xyz','DOI','x','" + "c" * 64 + "','t','s','v','VERIFIED')",
    ],
)
def test_direct_mutation_is_aborted_by_trigger(db: Path, stmt: str) -> None:
    GroundingRegistry(str(db)).register(rec("DOI", "10.1000/xyz", D1))
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA recursive_triggers = ON")
        with pytest.raises(sqlite3.IntegrityError, match="VERIFIED_EVIDENCE_IMMUTABLE"):
            conn.execute(stmt)
    assert rows(db) == [("DOI:10.1000/xyz", D1)]


def test_in_memory_registry_rejects_conflicting_digest() -> None:
    reg = GroundingRegistry()
    reg.register(rec("DOI", "10.1/a", D1))
    reg.register(rec("DOI", "10.1/A", D1))
    with pytest.raises(EvidenceIntegrityConflictError):
        reg.register(rec("DOI", "10.1/a", D2))


def test_lowercase_word_after_patent_is_not_a_kind_code(db: Path) -> None:
    from babylon60.kernel.grounding_interceptor import GroundingInterceptor

    reg = GroundingRegistry(str(db))
    reg.register(rec("PATENT", "9640165", D1))
    res = GroundingInterceptor(registry=reg).intercept("Patente US 9,640,165 y de nuevo US 9,640,165 B2.")
    assert [r.identifier for r in res.verified_citations] == ["9640165"]
    assert res.unverified_citations and "B2" in res.unverified_citations[0][1]
