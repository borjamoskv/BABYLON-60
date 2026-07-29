"""
[C5-REAL] babylon60.core.browser_agent — Autonomous Browser Research Agent Component.

Unifies Level 0 Caching (URLCache), Popperian Falsification Gate (popperian_filter),
and Physical Anchor Extraction under the Vibe Operating Invariant (RULE_VIBE_OPERATING_01).

Author: Telmo Dinámico de Moskv (borjamoskv)
"""

from __future__ import annotations

import re
from typing import Callable, Optional, Dict, Any
from babylon60.core.url_cache import URLCacheSync
from babylon60.core.popperian_filter import evaluate_payload, FilterResult, ANCHOR_REGEX

class BrowserResearchAgent:
    """
    Sovereign Browser Research Agent Transducer.
    Enforces non-anthropomorphic falsification over external web data.
    """

    def __init__(self, db_name: str = "browser_url_cache.db"):
        self.cache = URLCacheSync(db_name)

    def fetch_and_verify(
        self,
        url: str,
        fetch_fn: Callable[[str], str],
        causal_taint: str,
        max_cache_age: int = 86400,
    ) -> Dict[str, Any]:
        """
        Executes the 3-phase Browser Agent pipeline:
        1. Level 0 Thermodynamic Cache lookup
        2. Level 1 Direct Transduction (network fetch)
        3. Level 2 Popperian Falsification Gate & Anchor Extraction
        """
        if not causal_taint:
            raise ValueError("INV_BFT_03: causal_taint is mandatory for browser research.")

        # Phase 1: Level 0 Cache Check
        cached_payload = self.cache.get(url, max_age_seconds=max_cache_age)
        if cached_payload is not None:
            return {
                "url": url,
                "status": "CACHE_HIT",
                "content": cached_payload,
                "filter_result": FilterResult(passed=True, reason="CACHE_HIT", entropy=0.0),
                "anchors": self._extract_anchors(cached_payload),
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
        return {
            "url": url,
            "status": "VERIFIED_AND_CACHED",
            "content": raw_payload,
            "filter_result": filter_res,
            "anchors": anchors,
        }

    def _extract_anchors(self, text: str) -> list[str]:
        """Extracts cryptographic hashes and URLs to use as BFT Ledger attestations."""
        matches = ANCHOR_REGEX.findall(text)
        return list(set(matches))
