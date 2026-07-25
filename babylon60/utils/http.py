from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger('babylon60.http')
_DEFAULT_MAX_RETRIES = 5
_DEFAULT_BASE_DELAY = 2.0

class HttpRetryMixin:
    _max_retries: int = _DEFAULT_MAX_RETRIES
    _base_delay: float = _DEFAULT_BASE_DELAY

    @property
    def _provider(self) -> str:
        return self.__class__.__name__

    async def _post_with_retry(self, url: str, headers: dict[str, str], payload: dict[str, Any], label: str='POST') -> dict[str, Any]:
        return await self._request_with_retry('POST', url, headers, payload=payload, label=label)

    async def _get_with_retry(self, url: str, headers: dict[str, str], label: str='GET') -> dict[str, Any]:
        return await self._request_with_retry('GET', url, headers, payload=None, label=label)

    async def _do_http_call(self, method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None, label: str) -> dict[str, Any] | Exception:
        import httpx
        if method == 'POST':
            response = await self._client.post(url, headers=headers, json=payload)
        else:
            response = await self._client.get(url, headers=headers)
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            return exc
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ValueError(f'Unexpected response format from {self._provider} ({label})') from exc

    async def _request_with_retry(self, method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None=None, label: str='') -> dict[str, Any]:
        import httpx
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            result = await self._do_http_call(method, url, headers, payload, label)
            if not isinstance(result, Exception):
                return result
            last_exc = result
            if not isinstance(result, httpx.HTTPStatusError) or result.response.status_code != 429:
                raise result
            if attempt >= self._max_retries - 1:
                raise result
            import random
            base_delay_val = self._base_delay * 2 ** attempt
            delay = base_delay_val + random.uniform(0.1, 2.0) ** (attempt + 1)
            logger.warning('HTTP %s 429 [%s] %s. Retry %d/%d in %.1fs...', method, self._provider, label, attempt + 1, self._max_retries, delay)
            await asyncio.sleep(delay)
        raise last_exc or RuntimeError(f'Retry loop exhausted for {self._provider} ({label})')

async def _do_standalone_post(client: Any, url: str, headers: dict[str, str], payload: dict[str, Any], provider: str, label: str) -> dict[str, Any] | Exception:
    import httpx
    response = await client.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        return exc
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise ValueError(f'Unexpected response format from {provider} ({label})') from exc

async def post_with_retry(client: Any, url: str, headers: dict[str, str], payload: dict[str, Any], provider: str='unknown', label: str='POST', max_retries: int=_DEFAULT_MAX_RETRIES, base_delay: float=_DEFAULT_BASE_DELAY) -> dict[str, Any]:
    import httpx
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        result = await _do_standalone_post(client, url, headers, payload, provider, label)
        if not isinstance(result, Exception):
            return result
        last_exc = result
        if not isinstance(result, httpx.HTTPStatusError) or result.response.status_code != 429:
            raise result
        if attempt >= max_retries - 1:
            raise result
        import random
        base_delay_val = base_delay * 2 ** attempt
        delay = base_delay_val + random.uniform(0.1, 2.0) ** (attempt + 1)
        logger.warning('HTTP POST 429 [%s] %s. Retry %d/%d in %.1fs...', provider, label, attempt + 1, max_retries, delay)
        await asyncio.sleep(delay)
    raise last_exc or RuntimeError(f'Retry loop exhausted for {provider} ({label})')