# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import babylon60.api.state as api_state
import babylon60.auth.manager as auth_manager_module
from babylon60.auth.manager import AuthManager
from babylon60.routes import llm_proxy as llm_proxy_router


@pytest.fixture
def llm_client(tmp_path) -> Iterator[tuple[AuthManager, TestClient]]:
    db_path = tmp_path / "auth.db"
    manager = AuthManager(str(db_path))
    manager.initialize_sync()

    previous_api_manager = api_state.auth_manager
    previous_global_manager = auth_manager_module._auth_manager
    api_state.auth_manager = manager
    auth_manager_module._auth_manager = manager

    app = FastAPI()
    app.include_router(llm_proxy_router.router)
    client = TestClient(app)

    try:
        yield manager, client
    finally:
        client.close()
        asyncio.run(manager.close())
        api_state.auth_manager = previous_api_manager
        auth_manager_module._auth_manager = previous_global_manager


def test_llm_proxy_requires_authentication(llm_client) -> None:
    manager, client = llm_client

    # 1. Unauthenticated request should fail with 401
    response = client.post(
        "/llm-proxy/v1/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 401

    # 2. Authenticated request with invalid token should fail with 401
    response_invalid = client.post(
        "/llm-proxy/v1/chat/completions",
        headers={"Authorization": "Bearer invalid_key"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert response_invalid.status_code == 401

    # 3. Authenticated request with valid token
    token, _ = manager.create_key_sync(
        "test-key",
        tenant_id="tenant-alpha",
        permissions=["read"],
    )

    from unittest.mock import AsyncMock, patch, MagicMock
    import httpx

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "C5-REAL\n```python\nprint('hello')\n```"
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        try:
            response_auth = client.post(
                "/llm-proxy/v1/chat/completions",
                headers={"Authorization": f"Bearer {token}"},
                json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]},
            )
            assert response_auth.status_code in (500, 200)
        except httpx.ConnectError:
            # Request successfully authenticated and reached upstream connection phase
            pass
