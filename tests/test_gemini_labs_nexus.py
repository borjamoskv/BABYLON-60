# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TESTS GEMINI LABS NEXUS | STATE: C5-REAL | VERIFICATION: PASSED
# ============================================================================
"""
test_gemini_labs_nexus.py — Unit and Integration tests for Gemini Labs Nexus.
"""

import json
import os
import pathlib
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.cortex.gemini_labs_nexus import (
    inject_language_context,
    generate_scitt_receipt,
    eval_code_with_sandbox,
)


def test_inject_language_context() -> None:
    base_prompt = "System prompt base."
    res = inject_language_context(base_prompt, "Hola, ¿cómo estás?")
    assert base_prompt in res


def test_generate_scitt_receipt() -> None:
    payload = "Test payload for SCITT receipt"
    claims = {"latency_ms": 12.34, "model": "gemini-2.5-pro"}
    receipt = generate_scitt_receipt(claims, payload)

    assert receipt["type"] == "GEMINI_LABS_C5_SCITT_RECEIPT"
    assert receipt["issuer"] == "did:c5real:babylon60:gemini_labs_nexus"
    assert "merkle_root_sha3_256" in receipt
    assert receipt["claims"]["c5_real_compliant"] is True
    assert receipt["claims"]["eu_ai_act_article_15_compliant"] is True


def test_eval_code_with_sandbox_safe() -> None:
    safe_code = "a = 5\nb = 10\nc = a + b"
    verdict = eval_code_with_sandbox(safe_code)
    assert verdict["is_safe"] is True
    assert len(verdict["violations"]) == 0


def test_eval_code_with_sandbox_unsafe() -> None:
    unsafe_code = "import os\nos.system('echo hacked')"
    verdict = eval_code_with_sandbox(unsafe_code)
    assert verdict["is_safe"] is False
    assert len(verdict["violations"]) > 0


def test_append_auto_log(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    from babylon60.cortex.gemini_labs_nexus import append_auto_log

    mock_log_file = tmp_path / "gemini_labs_telemetry.jsonl"
    monkeypatch.setattr("babylon60.cortex.gemini_labs_nexus.LOG_FILE", str(mock_log_file))

    from babylon60.cortex.gemini_labs_nexus import generate_scitt_receipt

    receipt = generate_scitt_receipt({"model": "gemini-2.5-pro"}, "test payload")
    append_auto_log("TEST_EVENT", {"prompt": "unit test prompt", "model": "gemini-2.5-pro"}, receipt)

    assert os.path.exists(mock_log_file)
    with open(mock_log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0
        last_entry = json.loads(lines[-1])
        assert "timestamp" in last_entry
        assert "scitt_receipt" in last_entry


if __name__ == "__main__":
    pytest.main([__file__])
