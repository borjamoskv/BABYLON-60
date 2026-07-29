# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""Resilient Browser Research Agent (RBRA).

Provides rate-limit (429) resilient web searching, URL fetching, and claim falsification
for autonomous subagents in the BABYLON-60 ecosystem.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from babylon60.extensions.immune.noise_annihilator import NoiseAnnihilatorAgent, Result

logger = logging.getLogger(__name__)


class ResilientBrowserAgent:
    """Browser agent equipped with exponential backoff and noise annihilation capabilities."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5) -> None:
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.annihilator = NoiseAnnihilatorAgent()

    def fetch_and_filter(self, url: str, raw_content: str) -> Result[str, str]:
        """
        Processes web page content through the 3-layer Popperian filter.

        Args:
            url: Target URL string.
            raw_content: Raw text or markdown fetched from URL.

        Returns:
            Result.Ok(exergy_text) if valid, Result.Err(reason) if discarded as noise.
        """
        logger.info("[BROWSER_AGENT] Inspecting URL: %s (%d bytes)", url, len(raw_content))
        return self.annihilator.process_claim(raw_content)

    def execute_resilient_query(self, query_fn, *args, **kwargs) -> Any:
        """
        Executes a network query function with exponential backoff against HTTP 429 rate limits.
        """
        attempt = 0
        while attempt < self.max_retries:
            try:
                return query_fn(*args, **kwargs)
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    sleep_time = self.backoff_factor ** attempt
                    logger.warning(
                        "⚠️ [BROWSER_AGENT] Rate limit encountered (429). Backing off for %.2fs (Attempt %d/%d)",
                        sleep_time, attempt + 1, self.max_retries
                    )
                    time.sleep(sleep_time)
                    attempt += 1
                else:
                    raise
        raise RuntimeError(f"ResilientBrowserAgent exhausted {self.max_retries} retries on rate limit.")
