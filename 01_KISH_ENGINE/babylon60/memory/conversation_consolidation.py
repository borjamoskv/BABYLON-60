# ============================================================================
# BABYLON-60 v5.1 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | CONVERSATION CONSOLIDATION ENGINE
# ============================================================================
"""Deterministic C5-REAL conversation consolidation engine.

Unifies epistemic brain-drain auditing (`cortex-telemetry` §10) with durable
BABYLON-60 persistence contracts:
- Explicit source root opt-in (never implicitly opens global user brain/DBs).
- Strictly read-only inspection of source conversations using `O_NOFOLLOW` and
  regular-file descriptor validation (`INV_C5_FS_DESCRIPTOR_NOFOLLOW`).
- Canonical `BLAKE3` identities driven by `logical_tick`, never wall-clock time
  (`INV_C5_ONWIRE_CANON`, `INV_C5_CANONICAL_LOGICAL_TICK`).
- SQLite WAL persistence with `PRAGMA synchronous = FULL` outside Git sources
  (`INV_C5_WAL_SYNCHRONOUS_FULL`), zero LLM internal deliberations stored, and
  atomic Markdown catalog generation.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import stat
import tempfile
from contextlib import closing
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

import blake3

from babylon60.memory.provenance_arbiter import compute_content_identity

REPO_ROOT = Path(__file__).absolute().parents[3]
_CONTENT_DOMAIN = b"CORTEX-CONTENT-v3\x00"
_MANIFEST_DOMAIN = b"CORTEX-CONSOLIDATION-MANIFEST-v1\x00"

MECHANICAL_ARTIFACT_EXACT = frozenset(
    {
        "walkthrough.md",
        "implementation_plan.md",
        "task.md",
    }
)
MECHANICAL_ARTIFACT_PREFIXES = ("learning_proposal",)
EXCLUDED_SESSION_SUBDIRS = frozenset(
    {
        "tempmediastorage",
        ".system_generated",
        "scratch",
        "__pycache__",
        ".git",
    }
)
CRYSTAL_EXTENSIONS = frozenset({".md"})
CODE_EXTENSIONS = frozenset({".py", ".sh", ".rs", ".ts", ".tsx", ".js", ".mjs", ".lean", ".sql", ".toml"})

_USER_REQUEST_RE = re.compile(r"<USER_REQUEST>(.*?)</USER_REQUEST>", re.DOTALL | re.IGNORECASE)
_SYSTEM_BLOCK_RE = re.compile(
    r"<(?:ADDITIONAL_METADATA|USER_SETTINGS_CHANGE|c5_ring0_telemetry|PLAN|GOAL)>.*?"
    r"</(?:ADDITIONAL_METADATA|USER_SETTINGS_CHANGE|c5_ring0_telemetry|PLAN|GOAL)>",
    re.DOTALL | re.IGNORECASE,
)
_XML_TAG_RE = re.compile(r"</?[A-Za-z_][A-Za-z0-9_:-]*>")
_WHITESPACE_RE = re.compile(r"\s+")
_UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
_B3_RE = re.compile(r"\bb3:[0-9a-f]{64}\b", re.IGNORECASE)
_MARKER_RE = re.compile(r"<!--\s*c5-crystal:\s*session=([0-9a-fA-F-]+)\s+path=([^\s]+)\s+b3=(b3:[0-9a-fA-F]{64})\s*-->")

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
    re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}"),
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),
    re.compile(r"gh[pous]_[a-zA-Z0-9]{36}"),
    re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE) KEY-----"),
)

_DOMAIN_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "babylon60",
        (
            "babylon",
            "kish",
            "seqlock",
            "kudurru",
            "larsa",
            "bft",
            "lean",
            "z3",
            "rust",
            "nemesis",
            "ring0",
            "ring 0",
            "moskv",
            "cortex",
            "mcp",
            "antigravity",
            "subagent",
            "orchestrator",
            "anergia",
            "poda",
            "existence_gap",
            "craft_anything",
            "censo_144",
            "parity audit",
        ),
    ),
    (
        "c5_epistemology",
        (
            "c5 real",
            "c5-real",
            "exerg",
            "entrop",
            "landauer",
            "termodin",
            "consolid",
            "epistem",
            "autodidact",
            "falsacion",
            "isomorf",
            "hf_trending",
            "hf_daily",
            "cristal_epistemico",
            "c5_cristal",
            "acta_semanal",
            "seo_geo",
        ),
    ),
    (
        "audio_dsp_flstudio",
        (
            "flstudio",
            "audio",
            "midi",
            "faust",
            "dsp",
            "ambisonic",
            "lufs",
            "remotion",
            "microtonal",
            "espectral",
            "caribou",
            "musica",
            "motorik",
            "bpm",
            "suno",
            "gflow",
            "videoclip",
            "remix",
            "laboa",
        ),
    ),
    (
        "legaltech_governance",
        (
            "eu ai act",
            "aiact",
            "ai_act",
            "legal",
            "hacienda",
            "fiscal",
            "contrato",
            "compliance",
            "actuarial",
            "_mna",
            "m&a",
            "fondeo",
            "capitalizacion",
            "trinquete",
        ),
    ),
    (
        "apple_silicon_hardware",
        ("apple silicon", "m3 pro", "darwin", "arm64", "trng", "secure enclave", "launchd"),
    ),
    (
        "literature_diana",
        (
            "diana",
            "cervantes",
            "filolog",
            "literatur",
            "beckett",
            "aforismo",
            "spo_",
            "hipocresia",
            "polinizacion",
            "somatica",
        ),
    ),
)


@dataclass(frozen=True)
class ConsolidatedArtifactRecord:
    """Metadata and digest for a non-mechanical artifact inside a session."""

    artifact_id: str
    session_id: str
    rel_path: str
    size_bytes: int
    content_b3: str
    classification: str
    catalog_status: str


@dataclass(frozen=True)
class ConsolidationConflict:
    """Divergent digest detected against an existing catalog or vault database."""

    session_id: str
    rel_path: str
    source_surface: str
    recorded_b3: str
    observed_b3: str


@dataclass(frozen=True)
class ConsolidatedSessionRecord:
    """Sanitized structural summary of one Antigravity/agent session."""

    session_id: str
    session_dir: str
    first_seen_utc: str | None
    last_seen_utc: str | None
    user_turn_count: int
    tool_call_count: int
    error_count: int
    malformed_lines: int
    topic_summary: str
    domains: tuple[str, ...]
    transcript_b3: str
    logical_tick: int
    session_in_catalog_ref: bool
    artifacts: tuple[ConsolidatedArtifactRecord, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ConsolidationReport:
    """Complete deterministic output of a consolidation audit or write pass."""

    schema_version: str
    mode: str
    dry_run: bool
    logical_tick: int
    brain_root: str | None
    db_path: str
    catalog_ref: str | None
    catalog_out: str | None
    catalog_ref_present: bool
    db_existed_before: bool
    db_written: bool
    catalog_written: bool
    sessions_scanned: int
    sessions_with_crystals: int
    sessions_already_in_catalog: int
    sessions_persisted_now: int
    artifacts_indexed: int
    crystal_md_count: int
    new_crystal_candidates: int
    already_indexed_crystals: int
    conflicts_count: int
    manifest_b3: str
    status: str
    sessions: tuple[ConsolidatedSessionRecord, ...] = field(default_factory=tuple)
    conflicts: tuple[ConsolidationConflict, ...] = field(default_factory=tuple)

    def to_dict(self, *, include_sessions: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_sessions:
            payload.pop("sessions", None)
        return payload


@dataclass(frozen=True)
class _CatalogIndex:
    present: bool
    session_ids: frozenset[str]
    content_digests: frozenset[str]
    pair_digests: Mapping[tuple[str, str], str]


def default_conversation_vault_db() -> Path:
    """Resolve the default out-of-repo SQLite conversation vault path."""
    override = os.environ.get("CORTEX_CONVERSATION_VAULT_DB")
    if override:
        return Path(override).expanduser()
    babylon_home = os.environ.get("BABYLON_HOME")
    base = Path(babylon_home).expanduser() if babylon_home else Path.home() / ".babylon60"
    return base / "conversations" / "conversation_vault.db"


def _open_regular_ro(path: Path) -> int:
    """Open a regular file read-only without following symlinks (INV_C5_FS_DESCRIPTOR_NOFOLLOW)."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"Expected regular file, got mode {oct(info.st_mode)}: {path}")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_regular_text(path: Path, *, max_bytes: int = 16 * 1024 * 1024) -> str:
    fd = _open_regular_ro(path)
    with os.fdopen(fd, "rb") as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError(f"File exceeds {max_bytes} byte safety bound: {path}")
    return raw.decode("utf-8", errors="replace")


def _stream_file_content_b3(path: Path) -> tuple[str, int]:
    """Compute canonical BLAKE3 content identity I_content in constant memory."""
    fd = _open_regular_ro(path)
    hasher = blake3.blake3(_CONTENT_DOMAIN)
    total_bytes = 0
    with os.fdopen(fd, "rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            total_bytes += len(chunk)
            hasher.update(chunk)
    return "b3:" + hasher.hexdigest(), total_bytes


def canonical_manifest_digest(logical_tick: int, session_digests: Sequence[tuple[str, str]]) -> str:
    """Compute canonical BLAKE3 manifest digest strictly from logical_tick and session digests."""
    if type(logical_tick) is not int or logical_tick < 0:
        raise ValueError("logical_tick must be a non-negative integer")
    hasher = blake3.blake3(_MANIFEST_DOMAIN)
    hasher.update(logical_tick.to_bytes(8, "little"))
    for session_id, transcript_b3 in sorted(session_digests):
        sid_bytes = session_id.encode("utf-8")
        dig_bytes = transcript_b3.encode("utf-8")
        hasher.update(len(sid_bytes).to_bytes(4, "little") + sid_bytes)
        hasher.update(len(dig_bytes).to_bytes(4, "little") + dig_bytes)
    return "b3:" + hasher.hexdigest()


def sanitize_user_request_text(raw_content: str) -> str:
    """Extract clean user prompt text, stripping IDE XML wrappers and redacting secrets."""
    if not isinstance(raw_content, str) or not raw_content:
        return ""
    matches = [m.strip() for m in _USER_REQUEST_RE.findall(raw_content) if m.strip()]
    text = " | ".join(matches) if matches else _SYSTEM_BLOCK_RE.sub(" ", raw_content)
    text = _XML_TAG_RE.sub(" ", text)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET]", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _classify_domains(
    texts: Sequence[str],
    artifact_names: Sequence[str] = (),
) -> tuple[str, ...]:
    raw_blob = " ".join([*texts, *artifact_names]).lower()
    normalized_blob = raw_blob.replace("_", " ").replace("-", " ")
    matched = [
        domain for domain, keywords in _DOMAIN_RULES if any(kw in raw_blob or kw in normalized_blob for kw in keywords)
    ]
    return tuple(matched) if matched else ("general_ops",)


def _is_mechanical_artifact(rel_path: Path) -> bool:
    parts_lower = [part.lower() for part in rel_path.parts]
    if any(part in EXCLUDED_SESSION_SUBDIRS or part.startswith(".") for part in parts_lower[:-1]):
        return True
    name_lower = rel_path.name.lower()
    if name_lower.startswith(".") or name_lower.endswith(".metadata.json") or ".resolved" in name_lower:
        return True
    if name_lower in MECHANICAL_ARTIFACT_EXACT:
        return True
    if name_lower.startswith(MECHANICAL_ARTIFACT_PREFIXES):
        return True
    return False


def _classify_artifact(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in CRYSTAL_EXTENSIONS:
        return "CRYSTAL_MD"
    if ext in CODE_EXTENSIONS:
        return "CODE_OR_SCRIPT"
    return "OTHER"


def _parse_catalog_reference(catalog_ref: Path | None) -> _CatalogIndex:
    if catalog_ref is None:
        return _CatalogIndex(False, frozenset(), frozenset(), {})
    try:
        text = _read_regular_text(catalog_ref)
    except FileNotFoundError:
        return _CatalogIndex(False, frozenset(), frozenset(), {})

    session_ids = frozenset(m.lower() for m in _UUID_RE.findall(text))
    content_digests = frozenset(m.lower() for m in _B3_RE.findall(text))
    pair_digests: dict[tuple[str, str], str] = {}
    for sid, rel_path, digest in _MARKER_RE.findall(text):
        pair_digests[(sid.lower(), rel_path)] = digest.lower()
    return _CatalogIndex(True, session_ids, content_digests, pair_digests)


def _iter_session_files(session_dir: Path) -> list[Path]:
    """Walk non-excluded regular files inside a session dir without following symlinks."""
    found: list[Path] = []

    def walk(current: Path) -> None:
        with os.scandir(current) as entries:
            ordered = sorted(entries, key=lambda entry: entry.name)
            for entry in ordered:
                name_lower = entry.name.lower()
                if entry.is_dir(follow_symlinks=False):
                    if name_lower in EXCLUDED_SESSION_SUBDIRS or entry.name.startswith("."):
                        continue
                    walk(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    found.append(Path(entry.path))

    walk(session_dir)
    return found


def _inspect_transcript(
    transcript_path: Path,
) -> tuple[str | None, str | None, int, int, int, int, str, list[str], str]:
    """Stream transcript.jsonl safely, discarding all LLM thinking/reasoning content."""
    try:
        fd = _open_regular_ro(transcript_path)
    except FileNotFoundError:
        return None, None, 0, 0, 0, 0, "(sin transcript)", [], compute_content_identity(b"")

    hasher = blake3.blake3(_CONTENT_DOMAIN)
    first_seen: str | None = None
    last_seen: str | None = None
    user_turns = 0
    tool_calls = 0
    errors = 0
    malformed = 0
    user_snippets: list[str] = []

    with os.fdopen(fd, "rb") as stream:
        for raw_line in stream:
            hasher.update(raw_line)
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if not isinstance(record, dict):
                malformed += 1
                continue

            created_at = record.get("created_at") or record.get("timestamp")
            if isinstance(created_at, str) and created_at.strip():
                ts = created_at.strip()
                if first_seen is None or ts < first_seen:
                    first_seen = ts
                if last_seen is None or ts > last_seen:
                    last_seen = ts

            rec_type = record.get("type")
            if rec_type == "USER_INPUT":
                user_turns += 1
                clean = sanitize_user_request_text(str(record.get("content", "")))
                if clean:
                    user_snippets.append(clean[:240])
            elif rec_type == "PLANNER_RESPONSE":
                # Explicitly ignore `thinking` and raw planner text; count structural tool calls only.
                calls = record.get("tool_calls")
                if isinstance(calls, list):
                    tool_calls += len(calls)
            elif rec_type in {"TOOL_ERROR", "ERROR"}:
                errors += 1

            exit_code = record.get("exit_code")
            if isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code != 0:
                errors += 1

    transcript_b3 = "b3:" + hasher.hexdigest()
    topic = user_snippets[0][:160] if user_snippets else "(sin USER_INPUT)"
    return first_seen, last_seen, user_turns, tool_calls, errors, malformed, topic, user_snippets, transcript_b3


def _load_existing_vault_digests(db_path: Path) -> tuple[bool, dict[tuple[str, str], str]]:
    if not db_path.exists():
        return False, {}
    uri = db_path.absolute().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=5.0)) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "consolidated_artifacts" not in tables:
            return True, {}
        rows = conn.execute("SELECT session_id, rel_path, content_b3 FROM consolidated_artifacts").fetchall()
    return True, {(str(sid), str(rel)): str(dig) for sid, rel, dig in rows}


def _configure_wal_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = FULL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS consolidation_runs (
            run_id TEXT PRIMARY KEY,
            logical_tick INTEGER NOT NULL,
            brain_root TEXT NOT NULL,
            dry_run INTEGER NOT NULL CHECK (dry_run IN (0, 1)),
            sessions_scanned INTEGER NOT NULL,
            sessions_consolidated INTEGER NOT NULL,
            artifacts_indexed INTEGER NOT NULL,
            manifest_b3 TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS consolidated_sessions (
            session_id TEXT PRIMARY KEY,
            session_dir TEXT NOT NULL,
            first_seen_utc TEXT,
            last_seen_utc TEXT,
            user_turn_count INTEGER NOT NULL,
            tool_call_count INTEGER NOT NULL,
            error_count INTEGER NOT NULL,
            topic_summary TEXT NOT NULL,
            domains_json TEXT NOT NULL,
            transcript_b3 TEXT NOT NULL,
            logical_tick INTEGER NOT NULL,
            source_present INTEGER NOT NULL CHECK (source_present IN (0, 1))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS consolidated_artifacts (
            artifact_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES consolidated_sessions(session_id) ON DELETE RESTRICT,
            rel_path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            content_b3 TEXT NOT NULL,
            classification TEXT NOT NULL CHECK (classification IN ('CRYSTAL_MD', 'CODE_OR_SCRIPT', 'OTHER')),
            catalog_status TEXT NOT NULL CHECK (catalog_status IN ('NEW_CANDIDATE', 'ALREADY_INDEXED', 'CONFLICT_DIGEST')),
            UNIQUE(session_id, rel_path)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_consolidated_artifacts_b3 ON consolidated_artifacts (content_b3);")


def render_markdown_catalog(report: ConsolidationReport) -> str:
    """Render a deterministic, secret-free Markdown catalog from a ConsolidationReport."""
    lines = [
        "# Catálogo Consolidado de Conversaciones (C5-REAL)",
        "",
        f"- **Estado:** `{report.status}` | **Modo:** `{report.mode}` | **Logical Tick:** `{report.logical_tick}`",
        f"- **Raíz escaneada:** `{report.brain_root or 'N/A'}`",
        f"- **Manifiesto BLAKE3:** `{report.manifest_b3}`",
        f"- **Sesiones escaneadas:** `{report.sessions_scanned}` (con cristales: `{report.sessions_with_crystals}`, ya referenciadas: `{report.sessions_already_in_catalog}`)",
        f"- **Cristales `.md`:** `{report.crystal_md_count}` (nuevos: `{report.new_crystal_candidates}`, ya indexados: `{report.already_indexed_crystals}`, conflictos: `{report.conflicts_count}`)",
        "",
        "## Sesiones con Cristales o Actividad Estructural",
        "",
    ]

    for sess in report.sessions:
        crystals = [art for art in sess.artifacts if art.classification == "CRYSTAL_MD"]
        if not crystals and sess.user_turn_count == 0:
            continue
        window = f"{sess.first_seen_utc or '?'} -> {sess.last_seen_utc or '?'}"
        domains = ", ".join(sess.domains)
        lines.append(f"### `{sess.session_id}`")
        lines.append(
            f"- **Ventana:** `{window}` | **Turnos usuario:** `{sess.user_turn_count}` | "
            f"**Tool calls:** `{sess.tool_call_count}` | **Errores:** `{sess.error_count}`"
        )
        lines.append(f"- **Dominios:** `{domains}` | **Transcript:** `{sess.transcript_b3}`")
        lines.append(f"- **Tema inicial:** {sess.topic_summary}")
        if crystals:
            lines.append("- **Cristales `.md`:**")
            for art in crystals:
                lines.append(f"  - `{art.rel_path}` ({art.size_bytes} B, `{art.catalog_status}`, `{art.content_b3}`)")
                lines.append(
                    f"    <!-- c5-crystal: session={sess.session_id} path={art.rel_path} b3={art.content_b3} -->"
                )
        lines.append("")

    if report.conflicts:
        lines.extend(["## Conflictos de Digest Detectados", ""])
        for conflict in report.conflicts:
            lines.append(
                f"- `{conflict.session_id}/{conflict.rel_path}` ({conflict.source_surface}): "
                f"registrado `{conflict.recorded_b3}` != observado `{conflict.observed_b3}`"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _atomic_write_text(dest: Path, content: str) -> None:
    """Atomically write Markdown output without following symlinks at destination."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        info = os.lstat(dest)
    except FileNotFoundError:
        info = None
    if info is not None and not stat.S_ISREG(info.st_mode):
        raise ValueError(f"Destination exists and is not a regular file: {dest}")

    fd, tmp_name = tempfile.mkstemp(prefix=".catalog-", suffix=".tmp", dir=str(dest.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_path, dest)
        dir_fd = os.open(dest.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def _persist_session_artifacts(conn: sqlite3.Connection, session: ConsolidatedSessionRecord) -> None:
    conn.execute(
        """
        INSERT INTO consolidated_sessions (
            session_id, session_dir, first_seen_utc, last_seen_utc,
            user_turn_count, tool_call_count, error_count,
            topic_summary, domains_json, transcript_b3, logical_tick, source_present
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(session_id) DO UPDATE SET
            session_dir = excluded.session_dir,
            first_seen_utc = COALESCE(excluded.first_seen_utc, consolidated_sessions.first_seen_utc),
            last_seen_utc = COALESCE(excluded.last_seen_utc, consolidated_sessions.last_seen_utc),
            user_turn_count = excluded.user_turn_count,
            tool_call_count = excluded.tool_call_count,
            error_count = excluded.error_count,
            topic_summary = excluded.topic_summary,
            domains_json = excluded.domains_json,
            transcript_b3 = excluded.transcript_b3,
            logical_tick = excluded.logical_tick,
            source_present = 1
        """,
        (
            session.session_id,
            session.session_dir,
            session.first_seen_utc,
            session.last_seen_utc,
            session.user_turn_count,
            session.tool_call_count,
            session.error_count,
            session.topic_summary,
            json.dumps(list(session.domains), ensure_ascii=False),
            session.transcript_b3,
            session.logical_tick,
        ),
    )
    for art in session.artifacts:
        if art.catalog_status == "CONFLICT_DIGEST":
            # Preserve previously committed digest on conflict; mark status only.
            conn.execute(
                """
                UPDATE consolidated_artifacts
                SET catalog_status = 'CONFLICT_DIGEST'
                WHERE session_id = ? AND rel_path = ?
                """,
                (session.session_id, art.rel_path),
            )
            continue
        conn.execute(
            """
            INSERT INTO consolidated_artifacts (
                artifact_id, session_id, rel_path, size_bytes,
                content_b3, classification, catalog_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, rel_path) DO UPDATE SET
                size_bytes = excluded.size_bytes,
                classification = excluded.classification,
                catalog_status = excluded.catalog_status
            """,
            (
                art.artifact_id,
                session.session_id,
                art.rel_path,
                art.size_bytes,
                art.content_b3,
                art.classification,
                art.catalog_status,
            ),
        )


def _persist_consolidation_db(
    *,
    resolved_db: Path,
    root: Path,
    logical_tick: int,
    manifest_b3: str,
    sessions: list[ConsolidatedSessionRecord],
    total_artifacts: int,
) -> int:
    resolved_db.parent.mkdir(parents=True, exist_ok=True)
    run_id = f"run_{logical_tick}_{manifest_b3[3:19]}"
    persisted_now = 0
    with closing(sqlite3.connect(str(resolved_db), timeout=5.0, isolation_level=None)) as conn:
        _configure_wal_connection(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            _ensure_schema(conn)
            for s in sessions:
                _persist_session_artifacts(conn, s)
                persisted_now += 1
            conn.execute(
                """
                INSERT OR REPLACE INTO consolidation_runs (
                    run_id, logical_tick, brain_root, dry_run,
                    sessions_scanned, sessions_consolidated, artifacts_indexed, manifest_b3
                ) VALUES (?, ?, ?, 0, ?, ?, ?, ?)
                """,
                (run_id, logical_tick, str(root), len(sessions), persisted_now, total_artifacts, manifest_b3),
            )
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        if conn.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise sqlite3.DatabaseError(f"SQLite integrity check failed after consolidation: {resolved_db}")
    return persisted_now


def consolidate_conversations(
    *,
    brain_root: Path | None = None,
    db_path: Path | None = None,
    catalog_ref: Path | None = None,
    catalog_out: Path | None = None,
    dry_run: bool = True,
    logical_tick: int = 60,
    allow_repo_db: bool = False,
) -> ConsolidationReport:
    """Audit and optionally persist conversation session metadata and crystal indices."""
    if type(logical_tick) is not int or logical_tick < 0:
        raise ValueError("logical_tick must be a non-negative integer")

    resolved_db = (db_path or default_conversation_vault_db()).expanduser()
    if not allow_repo_db and resolved_db.absolute().is_relative_to(REPO_ROOT):
        raise ValueError(f"Database path must remain outside repository root: {resolved_db}")

    db_existed_before, db_digests = _load_existing_vault_digests(resolved_db)

    if brain_root is None:
        if not dry_run:
            raise ValueError("Refusing to execute consolidation without explicit --brain-root")
        manifest = canonical_manifest_digest(logical_tick, ())
        return ConsolidationReport(
            schema_version="2.0",
            mode="PASSIVE_STATUS",
            dry_run=True,
            logical_tick=logical_tick,
            brain_root=None,
            db_path=str(resolved_db),
            catalog_ref=str(catalog_ref) if catalog_ref else None,
            catalog_out=str(catalog_out) if catalog_out else None,
            catalog_ref_present=False,
            db_existed_before=db_existed_before,
            db_written=False,
            catalog_written=False,
            sessions_scanned=len({sid for sid, _ in db_digests}),
            sessions_with_crystals=0,
            sessions_already_in_catalog=0,
            sessions_persisted_now=0,
            artifacts_indexed=len(db_digests),
            crystal_md_count=0,
            new_crystal_candidates=0,
            already_indexed_crystals=0,
            conflicts_count=0,
            manifest_b3=manifest,
            status="NO_EXPLICIT_SOURCE",
        )

    root = brain_root.expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"brain_root directory does not exist: {root}")

    catalog_index = _parse_catalog_reference(catalog_ref.expanduser() if catalog_ref else None)
    sessions: list[ConsolidatedSessionRecord] = []
    conflicts: list[ConsolidationConflict] = []
    session_digests: list[tuple[str, str]] = []

    with os.scandir(root) as entries:
        session_dirs = sorted(
            (
                Path(entry.path)
                for entry in entries
                if entry.is_dir(follow_symlinks=False)
                and entry.name.lower() not in EXCLUDED_SESSION_SUBDIRS
                and not entry.name.startswith(".")
            ),
            key=lambda p: p.name,
        )

    for s_dir in session_dirs:
        session_id = s_dir.name
        transcript_path = s_dir / ".system_generated" / "logs" / "transcript.jsonl"
        (
            first_seen,
            last_seen,
            user_turns,
            tool_calls,
            errors,
            malformed,
            topic,
            user_snippets,
            transcript_b3,
        ) = _inspect_transcript(transcript_path)
        session_digests.append((session_id, transcript_b3))

        artifacts: list[ConsolidatedArtifactRecord] = []
        for f_path in _iter_session_files(s_dir):
            rel = f_path.relative_to(s_dir)
            if _is_mechanical_artifact(rel):
                continue
            rel_str = rel.as_posix()
            content_b3, size_bytes = _stream_file_content_b3(f_path)
            classification = _classify_artifact(f_path)

            catalog_status = "NEW_CANDIDATE"
            cat_pair_b3 = catalog_index.pair_digests.get((session_id.lower(), rel_str))
            db_pair_b3 = db_digests.get((session_id, rel_str))

            if cat_pair_b3 is not None:
                if cat_pair_b3 == content_b3.lower():
                    catalog_status = "ALREADY_INDEXED"
                else:
                    catalog_status = "CONFLICT_DIGEST"
                    conflicts.append(ConsolidationConflict(session_id, rel_str, "catalog_ref", cat_pair_b3, content_b3))
            elif content_b3.lower() in catalog_index.content_digests:
                catalog_status = "ALREADY_INDEXED"

            if db_pair_b3 is not None and db_pair_b3 != content_b3:
                catalog_status = "CONFLICT_DIGEST"
                conflicts.append(ConsolidationConflict(session_id, rel_str, "vault_db", db_pair_b3, content_b3))
            elif db_pair_b3 == content_b3 and catalog_status == "NEW_CANDIDATE":
                catalog_status = "ALREADY_INDEXED"

            artifact_id = compute_content_identity(f"{session_id}\0{rel_str}")
            artifacts.append(
                ConsolidatedArtifactRecord(
                    artifact_id=artifact_id,
                    session_id=session_id,
                    rel_path=rel_str,
                    size_bytes=size_bytes,
                    content_b3=content_b3,
                    classification=classification,
                    catalog_status=catalog_status,
                )
            )

        domains = _classify_domains(
            user_snippets,
            artifact_names=[art.rel_path for art in artifacts],
        )

        sessions.append(
            ConsolidatedSessionRecord(
                session_id=session_id,
                session_dir=str(s_dir),
                first_seen_utc=first_seen,
                last_seen_utc=last_seen,
                user_turn_count=user_turns,
                tool_call_count=tool_calls,
                error_count=errors,
                malformed_lines=malformed,
                topic_summary=topic,
                domains=domains,
                transcript_b3=transcript_b3,
                logical_tick=logical_tick,
                session_in_catalog_ref=session_id.lower() in catalog_index.session_ids,
                artifacts=tuple(artifacts),
            )
        )

    sessions.sort(key=lambda s: (s.last_seen_utc or "", s.session_id), reverse=True)
    manifest_b3 = canonical_manifest_digest(logical_tick, session_digests)

    all_artifacts = [art for s in sessions for art in s.artifacts]
    crystals = [art for art in all_artifacts if art.classification == "CRYSTAL_MD"]
    sessions_with_crystals = sum(1 for s in sessions if any(a.classification == "CRYSTAL_MD" for a in s.artifacts))
    sessions_already = sum(1 for s in sessions if s.session_in_catalog_ref)
    new_crystals = sum(1 for a in crystals if a.catalog_status == "NEW_CANDIDATE")
    indexed_crystals = sum(1 for a in crystals if a.catalog_status == "ALREADY_INDEXED")

    db_written = False
    catalog_written = False
    persisted_now = 0

    if not dry_run:
        persisted_now = _persist_consolidation_db(
            resolved_db=resolved_db,
            root=root,
            logical_tick=logical_tick,
            manifest_b3=manifest_b3,
            sessions=sessions,
            total_artifacts=len(all_artifacts),
        )
        db_written = True

    preliminary = ConsolidationReport(
        schema_version="2.0",
        mode="DRY_RUN" if dry_run else "EXECUTE",
        dry_run=dry_run,
        logical_tick=logical_tick,
        brain_root=str(root),
        db_path=str(resolved_db),
        catalog_ref=str(catalog_ref) if catalog_ref else None,
        catalog_out=str(catalog_out) if catalog_out else None,
        catalog_ref_present=catalog_index.present,
        db_existed_before=db_existed_before,
        db_written=db_written,
        catalog_written=False,
        sessions_scanned=len(sessions),
        sessions_with_crystals=sessions_with_crystals,
        sessions_already_in_catalog=sessions_already,
        sessions_persisted_now=persisted_now,
        artifacts_indexed=len(all_artifacts),
        crystal_md_count=len(crystals),
        new_crystal_candidates=new_crystals,
        already_indexed_crystals=indexed_crystals,
        conflicts_count=len(conflicts),
        manifest_b3=manifest_b3,
        status="CONSOLIDATION_DRY_RUN" if dry_run else "CONSOLIDATED",
        sessions=tuple(sessions),
        conflicts=tuple(conflicts),
    )

    if not dry_run and catalog_out is not None:
        _atomic_write_text(catalog_out.expanduser(), render_markdown_catalog(preliminary))
        catalog_written = True

    return replace(preliminary, catalog_written=catalog_written)
