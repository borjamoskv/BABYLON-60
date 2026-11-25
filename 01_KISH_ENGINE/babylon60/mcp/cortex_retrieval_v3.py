"""CORTEX Memory V3b Hybrid Retrieval & Turn-Window Packing Engine.

Ported from the verified LongMemEval_S V3b evaluation (0.00 EUR local silicon):
  1. ``fts_date_header``: enriches SQLite FTS5 turn documents with lexical date
     tokens (``YYYY-MM-DD Month YYYY Mon``) from ``valid_from`` without mutating
     raw item values or invalidating dense embedding caches.
  2. ``role_aware_c2_rankings``: 4-stream Reciprocal Rank Fusion (RRF) over
     ``[bm25_all, sem_all, bm25_user_first, sem_user_first]`` with consensus
     ``#1`` assistant pinning (``_top_assistant_pins``) so verbose assistant
     filler is suppressed while direct ``single-session-assistant`` hits remain
     uncapped centers.
  3. ``void_dense_rank_from_vecs``: 1-bit binary quantization via
     ``babylon60.transducers.void_vec`` (``pack_void_bit`` +
     ``void_batch_hamming_dist``, 32x vector compression vs float32).
  4. ``select_turn_windows_for_budget``: chronological ``+-window`` (default 2)
     turn-window packer with span-subset deduplication (``span <= existing``),
     overlap merging, ``[...]`` non-contiguous gap markers, asymmetric
     center/neighbor budgets, and BLAKE3 context digesting for verifiable
     ``memory.read_receipt`` replay.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
import re
import sqlite3
from typing import Any, Protocol

import blake3
import numpy as np

from babylon60.transducers.void_vec import pack_void_bit, void_batch_hamming_dist

RETRIEVAL_MODES = ("literal", "fts5", "hybrid", "void_hybrid")
PACKING_MODES = ("items", "turn_window")
DEFAULT_WINDOW = 2
DEFAULT_MAX_PASSAGES = 18
DEFAULT_CONTEXT_BUDGET = 6000
DEFAULT_CENTER_BUDGET = 1400
DEFAULT_NEIGHBOR_BUDGET = 180
DEFAULT_RRF_K = 60
DEFAULT_MAX_PIN_ASSISTANT_CHARS = 4800

_TOKEN = re.compile(r"\w+", re.UNICODE)
_ROLE_PREFIX = re.compile(r"^\s*(user|assistant)\s*:\s*", re.IGNORECASE)

_MONTH_NAMES: dict[int, tuple[str, str]] = {
    1: ("January", "Jan"),
    2: ("February", "Feb"),
    3: ("March", "Mar"),
    4: ("April", "Apr"),
    5: ("May", "May"),
    6: ("June", "Jun"),
    7: ("July", "Jul"),
    8: ("August", "Aug"),
    9: ("September", "Sep"),
    10: ("October", "Oct"),
    11: ("November", "Nov"),
    12: ("December", "Dec"),
}


class Embedder(Protocol):
    """Protocol for pluggable dense embedding transducers."""

    def embed(self, texts: Sequence[str]) -> np.ndarray: ...


def estimate_tokens(text: str) -> int:
    """Conservative upper-bound token estimate without external tokenizer dependencies."""
    if not text:
        return 0
    return max(len(text.split()), math.ceil(len(text) / 3.2))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Clip ``text`` deterministically within ``max_tokens`` estimated tokens."""
    if max_tokens <= 0:
        return ""
    if estimate_tokens(text) <= max_tokens:
        return text
    char_cap = max(1, int(max_tokens * 3.0))
    clipped = text[:char_cap]
    words = clipped.split()
    if len(words) > max_tokens:
        clipped = " ".join(words[:max_tokens])
    return clipped


def fts_date_header(valid_from: str | None) -> str:
    """Render ISO-8601 ``valid_from`` (``YYYY-MM-DD...``) into lexical date tokens for FTS5."""
    if not valid_from or len(valid_from) < 10:
        return ""
    ymd = valid_from[:10]
    parts = ymd.split("-")
    if len(parts) != 3 or not (parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit()):
        return ymd
    year = parts[0]
    full_m, abbr_m = _MONTH_NAMES.get(int(parts[1]), ("", ""))
    if not full_m:
        return ymd
    if full_m == abbr_m:
        return f"{ymd} {full_m} {year}"
    return f"{ymd} {full_m} {year} {abbr_m}"


def infer_speaker(attribute: str | None, value: str) -> str:
    """Infer conversational turn role ('user' or 'assistant') from attribute or value prefix."""
    if attribute:
        low_attr = attribute.strip().lower()
        if low_attr == "assistant" or low_attr.endswith((":assistant", "/assistant", "_assistant")):
            return "assistant"
        if low_attr == "user" or low_attr.endswith((":user", "/user", "_user")):
            return "user"
    m = _ROLE_PREFIX.match(value)
    if m:
        return m.group(1).lower()
    return "user"


def strip_role_prefix(value: str) -> str:
    """Strip a leading 'user:' or 'assistant:' prefix when rendering formatted turn lines."""
    return _ROLE_PREFIX.sub("", value, count=1).strip()


def fts5_query(text: str) -> str:
    tokens = sorted({t.lower() for t in _TOKEN.findall(text)})
    return " OR ".join('"' + t.replace('"', '""') + '"' for t in tokens)


def fts5_bm25(query: str, corpus: Sequence[str]) -> list[int]:
    """Deterministic SQLite FTS5 BM25 ranking (porter + unicode61), ties broken by corpus position."""
    if not corpus:
        return []
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE d USING fts5(body, tokenize='porter unicode61')")
        conn.executemany("INSERT INTO d(rowid, body) VALUES (?, ?)", [(i + 1, doc) for i, doc in enumerate(corpus)])
        q = fts5_query(query)
        matched: list[int] = []
        if q:
            rows = conn.execute("SELECT rowid FROM d WHERE d MATCH ? ORDER BY bm25(d), rowid", (q,)).fetchall()
            matched = [int(r[0]) - 1 for r in rows]
    finally:
        conn.close()
    seen = set(matched)
    return matched + [i for i in range(len(corpus)) if i not in seen]


def _l2_normalize(vecs: np.ndarray) -> np.ndarray:
    arr = np.asarray(vecs, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[None, :]
    norms = np.clip(np.linalg.norm(arr, axis=1, keepdims=True), 1e-12, None)
    return np.asarray(arr / norms, dtype=np.float32)


@dataclass(frozen=True)
class DeterministicProjectionEmbedder:
    """Pure, offline, deterministic BLAKE3 signed n-gram projection embedder (multiple of 8 dims for VOID-VEC)."""

    dim: int = 256

    def __post_init__(self) -> None:
        if self.dim <= 0 or self.dim % 8 != 0:
            raise ValueError("dim must be a positive multiple of 8")

    def _encode_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = [t.lower() for t in _TOKEN.findall(text)]
        if not tokens:
            vec[0] = 1.0
            return vec
        features: list[tuple[str, float]] = []
        for idx, tok in enumerate(tokens):
            features.append((f"w:{tok}", 1.5))
            if len(tok) >= 4:
                features.append((f"p4:{tok[:4]}", 1.0))
            if len(tok) >= 5:
                features.append((f"p5:{tok[:5]}", 1.0))
            if idx + 1 < len(tokens):
                features.append((f"b:{tok}_{tokens[idx + 1]}", 1.25))
            padded = f"<{tok}>"
            for n in (3, 4):
                for start in range(max(0, len(padded) - n + 1)):
                    features.append((f"c{n}:{padded[start : start + n]}", 0.45))
        for feat, weight in features:
            digest = blake3.blake3(feat.encode("utf-8")).digest(length=8)
            h = int.from_bytes(digest, "little")
            bucket = h % self.dim
            sign = 1.0 if ((h >> 32) & 1) == 0 else -1.0
            vec[bucket] += sign * weight
        norm = float(np.linalg.norm(vec))
        if norm < 1e-12:
            vec[0] = 1.0
            return vec
        return vec / norm

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)
        return np.vstack([self._encode_one(t) for t in texts])


DEFAULT_DETERMINISTIC_EMBEDDER = DeterministicProjectionEmbedder(dim=256)


def encode_pair(query: str, corpus: Sequence[str], embedder: Embedder) -> tuple[np.ndarray, np.ndarray]:
    """Encode query and corpus using ``embed_query`` when present, or a single ``embed`` pass."""
    if not corpus:
        return np.empty((0,), dtype=np.float32), np.empty((0, 0), dtype=np.float32)
    embed_q = getattr(embedder, "embed_query", None)
    if callable(embed_q):
        q_vec = np.asarray(embed_q(query), dtype=np.float32)
        d_vecs = np.asarray(embedder.embed(corpus), dtype=np.float32)
        return q_vec, d_vecs
    vecs = np.asarray(embedder.embed([query, *corpus]), dtype=np.float32)
    return vecs[0], vecs[1:]


def dense_rank_from_vecs(q_vec: np.ndarray, d_vecs: np.ndarray) -> list[int]:
    if len(d_vecs) == 0:
        return []
    q_norm = _l2_normalize(q_vec)[0]
    d_norm = _l2_normalize(d_vecs)
    scores = d_norm @ q_norm
    return [int(i) for i in np.argsort(-scores, kind="stable")]


def void_dense_rank_from_vecs(q_vec: np.ndarray, d_vecs: np.ndarray) -> list[int]:
    """1-bit VOID-VEC ranking via sign-bit packing and Hamming distance."""
    if len(d_vecs) == 0:
        return []
    q_bits = pack_void_bit(q_vec)
    d_bits = [pack_void_bit(v) for v in d_vecs]
    dists = np.asarray(void_batch_hamming_dist(q_bits, d_bits), dtype=np.int64)
    return [int(i) for i in np.argsort(dists, kind="stable")]


def rrf(rankings: Sequence[Sequence[int]], k: int = DEFAULT_RRF_K) -> list[int]:
    score: dict[int, float] = {}
    for ranking in rankings:
        for pos, doc in enumerate(ranking):
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + pos + 1)
    return sorted(score, key=lambda d: (-score[d], d))


def user_first_permutation(ranking: Sequence[int], roles: Sequence[str]) -> list[int]:
    """Stable partition placing ``role == 'user'`` items ahead of non-user items."""
    users = [i for i in ranking if roles[i] == "user"]
    others = [i for i in ranking if roles[i] != "user"]
    return users + others


def _dedup_prepend(front: Sequence[int], rest: Sequence[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for idx in (*front, *rest):
        if idx not in seen:
            seen.add(idx)
            out.append(idx)
    return out


def _top_assistant_pins(
    bm25_r: Sequence[int],
    confirm_r: Sequence[int] | None,
    roles: Sequence[str],
    corpus: Sequence[str],
    *,
    max_chars: int = DEFAULT_MAX_PIN_ASSISTANT_CHARS,
) -> list[int]:
    """Preserve a consensus #1 lexical assistant hit (confirmed in top-2 semantic rank) ahead of user-first RRF."""
    if not bm25_r:
        return []
    cand = bm25_r[0]
    if roles[cand] != "assistant" or len(corpus[cand]) > max_chars:
        return []
    if confirm_r is not None and cand not in confirm_r[:2]:
        return []
    return [cand]


def role_aware_c2_rankings(
    query: str,
    corpus: Sequence[str],
    embedder: Embedder | None = None,
    *,
    roles: Sequence[str],
    bm25_corpus: Sequence[str] | None = None,
    bm25_ranking: Sequence[int] | None = None,
    semantic_ranking: Sequence[int] | None = None,
    rrf_k: int = DEFAULT_RRF_K,
    include_void: bool = False,
    max_pin_assistant_chars: int = DEFAULT_MAX_PIN_ASSISTANT_CHARS,
) -> dict[str, list[int]]:
    """Compute V3b role-aware rankings (``fts5``, ``hybrid``, and optional ``void_hybrid``)."""
    if len(roles) != len(corpus):
        raise ValueError(f"roles length ({len(roles)}) != corpus length ({len(corpus)})")
    if not corpus:
        out: dict[str, list[int]] = {
            "c1_bm25": [],
            "fts5": [],
            "dense_only": [],
            "hybrid": [],
        }
        if include_void:
            out["void_dense_only"] = []
            out["void_hybrid"] = []
        return out

    lex_corpus = bm25_corpus if bm25_corpus is not None else corpus
    bm25_r = list(bm25_ranking) if bm25_ranking is not None else fts5_bm25(query, lex_corpus)
    u_bm25 = user_first_permutation(bm25_r, roles)
    c1_pins = _top_assistant_pins(bm25_r, None, roles, corpus, max_chars=max_pin_assistant_chars)
    fts5_ranked = _dedup_prepend(c1_pins, rrf([bm25_r, u_bm25], k=rrf_k))

    if semantic_ranking is not None:
        dense_r = list(semantic_ranking)
        u_dense = user_first_permutation(dense_r, roles)
        c2_pins = _top_assistant_pins(bm25_r, dense_r, roles, corpus, max_chars=max_pin_assistant_chars)
        hybrid_ranked = _dedup_prepend(c2_pins, rrf([bm25_r, dense_r, u_bm25, u_dense], k=rrf_k))
        out = {
            "c1_bm25": bm25_r,
            "fts5": fts5_ranked,
            "dense_only": dense_r,
            "hybrid": hybrid_ranked,
        }
        if include_void:
            out["void_dense_only"] = dense_r
            out["void_hybrid"] = hybrid_ranked
        return out

    active_embedder = embedder if embedder is not None else DEFAULT_DETERMINISTIC_EMBEDDER
    q_vec, d_vecs = encode_pair(query, corpus, active_embedder)
    dense_r = dense_rank_from_vecs(q_vec, d_vecs)
    u_dense = user_first_permutation(dense_r, roles)
    c2_pins = _top_assistant_pins(bm25_r, dense_r, roles, corpus, max_chars=max_pin_assistant_chars)
    out = {
        "c1_bm25": bm25_r,
        "fts5": fts5_ranked,
        "dense_only": dense_r,
        "hybrid": _dedup_prepend(c2_pins, rrf([bm25_r, dense_r, u_bm25, u_dense], k=rrf_k)),
    }
    if include_void:
        void_r = void_dense_rank_from_vecs(q_vec, d_vecs)
        u_void = user_first_permutation(void_r, roles)
        void_pins = _top_assistant_pins(bm25_r, void_r, roles, corpus, max_chars=max_pin_assistant_chars)
        out["void_dense_only"] = void_r
        out["void_hybrid"] = _dedup_prepend(void_pins, rrf([bm25_r, void_r, u_bm25, u_void], k=rrf_k))
    return out


@dataclass(frozen=True)
class TurnRecord:
    """Normalized turn item for V3b turn-window packing."""

    memory_id: str
    entry_hash: str
    recorded_seq: int
    session_key: str
    role: str
    text: str
    valid_from: str | None
    item_ref: Any

    @property
    def index_text(self) -> str:
        return self.text

    @property
    def fts_text(self) -> str:
        hdr = fts_date_header(self.valid_from)
        return f"{hdr} {self.text}".strip() if hdr else self.text


@dataclass(frozen=True)
class SessionGroup:
    session_key: str
    valid_from: str | None
    first_seq: int
    turns: tuple[TurnRecord, ...]


@dataclass(frozen=True)
class TurnRef:
    session_idx: int
    turn_idx: int
    session: SessionGroup
    turn: TurnRecord


@dataclass(frozen=True)
class PackedTurnWindows:
    context_text: str
    selected_session_keys: tuple[str, ...]
    selected_turns: tuple[TurnRecord, ...]
    est_tokens: int
    truncated: bool
    context_blake3: str
    passage_count: int


def build_sessions_and_turn_refs(turns: Sequence[TurnRecord]) -> tuple[list[SessionGroup], list[TurnRef]]:
    """Group ordered ``TurnRecord`` items into sessions by ``session_key`` and flatten turn refs."""
    order: list[str] = []
    grouped: dict[str, list[TurnRecord]] = {}
    for tr in turns:
        if tr.session_key not in grouped:
            order.append(tr.session_key)
            grouped[tr.session_key] = []
        grouped[tr.session_key].append(tr)
    sessions: list[SessionGroup] = []
    for skey in order:
        sturns = tuple(grouped[skey])
        first_valid = next((t.valid_from for t in sturns if t.valid_from), None)
        sessions.append(
            SessionGroup(
                session_key=skey,
                valid_from=first_valid,
                first_seq=sturns[0].recorded_seq,
                turns=sturns,
            )
        )
    refs: list[TurnRef] = []
    for s_idx, sess in enumerate(sessions):
        for t_idx, tr in enumerate(sess.turns):
            refs.append(TurnRef(session_idx=s_idx, turn_idx=t_idx, session=sess, turn=tr))
    return sessions, refs


def _render_turn_window_blocks(
    sessions: Sequence[SessionGroup],
    selected_by_session: dict[int, set[int]],
    center_turns: set[tuple[int, int]],
    *,
    center_budget: int,
    neighbor_budget: int,
) -> tuple[str, list[SessionGroup], list[TurnRecord]]:
    chosen_s = sorted(
        (sessions[s_idx] for s_idx in selected_by_session),
        key=lambda s: (s.valid_from or "", s.first_seq),
    )
    skey_to_idx = {sess.session_key: i for i, sess in enumerate(sessions)}
    blocks: list[str] = []
    used_turns: list[TurnRecord] = []

    for p_num, sess in enumerate(chosen_s, 1):
        s_idx = skey_to_idx[sess.session_key]
        t_indices = sorted(selected_by_session[s_idx])
        lines: list[str] = []
        prev_t: int | None = None
        for t_idx in t_indices:
            if prev_t is not None and t_idx > prev_t + 1:
                lines.append("[...]")
            tr = sess.turns[t_idx]
            used_turns.append(tr)
            cap = center_budget if (s_idx, t_idx) in center_turns else neighbor_budget
            body = truncate_to_tokens(strip_role_prefix(tr.text), cap)
            lines.append(f"{tr.role}: {body}")
            prev_t = t_idx
        blocks.append(f"### Passage {p_num}:\nSession Date: {sess.valid_from or 'unknown'}\n\n" + "\n\n".join(lines))

    return "\n\n".join(blocks), chosen_s, used_turns


def select_turn_windows_for_budget(
    sessions: Sequence[SessionGroup],
    turn_refs: Sequence[TurnRef],
    ranking: Sequence[int],
    *,
    window: int = DEFAULT_WINDOW,
    max_passages: int = DEFAULT_MAX_PASSAGES,
    context_budget: int = DEFAULT_CONTEXT_BUDGET,
    center_budget: int = DEFAULT_CENTER_BUDGET,
    neighbor_budget: int = DEFAULT_NEIGHBOR_BUDGET,
) -> PackedTurnWindows:
    """Pack up to ``max_passages`` ranked turns with ``+-window`` neighbors within ``context_budget``."""
    selected_by_session: dict[int, set[int]] = {}
    center_turns: set[tuple[int, int]] = set()
    passages_picked = 0
    failed_fits = 0
    truncated = False
    context_text = ""
    chosen_s: list[SessionGroup] = []
    used_turns: list[TurnRecord] = []

    for pos in ranking:
        if passages_picked >= max_passages:
            break
        if context_text and (context_budget - estimate_tokens(context_text) < 40 or failed_fits >= 25):
            break
        ref = turn_refs[pos]
        s_idx = ref.session_idx
        t_idx = ref.turn_idx
        lo = max(0, t_idx - window)
        hi = min(len(ref.session.turns) - 1, t_idx + window)
        span = set(range(lo, hi + 1))
        existing = selected_by_session.get(s_idx, set())
        if span <= existing:
            continue
        is_overlap = bool(span & existing)

        cand_selected = {k: set(v) for k, v in selected_by_session.items()}
        cand_selected.setdefault(s_idx, set()).update(span)
        cand_centers = set(center_turns)
        if t_idx not in existing or ref.turn.role == "user":
            cand_centers.add((s_idx, t_idx))

        cand_text, cand_s, cand_turns = _render_turn_window_blocks(
            sessions,
            cand_selected,
            cand_centers,
            center_budget=center_budget,
            neighbor_budget=neighbor_budget,
        )
        if estimate_tokens(cand_text) > context_budget:
            if passages_picked == 0:
                context_text = truncate_to_tokens(cand_text, context_budget)
                chosen_s = cand_s
                used_turns = cand_turns
                passages_picked = 1
                truncated = True
                break
            failed_fits += 1
            continue

        selected_by_session = cand_selected
        center_turns = cand_centers
        context_text = cand_text
        chosen_s = cand_s
        used_turns = cand_turns
        if not is_overlap or passages_picked == 0:
            passages_picked += 1
        failed_fits = 0

    est = estimate_tokens(context_text)
    return PackedTurnWindows(
        context_text=context_text,
        selected_session_keys=tuple(s.session_key for s in chosen_s),
        selected_turns=tuple(used_turns),
        est_tokens=est,
        truncated=truncated,
        context_blake3=blake3.blake3(context_text.encode("utf-8")).hexdigest(),
        passage_count=passages_picked,
    )


__all__ = [
    "DEFAULT_CENTER_BUDGET",
    "DEFAULT_CONTEXT_BUDGET",
    "DEFAULT_DETERMINISTIC_EMBEDDER",
    "DEFAULT_MAX_PASSAGES",
    "DEFAULT_MAX_PIN_ASSISTANT_CHARS",
    "DEFAULT_NEIGHBOR_BUDGET",
    "DEFAULT_RRF_K",
    "DEFAULT_WINDOW",
    "DeterministicProjectionEmbedder",
    "Embedder",
    "PACKING_MODES",
    "PackedTurnWindows",
    "RETRIEVAL_MODES",
    "SessionGroup",
    "TurnRecord",
    "TurnRef",
    "build_sessions_and_turn_refs",
    "dense_rank_from_vecs",
    "encode_pair",
    "estimate_tokens",
    "fts5_bm25",
    "fts5_query",
    "fts_date_header",
    "infer_speaker",
    "role_aware_c2_rankings",
    "rrf",
    "select_turn_windows_for_budget",
    "strip_role_prefix",
    "truncate_to_tokens",
    "user_first_permutation",
    "void_dense_rank_from_vecs",
]
