# ============================================================================
# BABYLON-60 v5.1 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | CORTEX MEMORY VIEW PROJECTION
# ============================================================================
"""Deterministic read-only Markdown view over the CORTEX JSON memory files.

The view is a projection, never a source of truth:
- Explicit memory root opt-in (never implicitly opens the user's home memory).
- Sources (`ghosts.json`, `system.json`, `projects/*.json`, top-level `*.jsonl`)
  are opened read-only with `O_NOFOLLOW` and are never written.
- No model is involved: every block is the source value itself, preceded by a
  marker citing source file, JSON pointer and the BLAKE3 identity of the value.
- No wall-clock time or absolute path enters the output, so deleting the view
  and regenerating it from unchanged sources yields identical bytes.
"""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import blake3

from babylon60.memory.conversation_consolidation import _atomic_write_text, _open_regular_ro
from babylon60.memory.provenance_arbiter import compute_content_identity

VIEW_ROOT_MARKER = "<!-- cortex-view-root: v1 -->"
INDEX_PAGE = "INDEX.md"
MAX_SOURCE_BYTES = 16 * 1024 * 1024

_MANIFEST_DOMAIN = b"CORTEX-MEMORY-VIEW-MANIFEST-v1\x00"
_OBJECT_SOURCES = ("ghosts.json", "system.json")
_PAGE_SUBDIRS = ("projects", "logs")
_BACKTICK_RUN_RE = re.compile(r"`+")
BLOCK_MARKER_RE = re.compile(
    r'^<!-- cortex-view: src=("(?:[^"\\]|\\.)*") ptr=("(?:[^"\\]|\\.)*") b3=(b3:[0-9a-f]{64}) -->$'
)


class MemoryViewError(ValueError):
    """The memory view cannot be projected or written without breaking its contract."""


@dataclass(frozen=True)
class ViewSource:
    """One source file as it was read for this projection."""

    rel_path: str
    page: str
    size_bytes: int
    content_b3: str
    entry_count: int


@dataclass(frozen=True)
class ViewDrift:
    """A page on disk that differs from what the sources project."""

    page: str
    kind: str  # MISSING | MODIFIED | STALE


@dataclass(frozen=True)
class MemoryProjection:
    """The full view: page path -> Markdown, plus the sources it was built from."""

    manifest_b3: str
    sources: tuple[ViewSource, ...]
    pages: Mapping[str, str]

    @property
    def block_count(self) -> int:
        return sum(source.entry_count for source in self.sources)


def canonical_value_identity(value: Any) -> str:
    """BLAKE3 identity of a JSON value, independent of key order and whitespace."""
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return compute_content_identity(canonical.encode("ascii"))


def _reject_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant {token}")


def _read_source(path: Path) -> bytes:
    fd = _open_regular_ro(path)
    with os.fdopen(fd, "rb") as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise MemoryViewError(f"Source exceeds {MAX_SOURCE_BYTES} byte safety bound: {path}")
    return raw


def _parse(text: str, where: str) -> Any:
    try:
        return json.loads(text, parse_constant=_reject_constant)
    except ValueError as exc:
        raise MemoryViewError(f"Invalid JSON in {where}: {exc}") from exc


def _pointer(key: str) -> str:
    return "/" + key.replace("~", "~0").replace("/", "~1")


def _comment_string(text: str) -> str:
    # JSON-quoted, with '>' escaped so no value can close the HTML comment early.
    return json.dumps(text, ensure_ascii=True).replace(">", "\\u003e")


def _code_span(text: str) -> str:
    shown = json.dumps(text, ensure_ascii=False)[1:-1]
    try:
        shown.encode("utf-8")
    except UnicodeEncodeError:
        shown = json.dumps(text, ensure_ascii=True)[1:-1]
    longest = max((len(run) for run in _BACKTICK_RUN_RE.findall(shown)), default=0)
    fence = "`" * (longest + 1)
    return f"{fence} {shown} {fence}" if longest else f"`{shown}`"


def _fenced_json(value: Any) -> list[str]:
    body = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
    try:
        body.encode("utf-8")
    except UnicodeEncodeError:
        body = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
    # No line of pretty-printed JSON is made only of backticks, so nothing in the value can close the fence.
    return ["```json", body, "```"]


def _render_page(source_rel: str, raw: bytes, entries: list[tuple[str, str, Any]]) -> str:
    lines = [
        f"# {_code_span(source_rel)}",
        "",
        f"> Vista de solo lectura generada desde {_code_span(source_rel)} "
        f"(`{compute_content_identity(raw)}`, {len(raw)} B). "
        "No editar: se regenera desde la fuente y cualquier cambio manual se pierde.",
        "",
    ]
    for title, pointer, value in entries:
        lines.append(f"## {_code_span(title)}")
        lines.append(
            f"<!-- cortex-view: src={_comment_string(source_rel)} ptr={_comment_string(pointer)} "
            f"b3={canonical_value_identity(value)} -->"
        )
        lines.extend(_fenced_json(value))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _object_entries(document: Any) -> list[tuple[str, str, Any]]:
    if isinstance(document, dict):
        return [(key, _pointer(key), document[key]) for key in sorted(document)]
    return [("(raíz)", "", document)]


def _log_entries(text: str, source_rel: str) -> list[tuple[str, str, Any]]:
    entries: list[tuple[str, str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip():
            entries.append((f"línea {number}", f"/{number}", _parse(line, f"{source_rel} line {number}")))
    return entries


def _discover(memory_root: Path) -> list[tuple[str, str]]:
    """Return (source rel path, page rel path) pairs in a stable order."""
    found: list[tuple[str, str]] = []
    for name in _OBJECT_SOURCES:
        if os.path.lexists(memory_root / name):
            found.append((name, name[: -len(".json")] + ".md"))
    projects = memory_root / "projects"
    if os.path.lexists(projects):
        if not stat.S_ISDIR(os.lstat(projects).st_mode):
            raise MemoryViewError(f"projects must be a real directory: {projects}")
        for name in sorted(os.listdir(projects)):
            if name.endswith(".json") and not name.startswith("."):
                found.append((f"projects/{name}", f"projects/{name[: -len('.json')]}.md"))
    for name in sorted(os.listdir(memory_root)):
        if name.endswith(".jsonl") and not name.startswith("."):
            found.append((name, f"logs/{name[: -len('.jsonl')]}.md"))
    return found


def _render_index(manifest_b3: str, sources: tuple[ViewSource, ...]) -> str:
    lines = [
        VIEW_ROOT_MARKER,
        "# Vista de memoria CORTEX (solo lectura)",
        "",
        "> Proyección determinista de los ficheros JSON de memoria. No es fuente de verdad: "
        "puede borrarse y regenerarse sin pérdida. Cada bloque cita su fuente, su puntero JSON "
        "y el BLAKE3 del valor.",
        "",
        f"- **Manifiesto BLAKE3:** `{manifest_b3}`",
        f"- **Fuentes:** `{len(sources)}` | **Bloques:** `{sum(source.entry_count for source in sources)}`",
        "",
        "| Página | Fuente | Bytes | Bloques | BLAKE3 de la fuente |",
        "|---|---|---|---|---|",
    ]
    for source in sources:
        lines.append(
            f"| [{source.page}]({source.page}) | {_code_span(source.rel_path)} | {source.size_bytes} "
            f"| {source.entry_count} | `{source.content_b3}` |"
        )
    return "\n".join(lines) + "\n"


def project_memory(memory_root: Path | str) -> MemoryProjection:
    """Read the memory sources under an explicit root and build the full view in memory."""
    root = Path(memory_root).absolute()
    try:
        root_info = os.lstat(root)
    except FileNotFoundError as exc:
        raise MemoryViewError(f"Memory root does not exist: {root}") from exc
    if not stat.S_ISDIR(root_info.st_mode):
        raise MemoryViewError(f"Memory root must be a real directory: {root}")

    sources: list[ViewSource] = []
    pages: dict[str, str] = {}
    for source_rel, page in _discover(root):
        raw = _read_source(root / source_rel)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MemoryViewError(f"Source is not valid UTF-8: {source_rel}") from exc
        if source_rel.endswith(".jsonl"):
            entries = _log_entries(text, source_rel)
        else:
            entries = _object_entries(_parse(text, source_rel))
        if page in pages:
            raise MemoryViewError(f"Two sources project onto the same page: {page}")
        pages[page] = _render_page(source_rel, raw, entries)
        sources.append(ViewSource(source_rel, page, len(raw), compute_content_identity(raw), len(entries)))

    if not sources:
        raise MemoryViewError(f"No memory sources found under {root}")

    hasher = blake3.blake3(_MANIFEST_DOMAIN)
    for source in sources:
        for part in (source.rel_path.encode("utf-8"), source.content_b3.encode("ascii")):
            hasher.update(len(part).to_bytes(4, "little") + part)
    manifest_b3 = "b3:" + hasher.hexdigest()

    ordered = tuple(sources)
    pages[INDEX_PAGE] = _render_index(manifest_b3, ordered)
    return MemoryProjection(manifest_b3=manifest_b3, sources=ordered, pages=pages)


def _existing_pages(out_dir: Path) -> set[str]:
    """Markdown pages currently on disk in the view layout (top level, projects/, logs/)."""
    found: set[str] = set()
    if not os.path.lexists(out_dir):
        return found
    for sub in ("", *_PAGE_SUBDIRS):
        folder = out_dir / sub if sub else out_dir
        if not os.path.lexists(folder):
            continue
        if not stat.S_ISDIR(os.lstat(folder).st_mode):
            raise MemoryViewError(f"View path must be a real directory: {folder}")
        for name in os.listdir(folder):
            if name.endswith(".md"):
                found.add(f"{sub}/{name}" if sub else name)
    return found


def _read_page(path: Path) -> bytes | None:
    try:
        return _read_source(path)
    except (OSError, ValueError):
        return None


def check_view(projection: MemoryProjection, out_dir: Path | str) -> list[ViewDrift]:
    """Compare the view on disk with the projection, without writing anything."""
    out = Path(out_dir).absolute()
    on_disk = _existing_pages(out)
    drift: list[ViewDrift] = []
    for page in sorted(projection.pages):
        if page not in on_disk:
            drift.append(ViewDrift(page, "MISSING"))
        elif _read_page(out / page) != projection.pages[page].encode("utf-8"):
            drift.append(ViewDrift(page, "MODIFIED"))
    drift.extend(ViewDrift(page, "STALE") for page in sorted(on_disk - set(projection.pages)))
    return drift


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def write_view(projection: MemoryProjection, memory_root: Path | str, out_dir: Path | str) -> list[ViewDrift]:
    """Bring the view directory in line with the projection; returns what was changed.

    Only Markdown pages of the view layout are written or pruned, and only in a
    directory that is empty, absent, or already carries the view root marker.
    """
    root = Path(memory_root).resolve()
    out = Path(out_dir).absolute()
    resolved_out = out.resolve()
    if resolved_out == root or _is_within(root, resolved_out) or _is_within(resolved_out, root / "projects"):
        raise MemoryViewError(f"View directory must not be the memory root, contain it, or sit in projects/: {out}")

    if os.path.lexists(out):
        if not stat.S_ISDIR(os.lstat(out).st_mode):
            raise MemoryViewError(f"View path must be a real directory: {out}")
        if os.listdir(out):
            index = _read_page(out / INDEX_PAGE)
            if index is None or not index.startswith(VIEW_ROOT_MARKER.encode("ascii") + b"\n"):
                raise MemoryViewError(f"Refusing to write into a non-empty directory that is not a view: {out}")

    changes = check_view(projection, out)
    for change in changes:
        if change.kind == "STALE":
            os.unlink(out / change.page)
    # The index carries the root marker, so it goes first: an interrupted run can be resumed.
    for change in sorted((c for c in changes if c.kind != "STALE"), key=lambda c: c.page != INDEX_PAGE):
        _atomic_write_text(out / change.page, projection.pages[change.page])
    return changes
