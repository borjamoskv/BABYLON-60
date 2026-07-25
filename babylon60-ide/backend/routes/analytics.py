from __future__ import annotations

import contextlib
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ..services.db_pool import connect_readonly

router = APIRouter(prefix="/api/ledger", tags=["analytics"])
_TOKEN_RE = re.compile("[a-z0-9_]+")
_BM25_K1 = 1.5
_BM25_B = 0.75
_SEARCH_SCAN_CAP = 5000


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _find_ledger_db(root: Path) -> Path | None:
    candidates = [root / "master_ledger.db", root / "babylon60" / "bft" / "ultrathink_ledger.db"]
    for c in candidates:
        if c.exists():
            return c
    for db_file in sorted(root.glob("*.db")):
        try:
            with contextlib.closing(connect_readonly(db_file)) as conn:
                has = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='ledger_entries'"
                ).fetchone()
                if has:
                    return db_file
        except sqlite3.DatabaseError:
            continue
    return None


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@router.get("/analytics")
def ledger_analytics() -> dict[str, Any]:
    root = _get_project_root()
    db_path = _find_ledger_db(root)
    if not db_path:
        raise HTTPException(404, "No ledger database found")
    conn = connect_readonly(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM ledger_entries").fetchone()["c"]
        streams = [
            {"stream": r["stream"], "count": r["c"]}
            for r in conn.execute(
                "SELECT stream, COUNT(*) AS c FROM ledger_entries GROUP BY stream ORDER BY c DESC LIMIT 20"
            )
        ]
        event_types = [
            {"event_type": r["event_type"], "count": r["c"]}
            for r in conn.execute(
                "SELECT event_type, COUNT(*) AS c FROM ledger_entries GROUP BY event_type ORDER BY c DESC LIMIT 20"
            )
        ]
        agent_counter: Counter[str] = Counter()
        for r in conn.execute("SELECT cortex_taint FROM ledger_entries"):
            taint = r["cortex_taint"] or "unknown"
            agent_counter[taint.split(":", 1)[0].split("|", 1)[0]] += 1
        agents = [{"agent": a, "count": c} for a, c in agent_counter.most_common(20)]
        lam = conn.execute(
            "SELECT MIN(lamport_t) AS mn, MAX(lamport_t) AS mx, COUNT(DISTINCT lamport_t) AS d FROM ledger_entries"
        ).fetchone()
        lam_min, lam_max, lam_distinct = (lam["mn"], lam["mx"], lam["d"])
        expected = lam_max - lam_min + 1 if lam_min is not None and lam_max is not None else 0
        lamport = {
            "min": lam_min,
            "max": lam_max,
            "distinct": lam_distinct,
            "expected_span": expected,
            "gaps": max(0, expected - lam_distinct) if expected else 0,
            "contiguous": bool(expected) and lam_distinct == expected,
        }
        span = conn.execute("SELECT MIN(created_at) AS first, MAX(created_at) AS last FROM ledger_entries").fetchone()
        return {
            "db_path": db_path.name,
            "total_entries": total,
            "streams": streams,
            "event_types": event_types,
            "agents": agents,
            "lamport": lamport,
            "time_span": {"first": span["first"], "last": span["last"]},
        }
    finally:
        conn.close()


@router.get("/search")
def ledger_search(q: str = Query(..., min_length=1), limit: int = Query(15, ge=1, le=100)) -> dict[str, Any]:
    root = _get_project_root()
    db_path = _find_ledger_db(root)
    if not db_path:
        raise HTTPException(404, "No ledger database found")
    q_terms = _tokenize(q)
    if not q_terms:
        return {"query": q, "results": [], "corpus_size": 0, "method": "bm25-lexical"}
    conn = connect_readonly(db_path)
    try:
        total_rows = conn.execute("SELECT COUNT(*) AS c FROM ledger_entries").fetchone()["c"]
        rows = conn.execute(
            "SELECT seq, stream, entity_id, event_type, cortex_taint, payload_json, created_at FROM ledger_entries ORDER BY seq DESC LIMIT ?",
            (_SEARCH_SCAN_CAP,),
        ).fetchall()
        docs: list[tuple[int, list[str], sqlite3.Row]] = []
        df: Counter[str] = Counter()
        total_len = 0
        for r in rows:
            text = " ".join(
                str(r[k] or "") for k in ("payload_json", "cortex_taint", "event_type", "stream", "entity_id")
            )
            toks = _tokenize(text)
            docs.append((r["seq"], toks, r))
            total_len += len(toks)
            for t in set(toks):
                df[t] += 1
        scanned = len(docs)
        n = scanned or 1
        avgdl = total_len / n
        idf: dict[str, float] = {}
        for t in set(q_terms):
            n_t = df.get(t, 0)
            idf[t] = math.log(1 + (n - n_t + 0.5) / (n_t + 0.5))
        scored: list[dict[str, Any]] = []
        for _seq, toks, r in docs:
            if not toks:
                continue
            tf = Counter(toks)
            dl = len(toks)
            score = 0.0
            for t in q_terms:
                f = tf.get(t, 0)
                if not f:
                    continue
                denom = f + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl)
                score += idf.get(t, 0.0) * (f * (_BM25_K1 + 1)) / denom
            if score > 0:
                payload = r["payload_json"] or ""
                scored.append(
                    {
                        "seq": r["seq"],
                        "stream": r["stream"],
                        "entity_id": r["entity_id"],
                        "event_type": r["event_type"],
                        "cortex_taint": r["cortex_taint"],
                        "created_at": r["created_at"],
                        "score": round(score, 4),
                        "snippet": payload[:180],
                    }
                )
        scored.sort(key=lambda d: d["score"], reverse=True)
        return {
            "query": q,
            "terms": q_terms,
            "results": scored[:limit],
            "corpus_size": scanned,
            "scanned": scanned,
            "total": total_rows,
            "truncated": total_rows > scanned,
            "method": "Okapi BM25 (léxico, no neuronal)",
        }
    finally:
        conn.close()
