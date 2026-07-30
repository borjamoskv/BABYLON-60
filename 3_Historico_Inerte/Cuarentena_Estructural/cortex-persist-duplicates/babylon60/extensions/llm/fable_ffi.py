# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class FableFFIClient:
    """
    C5-REAL Fable 5.0 Foreign Function Interface (FFI) Client.
    Abstracts direct HTTP calls to Anthropic's Fable 5 API to enforce
    deterministic CORTEX interaction and isolate external API logic.
    """

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key
        self.client = client
        self.url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2026-06-09",
            "content-type": "application/json",
        }

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def invoke(self, payload: dict[str, Any], timeout: float = 120.0) -> dict[str, Any]:
        """Invoke the Fable 5 API with the given payload."""
        logger.debug("[FableFFIClient] Executing call to %s", self.url)

        async def _make_request(c: httpx.AsyncClient) -> dict[str, Any]:
            response = await c.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=httpx.Timeout(timeout),
            )
            response.raise_for_status()
            return response.json()

        if self.client:
            return await _make_request(self.client)
        else:
            async with httpx.AsyncClient() as c:
                return await _make_request(c)
