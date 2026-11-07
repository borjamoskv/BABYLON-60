# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import json
import hashlib
import time
from typing import Callable, Dict, Any
from babylon60.core.url_cache import URLCacheSync
from babylon60.core.popperian_filter import evaluate_payload, FilterResult, ANCHOR_REGEX

_ATTESTATION_INIT_SQL = """
CREATE TABLE IF NOT EXISTS bft_attestations (
    attestation_id TEXT PRIMARY KEY,
    url_hash TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    anchors_json TEXT NOT NULL,
    lamport_t INTEGER NOT NULL,
    causal_taint TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
"""


class BrowserResearchAgent:
    """
    Sovereign Browser Research Agent Transducer.
    Enforces non-anthropomorphic falsification over external web data
    and records BFT Ledger attestations with Lamport ordering.
    """

    def __init__(self, db_name: str = "browser_url_cache.db") -> None:
        self.cache = URLCacheSync(db_name)
        self._init_attestation_ledger()

    def _init_attestation_ledger(self) -> None:
        self.cache.conn.execute(_ATTESTATION_INIT_SQL)

    def _next_lamport_t(self) -> int:
        """Returns MAX(lamport_t) + 1 for BFT ordering invariant."""
        cursor = self.cache.conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(lamport_t), 0) + 1 FROM bft_attestations")
        row = cursor.fetchone()
        return int(row[0]) if row else 1

    def _record_attestation(self, url: str, payload: str, anchors: list[str], causal_taint: str) -> Dict[str, Any]:
        """Emits an immutable BFT Attestation into the ledger (INV_INGESTA_08)."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        payload_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        attestation_id = hashlib.sha256(f"{url_hash}:{payload_sha256}:{time.time()}".encode("utf-8")).hexdigest()
        lamport_t = self._next_lamport_t()
        now = int(time.time())

        self.cache.conn.execute(
            """
            INSERT INTO bft_attestations (attestation_id, url_hash, payload_sha256, anchors_json, lamport_t, causal_taint, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (attestation_id, url_hash, payload_sha256, json.dumps(anchors), lamport_t, causal_taint, now),
        )

        return {
            "attestation_id": attestation_id,
            "lamport_t": lamport_t,
            "payload_sha256": payload_sha256,
        }

    def fetch_and_verify(
        self,
        url: str,
        fetch_fn: Callable[[str], str],
        causal_taint: str,
        max_cache_age: int = 86400,
    ) -> Dict[str, Any]:
        """
        Executes the 4-phase Browser Agent pipeline:
        1. Level 0 Thermodynamic Cache lookup
        2. Level 1 Direct Transduction (network fetch)
        3. Level 2 Popperian Falsification Gate & Anchor Extraction
        4. Level 3 BFT Ledger Attestation Emission (Lamport ordered)
        """
        if not causal_taint:
            raise ValueError("INV_BFT_03: causal_taint is mandatory for browser research.")

        # Phase 1: Level 0 Cache Check
        cached_payload = self.cache.get(url, max_age_seconds=max_cache_age)
        if cached_payload is not None:
            anchors = self._extract_anchors(cached_payload)
            return {
                "url": url,
                "status": "CACHE_HIT",
                "content": cached_payload,
                "filter_result": FilterResult(passed=True, reason="CACHE_HIT", entropy=0.0),
                "anchors": anchors,
            }

        # Phase 2: Level 1 Transduction (Execute network fetch callback)
        try:
            raw_payload = fetch_fn(url)
        except Exception as e:
            return {
                "url": url,
                "status": "FETCH_FAILED",
                "error": str(e),
                "content": None,
            }

        # Phase 3: Level 2 Popperian Falsification Gate
        filter_res = evaluate_payload(raw_payload)
        if not filter_res.passed:
            return {
                "url": url,
                "status": "REJECTED",
                "reason": filter_res.reason,
                "filter_result": filter_res,
                "content": None,
            }

        # Store verified payload in Level 0 Cache with causal audit trail
        self.cache.put(url, raw_payload, causal_taint=causal_taint)

        anchors = self._extract_anchors(raw_payload)

        # Phase 4: Emit BFT Ledger Attestation
        attestation_info = self._record_attestation(url, raw_payload, anchors, causal_taint)

        return {
            "url": url,
            "status": "VERIFIED_AND_ATTESTED",
            "content": raw_payload,
            "filter_result": filter_res,
            "anchors": anchors,
            "bft_attestation": attestation_info,
        }

    def _extract_anchors(self, text: str) -> list[str]:
        """Extracts cryptographic hashes and URLs to use as BFT Ledger attestations."""
        matches = ANCHOR_REGEX.findall(text)
        return list(set(matches))
