import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../babylon60-ide/backend")))

from routes.inference import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_zero_network_valid_localhost():
    response = client.post("/api/inference/local/generate", json={
        "prompt": "Test",
        "model": "test",
        "base_url": "http://127.0.0.1:11434/v1"
    })
    # Since there's no actual ollama server in the test environment, we expect a 503 (Local silicon inference socket failed)
    # But it should NOT be a 403 (Zero-Network Policy breached).
    assert response.status_code == 503

def test_zero_network_valid_localhost_name():
    response = client.post("/api/inference/local/generate", json={
        "prompt": "Test",
        "model": "test",
        "base_url": "http://localhost:11434/v1"
    })
    assert response.status_code == 503

def test_zero_network_invalid_domain():
    response = client.post("/api/inference/local/generate", json={
        "prompt": "Test",
        "model": "test",
        "base_url": "http://openai.com/v1"
    })
    assert response.status_code == 403
    assert "strictly forbidden" in response.json()["detail"]

def test_zero_network_attacker_bypass():
    response = client.post("/api/inference/local/generate", json={
        "prompt": "Test",
        "model": "test",
        "base_url": "http://localhost.attacker.com/v1"
    })
    assert response.status_code == 403
    assert "must be confined to loopback" in response.json()["detail"]

def test_zero_network_attacker_bypass_at():
    response = client.post("/api/inference/local/generate", json={
        "prompt": "Test",
        "model": "test",
        "base_url": "http://localhost@attacker.com/v1"
    })
    assert response.status_code == 403
    assert "must be confined to loopback" in response.json()["detail"]
