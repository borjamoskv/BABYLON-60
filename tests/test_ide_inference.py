import sys
from pathlib import Path

# Add IDE backend path to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent / "babylon60-ide" / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


from routes.inference import generate_mamba, MambaInferenceRequest  # noqa: E402


def test_mamba_route_handler() -> None:
    """Verify that the FastAPI inference route correctly drives the Mamba Ledger Engine."""
    req = MambaInferenceRequest(prompt="Verification of local execution", max_tokens=3)
    res = generate_mamba(req)

    assert "text" in res
    assert "nodes" in res
    assert len(res["nodes"]) == 4  # 1 prompt node + 3 token nodes
    assert res["provider"] == "NATIVE_MAMBA_SSM_LEDGER_ENGINE"

    # Verify node structure
    for node in res["nodes"]:
        assert "node_id" in node
        assert "parent_id" in node
        assert "claim" in node
        assert "payload_hash" in node
        assert len(node["node_id"]) == 64
        assert len(node["payload_hash"]) == 64
