# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened · Kernel
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | RING-0 CORTAFUEGOS 5
# ============================================================================
"""
Grounding Interceptor & Fail-Closed Citation Dropper (Cortafuegos 5).
Intercepta y audita deterministamente en silicio cualquier flujo de texto,
impidiendo la emisión de patentes, identificadores arXiv, DOIs o citas académicas
que carezcan de un EvidenceRef criptográfico verificado en la base de datos local.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import logging
import re
import sqlite3
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("babylon60.grounding_interceptor")

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class UnverifiedGroundingError(Exception):
    """Lanzada en modo STRICT_ABORT ante cualquier claim o cita no verificada (BJR-E041)."""


class EvidenceIntegrityConflictError(Exception):
    """Lanzada cuando una clave ya registrada recibe un sha256_digest distinto (inmutabilidad)."""

    def __init__(self, key: str, stored_digest: str, offered_digest: str) -> None:
        super().__init__(
            f"[VERIFIED_EVIDENCE_IMMUTABLE] '{key}' ya registrado con digest {stored_digest}; "
            f"rechazado digest {offered_digest}."
        )
        self.key = key
        self.stored_digest = stored_digest
        self.offered_digest = offered_digest


class SyntheticPlaceholderError(Exception):
    """Lanzada ante la presencia de placeholders sintéticos (ej. arXiv:2408.xxxxx)."""


@dataclasses.dataclass(frozen=True)
class EvidenceRecord:
    """Registro inmutable de una evidencia empírica verificada en silicio."""

    entity_type: str  # 'PATENT', 'ARXIV', 'DOI', 'PAPER'
    identifier: str  # Identificador normalizado (ej. 'US-9640165', '2408.08058')
    sha256_digest: str  # Digest SHA-256 del documento primario o metadato
    canonical_title: str  # Título o descripción formal verificada
    source: str  # Repositorio/institución de origen (ej. 'USPTO', 'arXiv', 'QMUL')
    verified_at: str  # Timestamp ISO-8601 de verificación
    status: str = "VERIFIED"


@dataclasses.dataclass
class InterceptResult:
    """Resultado determinista de la interceptación."""

    is_clean: bool
    status: str  # 'COMMITTED', 'REDACTED', 'AUDITED_DIRTY', 'DROP'
    original_text: str
    sanitized_text: str
    verified_citations: List[EvidenceRecord]
    unverified_citations: List[Tuple[str, str]]  # (entity_type, raw_identifier)
    merkle_root: str


class GroundingRegistry:
    """
    Registro y caché empírica de evidencias verificadas.
    Soporta inicialización en memoria, persistencia SQLite y carga desde JSON/TOML.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._cache: Dict[str, EvidenceRecord] = {}
        self._db_path = db_path
        if self._db_path:
            self._init_sqlite()

    def _connect(self) -> sqlite3.Connection:
        assert self._db_path is not None
        # isolation_level=None: autocommit; las transacciones se abren explícitamente
        # con BEGIN IMMEDIATE, sin transacciones implícitas del módulo sqlite3.
        conn = sqlite3.connect(self._db_path, timeout=5.0, isolation_level=None)
        conn.execute("PRAGMA recursive_triggers = ON")
        return conn

    def _init_sqlite(self) -> None:
        with contextlib.closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS verified_evidence (
                        key TEXT PRIMARY KEY,
                        entity_type TEXT NOT NULL,
                        identifier TEXT NOT NULL,
                        sha256_digest TEXT NOT NULL,
                        canonical_title TEXT NOT NULL,
                        source TEXT NOT NULL,
                        verified_at TEXT NOT NULL,
                        status TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS verified_evidence_no_update
                    BEFORE UPDATE ON verified_evidence
                    BEGIN SELECT RAISE(ABORT, 'VERIFIED_EVIDENCE_IMMUTABLE'); END
                    """
                )
                conn.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS verified_evidence_no_delete
                    BEFORE DELETE ON verified_evidence
                    BEGIN SELECT RAISE(ABORT, 'VERIFIED_EVIDENCE_IMMUTABLE'); END
                    """
                )
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        self._load_from_sqlite()

    def _make_key(self, entity_type: str, identifier: str) -> str:
        norm_id = self.normalize_identifier(entity_type, identifier)
        return f"{entity_type.upper()}:{norm_id}"

    @staticmethod
    def normalize_identifier(entity_type: str, identifier: str) -> str:
        """Normaliza sin colapsar documentos distintos.

        - DOI: minúsculas; se eliminan prefijos ``doi:`` y ``https://doi.org/``/``dx.doi.org``.
        - PATENT: se preserva el kind code WIPO ST.16 (``US123A1`` != ``US123B2``).
        - ARXIV: se preserva el sufijo de versión explícito ``vN`` (``v1`` != ``v2``).
        """
        etype = entity_type.upper()
        raw = identifier.strip()
        if etype == "DOI":
            clean_doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", raw, flags=re.IGNORECASE)
            return clean_doi.rstrip(".,;)").lower()
        clean = raw.replace(",", "").replace(".", "" if etype == "PATENT" else ".").replace(" ", "").upper()
        if etype == "PATENT":
            clean = re.sub(r"^(?:USPATENT(?:NO)?|USPAT|US)", "", clean)
            m = re.fullmatch(r"(?:PATENT(?:NO)?)?-?(\d+)([A-Z]\d?)?", clean)
            if not m:
                return f"US-{clean}"
            number, kind = m.group(1), m.group(2)
            return f"US-{number}-{kind}" if kind else f"US-{number}"
        if etype == "ARXIV":
            clean = re.sub(r"^ARXIV:", "", clean, flags=re.IGNORECASE)
            return clean.lower()
        return clean

    @staticmethod
    def _validate_digest(digest: str, identifier: str) -> None:
        if not digest or len(digest) != 64 or digest.lower() == EMPTY_SHA256:
            raise ValueError(f"[BJR-E041] EvidenceRef huérfano o con hash vacío para '{identifier}'.")

    def register(self, record: EvidenceRecord) -> None:
        """Registra una evidencia verificada de forma inmutable e idempotente (BJR-E041).

        Misma clave + mismo digest -> no-op. Misma clave + digest distinto ->
        EvidenceIntegrityConflictError, sin tocar lo almacenado. La caché en memoria
        solo se actualiza tras el COMMIT, de modo que un fallo de persistencia no
        deja evidencia confiada en memoria (SW100-C0075).
        """
        self._validate_digest(record.sha256_digest, record.identifier)
        key = self._make_key(record.entity_type, record.identifier)
        cached = self._cache.get(key)
        if not self._db_path:
            if cached is not None:
                if cached.sha256_digest != record.sha256_digest:
                    raise EvidenceIntegrityConflictError(key, cached.sha256_digest, record.sha256_digest)
                return
            self._cache[key] = record
            return
        with contextlib.closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute(
                    """
                    INSERT INTO verified_evidence
                    (key, entity_type, identifier, sha256_digest, canonical_title, source, verified_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(key) DO NOTHING
                    """,
                    (
                        key,
                        record.entity_type,
                        record.identifier,
                        record.sha256_digest,
                        record.canonical_title,
                        record.source,
                        record.verified_at,
                        record.status,
                    ),
                )
                if cur.rowcount == 0:
                    row = conn.execute(
                        "SELECT entity_type, identifier, sha256_digest, canonical_title, source, verified_at, status "
                        "FROM verified_evidence WHERE key = ?",
                        (key,),
                    ).fetchone()
                    if row is None or row[2] != record.sha256_digest:
                        stored = row[2] if row is not None else "<missing>"
                        raise EvidenceIntegrityConflictError(key, stored, record.sha256_digest)
                    record = EvidenceRecord(*row)
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        self._cache[key] = record

    def lookup(self, entity_type: str, identifier: str) -> Optional[EvidenceRecord]:
        key = self._make_key(entity_type, identifier)
        return self._cache.get(key)

    def _load_from_sqlite(self) -> None:
        assert self._db_path is not None
        with contextlib.closing(self._connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT entity_type, identifier, sha256_digest, canonical_title, source, verified_at, status "
                "FROM verified_evidence"
            )
            for row in cursor.fetchall():
                rec = EvidenceRecord(
                    entity_type=row[0],
                    identifier=row[1],
                    sha256_digest=row[2],
                    canonical_title=row[3],
                    source=row[4],
                    verified_at=row[5],
                    status=row[6],
                )
                key = self._make_key(rec.entity_type, rec.identifier)
                self._cache[key] = rec

    def load_from_json(self, json_path: str) -> int:
        """Carga evidencias desde un archivo JSON estructurado (fail-closed ante falta de digest)."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        items = data if isinstance(data, list) else data.get("evidence", [])
        for item in items:
            digest = item.get("sha256_digest", "")
            self._validate_digest(digest, item.get("identifier", "UNKNOWN"))
            rec = EvidenceRecord(
                entity_type=item.get("entity_type", "PAPER"),
                identifier=item["identifier"],
                sha256_digest=digest,
                canonical_title=item.get("canonical_title", ""),
                source=item.get("source", "UNKNOWN"),
                verified_at=item.get("verified_at", "2026-10-13T00:00:00Z"),
                status=item.get("status", "VERIFIED"),
            )
            self.register(rec)
            count += 1
        return count


class GroundingInterceptor:
    """
    Motor interceptor de Anillo-0 que escanea y filtra en tiempo real
    citas sin soporte empírico verificado (Cortafuegos 5).
    """

    POLICY_STRICT_ABORT = "STRICT_ABORT"
    POLICY_AUTO_REDACT = "AUTO_REDACT"
    POLICY_AUDIT_ONLY = "AUDIT_ONLY"

    RE_PATENT = re.compile(
        r"\b(?:US\s*(?:Patent\s*(?:No\.?)?|Pat\.?\s*)?|Patente\s+US\s*)"
        # Kind code ST.16 sensible a mayúsculas: con IGNORECASE global, la "y" de
        # "US 9,640,165 y ..." se tomaba como kind code y alteraba la clave.
        r"(\d{1,2}[,\.]\d{3}[,\.]\d{3}(?:\s*(?-i:[A-Z]\d?))?|\d{7,8}(?:\s*(?-i:[A-Z]\d?))?)\b",
        re.IGNORECASE,
    )
    RE_ARXIV = re.compile(
        r"\barXiv:\s*([0-9]{4}\.[0-9a-zA-Z_\.]+)\b",
        re.IGNORECASE,
    )
    RE_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
    RE_SYNTHETIC_PLACEHOLDER = re.compile(
        r"\b(?:arXiv:\d{4}\.[xX]{2,}|(?:US\s*Patent\s*)?[xX]{5,}|TODO_CITATION|MOCK_PAPER|MOCK_PATENT)\b"
    )

    def __init__(
        self,
        registry: Optional[GroundingRegistry] = None,
        default_policy: str = POLICY_AUTO_REDACT,
    ) -> None:
        self.registry = registry or GroundingRegistry()
        self.default_policy = default_policy

    def intercept(self, text: str, policy: Optional[str] = None) -> InterceptResult:
        """Escanea el texto y aplica la política seleccionada contra las citas no verificadas."""
        active_policy = policy or self.default_policy
        verified: List[EvidenceRecord] = []
        unverified: List[Tuple[str, str]] = []
        replacements: List[Tuple[int, int, str]] = []
        handled_spans: List[Tuple[int, int]] = []

        def _overlaps(start: int, end: int) -> bool:
            return any(not (end <= s or start >= e) for s, e in handled_spans)

        # 1. Comprobación fail-closed de placeholders sintéticos (arXiv:2408.xxxxx, TODO_CITATION, etc.)
        for match in self.RE_SYNTHETIC_PLACEHOLDER.finditer(text):
            raw_id = match.group(0)
            etype = "ARXIV" if raw_id.lower().startswith("arxiv:") else "PLACEHOLDER"
            unverified.append((etype, raw_id))
            handled_spans.append((match.start(), match.end()))
            if active_policy == self.POLICY_STRICT_ABORT:
                raise SyntheticPlaceholderError(
                    f"[CORTAFUEGOS-5] Placeholder sintético detectado: '{raw_id}' (BJR-E041)."
                )
            if active_policy == self.POLICY_AUTO_REDACT:
                replacements.append(
                    (
                        match.start(),
                        match.end(),
                        f"[REDACTADO: PLACEHOLDER_SINTÉTICO({raw_id})]",
                    )
                )

        # 2. Escaneo de Patentes
        for match in self.RE_PATENT.finditer(text):
            if _overlaps(match.start(), match.end()):
                continue
            raw_id = match.group(0)
            num_part = match.group(1)
            record = self.registry.lookup("PATENT", num_part)
            if record:
                verified.append(record)
            else:
                unverified.append(("PATENT", raw_id))
                if active_policy == self.POLICY_STRICT_ABORT:
                    raise UnverifiedGroundingError(
                        f"[CORTAFUEGOS-5] Patente sin EvidenceRef verificado en silicio: '{raw_id}' (BJR-E041)."
                    )
                if active_policy == self.POLICY_AUTO_REDACT:
                    replacements.append(
                        (
                            match.start(),
                            match.end(),
                            f"[REDACTADO_POR_FALTA_DE_EVIDENCE_REF: {raw_id.strip()}]",
                        )
                    )

        # 3. Escaneo de arXiv IDs
        for match in self.RE_ARXIV.finditer(text):
            if _overlaps(match.start(), match.end()):
                continue
            raw_id = match.group(0)
            arxiv_num = match.group(1)
            if "x" in arxiv_num.lower() or "todo" in arxiv_num.lower():
                unverified.append(("ARXIV", raw_id))
                if active_policy == self.POLICY_STRICT_ABORT:
                    raise SyntheticPlaceholderError(f"[CORTAFUEGOS-5] arXiv ID con placeholder sintético: '{raw_id}'.")
                if active_policy == self.POLICY_AUTO_REDACT:
                    replacements.append(
                        (
                            match.start(),
                            match.end(),
                            f"[REDACTADO: PLACEHOLDER_SINTÉTICO({raw_id})]",
                        )
                    )
                continue

            record = self.registry.lookup("ARXIV", arxiv_num)
            if record:
                verified.append(record)
            else:
                unverified.append(("ARXIV", raw_id))
                if active_policy == self.POLICY_STRICT_ABORT:
                    raise UnverifiedGroundingError(
                        f"[CORTAFUEGOS-5] arXiv ID sin EvidenceRef verificado: '{raw_id}' (BJR-E041)."
                    )
                if active_policy == self.POLICY_AUTO_REDACT:
                    replacements.append(
                        (
                            match.start(),
                            match.end(),
                            f"[REDACTADO_POR_FALTA_DE_EVIDENCE_REF: {raw_id.strip()}]",
                        )
                    )

        # 4. Escaneo de DOIs (10.xxxx/...)
        for match in self.RE_DOI.finditer(text):
            if _overlaps(match.start(), match.end()):
                continue
            raw_doi = match.group(0).rstrip(".,;)")
            end_pos = match.start() + len(raw_doi)
            record = self.registry.lookup("DOI", raw_doi)
            if record:
                verified.append(record)
            else:
                unverified.append(("DOI", raw_doi))
                if active_policy == self.POLICY_STRICT_ABORT:
                    raise UnverifiedGroundingError(
                        f"[CORTAFUEGOS-5] DOI sin EvidenceRef verificado: '{raw_doi}' (BJR-E041)."
                    )
                if active_policy == self.POLICY_AUTO_REDACT:
                    replacements.append(
                        (
                            match.start(),
                            end_pos,
                            f"[REDACTADO_POR_FALTA_DE_EVIDENCE_REF: {raw_doi}]",
                        )
                    )

        # 5. Construcción del texto saneado
        if active_policy == self.POLICY_AUTO_REDACT and replacements:
            replacements.sort(key=lambda r: r[0], reverse=True)
            sanitized_chars = list(text)
            for start, end, repl in replacements:
                sanitized_chars[start:end] = list(repl)
            sanitized_text = "".join(sanitized_chars)
            status = "REDACTED"
        else:
            sanitized_text = text
            status = "COMMITTED" if not unverified else "AUDITED_DIRTY"

        # 6. Cálculo del Merkle Root RFC 6962 de evidencias verificadas
        merkle_root = self._compute_merkle_root(verified)
        is_clean = len(unverified) == 0

        return InterceptResult(
            is_clean=is_clean,
            status=status if not is_clean else "COMMITTED",
            original_text=text,
            sanitized_text=sanitized_text,
            verified_citations=verified,
            unverified_citations=unverified,
            merkle_root=merkle_root,
        )

    @staticmethod
    def _compute_merkle_root(records: List[EvidenceRecord]) -> str:
        """Calcula la raíz Merkle con separación de dominio RFC 6962 (0x00 hojas, 0x01 nodos)."""
        if not records:
            return "EMPTY_GROUNDING_MERKLE_TREE"

        current_level = [hashlib.sha256(b"\x00" + r.sha256_digest.encode("utf-8")).hexdigest() for r in records]
        while len(current_level) > 1:
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    left = current_level[i]
                    right = current_level[i + 1]
                    combined = hashlib.sha256(b"\x01" + (left + right).encode("utf-8")).hexdigest()
                    next_level.append(combined)
                else:
                    # RFC 6962: promover nodo impar sin duplicación sintética
                    next_level.append(current_level[i])
            current_level = next_level

        return current_level[0]
