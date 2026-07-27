import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from babylon60.api.async_client import AsyncCortexClient
from babylon60.api.client import CortexError, Fact


@pytest.fixture
def mock_httpx_request():
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        yield mock_req


@pytest.mark.asyncio
async def test_async_client_initialization():
    with patch.dict("os.environ", {"MOSKV_API_KEY": "test_key"}):
        client = AsyncCortexClient(base_url="http://test:8484/")
        assert client.base_url == "http://test:8484"
        assert client.api_key == "test_key"
        headers = client._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test_key"


@pytest.mark.asyncio
async def test_async_client_request_success(mock_httpx_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_httpx_request.return_value = mock_response

    async with AsyncCortexClient() as client:
        # Mocking interceptor to avoid chaos logic complexity in tests
        with patch(
            "babylon60.api.async_client.async_interceptor", new_callable=AsyncMock
        ) as mock_interceptor:
            mock_interceptor.return_value = mock_response
            res = await client._request("GET", "/test")
            assert res == {"status": "ok"}
            mock_interceptor.assert_called_once()


@pytest.mark.asyncio
async def test_async_client_request_client_error():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Bad Request"}

    async with AsyncCortexClient() as client:
        with patch(
            "babylon60.api.async_client.async_interceptor", new_callable=AsyncMock
        ) as mock_interceptor:
            mock_interceptor.return_value = mock_response

            with pytest.raises(CortexError) as exc_info:
                await client._request("GET", "/test")

            assert exc_info.value.status_code == 400
            assert "Bad Request" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_client_request_retries_on_500():
    # 2 failures (500), 1 success (200)
    resp_500 = MagicMock()
    resp_500.status_code = 500

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"success": True}

    async with AsyncCortexClient() as client:
        with patch(
            "babylon60.api.async_client.async_interceptor", new_callable=AsyncMock
        ) as mock_interceptor:
            mock_interceptor.side_effect = [resp_500, resp_500, resp_200]
            # Patch asyncio.sleep to not actually wait
            with patch("asyncio.sleep", new_callable=AsyncMock):
                res = await client._request("GET", "/test")

            assert res == {"success": True}
            assert mock_interceptor.call_count == 3


@pytest.mark.asyncio
async def test_async_client_store():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"fact_id": 42}

            fact_id = await client.store("my-proj", "my-content", metadata={"a": 1})

            assert fact_id == 42
            mock_req.assert_called_once_with(
                "POST",
                "/v1/facts",
                json={
                    "project": "my-proj",
                    "content": "my-content",
                    "fact_type": "knowledge",
                    "tags": [],
                    "source": "",
                    "metadata": {"a": 1},
                },
            )


@pytest.mark.asyncio
async def test_async_client_search():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = [
                {"fact_id": 1, "project": "proj", "content": "c", "fact_type": "type"}
            ]

            results = await client.search("query", k=2, project="proj")

            assert len(results) == 1
            assert isinstance(results[0], Fact)
            assert results[0].id == 1
            assert results[0].content == "c"
            mock_req.assert_called_once_with(
                "POST", "/v1/search", json={"query": "query", "k": 2, "project": "proj"}
            )


@pytest.mark.asyncio
async def test_async_client_recall():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = [
                {"id": 10, "project": "proj", "content": "c", "fact_type": "type"}
            ]

            results = await client.recall("proj", limit=5, offset=10)

            assert len(results) == 1
            assert results[0].id == 10
            mock_req.assert_called_once_with(
                "GET",
                "/v1/projects/proj/facts",
                params={"include_deprecated": "false", "limit": 5, "offset": 10},
            )


@pytest.mark.asyncio
async def test_async_client_deprecate():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            res = await client.deprecate(99)
            assert res is True
            mock_req.assert_called_once_with("DELETE", "/v1/facts/99")


@pytest.mark.asyncio
async def test_async_client_update():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"fact_id": 99}
            res = await client.update(99, content="new")
            assert res == 99
            mock_req.assert_called_once_with("PATCH", "/v1/facts/99", json={"content": "new"})


@pytest.mark.asyncio
async def test_async_client_export():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"exported": True}
            res = await client.export("proj", fmt="csv")
            assert res == {"exported": True}
            mock_req.assert_called_once_with(
                "GET", "/v1/projects/proj/export", params={"format": "csv"}
            )


@pytest.mark.asyncio
async def test_async_client_status():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"status": "ok"}
            res = await client.status()
            assert res == {"status": "ok"}
            mock_req.assert_called_once_with("GET", "/v1/status")


@pytest.mark.asyncio
async def test_async_client_store_many():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"fact_ids": [1, 2, 3]}
            res = await client.store_many([{"content": "a"}, {"content": "b"}])
            assert res == [1, 2, 3]
            mock_req.assert_called_once_with(
                "POST", "/v1/facts/batch", json={"facts": [{"content": "a"}, {"content": "b"}]}
            )


@pytest.mark.asyncio
async def test_async_client_admin_endpoints():
    async with AsyncCortexClient() as client:
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            # create_key
            mock_req.return_value = {"key": "abc"}
            res = await client.create_key("my-key")
            assert res == {"key": "abc"}
            mock_req.assert_called_with(
                "POST", "/v1/admin/keys", params={"name": "my-key", "tenant_id": "default"}
            )

            # list_keys
            mock_req.return_value = [{"key": "abc"}]
            res = await client.list_keys()
            assert res == [{"key": "abc"}]
            mock_req.assert_called_with("GET", "/v1/admin/keys")
