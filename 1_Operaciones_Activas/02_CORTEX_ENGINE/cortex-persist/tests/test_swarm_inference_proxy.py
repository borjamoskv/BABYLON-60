import pytest
from unittest.mock import MagicMock, patch
from babylon60.swarm.inference_proxy import proxy_inference, InferenceRequest, InferenceProxyDaemon
from fastapi import HTTPException
import base64

@pytest.fixture
def inference_request():
    return InferenceRequest(
        agent_id="agent-1",
        prompt="Hello world",
        signature_b64=base64.b64encode(b"signature").decode()
    )

@pytest.mark.asyncio
async def test_proxy_inference_unknown_agent(inference_request):
    with patch("babylon60.swarm.inference_proxy.trust_matrix.get_peer_key", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await proxy_inference(inference_request)
        assert exc.value.status_code == 403
        assert "Identity Not Found" in exc.value.detail

@pytest.mark.asyncio
async def test_proxy_inference_invalid_signature(inference_request):
    mock_key = MagicMock()
    mock_key.verify.side_effect = ValueError("Bad sig")

    with patch("babylon60.swarm.inference_proxy.trust_matrix.get_peer_key", return_value=mock_key):
        with pytest.raises(HTTPException) as exc:
            await proxy_inference(inference_request)
        assert exc.value.status_code == 403
        assert "Invalid Signature" in exc.value.detail

@pytest.mark.asyncio
async def test_proxy_inference_success_testing_mode(inference_request):
    mock_key = MagicMock()

    with patch("babylon60.swarm.inference_proxy.trust_matrix.get_peer_key", return_value=mock_key):
        with patch.dict("os.environ", {"CORTEX_TESTING": "1"}):
            res = await proxy_inference(inference_request)
            assert res == {"response": "MOCK_RESPONSE_FOR_agent-1"}
            mock_key.verify.assert_called_once()

@pytest.mark.asyncio
async def test_proxy_inference_success_live(inference_request):
    mock_key = MagicMock()
    mock_llm_client_cls = MagicMock()
    mock_llm_client = MagicMock()
    mock_llm_client.generate.return_value = "Real response"
    mock_llm_client_cls.return_value = mock_llm_client

    with patch("babylon60.swarm.inference_proxy.trust_matrix.get_peer_key", return_value=mock_key):
        with patch.dict("os.environ", {}, clear=True):
            with patch("babylon60.swarm.inference_proxy.SovereignLLMClient", mock_llm_client_cls):
                res = await proxy_inference(inference_request)
                assert res == {"response": "Real response"}
                mock_llm_client.generate.assert_called_once_with("Hello world")

@pytest.mark.asyncio
async def test_proxy_inference_upstream_failure(inference_request):
    mock_key = MagicMock()
    mock_llm_client_cls = MagicMock()
    mock_llm_client = MagicMock()
    mock_llm_client.generate.side_effect = RuntimeError("API down")
    mock_llm_client_cls.return_value = mock_llm_client

    with patch("babylon60.swarm.inference_proxy.trust_matrix.get_peer_key", return_value=mock_key):
        with patch.dict("os.environ", {}, clear=True):
            with patch("babylon60.swarm.inference_proxy.SovereignLLMClient", mock_llm_client_cls):
                with pytest.raises(HTTPException) as exc:
                    await proxy_inference(inference_request)
                assert exc.value.status_code == 502
                assert "Upstream Inference Failed" in exc.value.detail

def test_inference_proxy_daemon():
    daemon = InferenceProxyDaemon(port=12345)

    with patch("threading.Thread") as mock_thread_cls:
        with patch("uvicorn.Server") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server

            mock_thread = MagicMock()
            mock_thread_cls.return_value = mock_thread

            daemon.start()

            mock_server_cls.assert_called_once()
            mock_thread_cls.assert_called_once_with(target=mock_server.run, daemon=True)
            mock_thread.start.assert_called_once()

            daemon.stop()

            assert mock_server.should_exit is True
            mock_thread.join.assert_called_once_with(timeout=2.0)
