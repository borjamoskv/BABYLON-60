from fastapi.testclient import TestClient
from babylon60.api.server import app

client = TestClient(app)

def test_health_check_bft():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "C5-REAL Kernel Active"
    assert "ledger_hash" in data

def test_handoff_rejection_empty_instruction():
    response = client.post("/handoff", json={
        "source_agent": "A1",
        "target_agent": "A2",
        "instruction": ""
    })
    assert response.status_code == 400
    assert "Falta instrucción causal" in response.json()["detail"]

def test_handoff_valid_event():
    response = client.post("/handoff", json={
        "source_agent": "moskv-1-apex",
        "target_agent": "claude-cowork",
        "instruction": "refactor bft"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "HANDOFF_SEALED"
    assert "event_id" in response.json()
