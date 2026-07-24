import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent / "babylon60-ide" / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


from routes.inference import MambaInferenceRequest, generate_mamba  # noqa: E402


def test_mamba_route_handler() -> None:
    """Verify that the FastAPI inference route correctly drives the Mamba Ledger Engine."""
    req = MambaInferenceRequest(prompt="Verification of local execution", max_tokens=3)
    res = generate_mamba(req)

    assert "text" in res
    assert "certificate" in res
    assert res["certificate"]["nodes_count"] == 4  # 1 prompt node + 3 token nodes
    assert res["provider"] == "NATIVE_MAMBA_SSM_LEDGER_ENGINE"
