"""
BABYLON-60 C5-REAL Transducer API Client
"""

from typing import Any, cast

import httpx


class CortexClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def check_health(self) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
