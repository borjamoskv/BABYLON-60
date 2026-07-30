# C5-REAL EXERGY CERTIFIED
"""Unit test suite for Zero-Trust Pipeline (runtime_wrapper.py & verify_receipt.py)."""

import json
import subprocess
from pathlib import Path
from scripts.verify_receipt import sha256_bytes

def test_zero_trust_pipeline_end_to_end(tmp_path, monkeypatch):
    # Setup test plan
    target_file = "tmp_test_target.txt"
    plan_data = {
        "version": "1.0",
        "declared_targets": [target_file],
        "actions": [
            {"type": "write_file", "path": target_file, "mode": "write", "content": "C5-REAL Zero Trust Test\n"}
        ],
    }
    plan_path = tmp_path / "test_plan.json"
    plan_path.write_text(json.dumps(plan_data), encoding="utf-8")

    # Run runtime wrapper command
    cmd = ["python3", "scripts/runtime_wrapper.py", str(plan_path), "--outdir", ".audit/receipts"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    res = json.loads(proc.stdout)
    assert res["PASS"] is True
    assert len(res["undeclared"]) == 0

    receipt_path = Path(res["receipt"])
    assert receipt_path.exists()

    # Run verify receipt command
    cmd_verify = ["python3", "scripts/verify_receipt.py", str(receipt_path)]
    proc_verify = subprocess.run(cmd_verify, capture_output=True, text=True)
    assert proc_verify.returncode == 0
    res_verify = json.loads(proc_verify.stdout)
    assert res_verify["PASS"] is True

    # Clean up test file
    Path(target_file).unlink(missing_ok=True)

def test_verify_receipt_tamper_detection(tmp_path):
    receipt_data = {"version": "1.0", "run_id": "test_run", "file_hashes": {}, "undeclared_mutations": []}
    # Calculate valid self_hash
    receipt_bytes = json.dumps(receipt_data, sort_keys=True).encode("utf-8")
    receipt_data["self_hash"] = sha256_bytes(receipt_bytes)

    # Tamper with receipt data
    receipt_data["tampered_field"] = "adversarial_injection"

    tampered_path = tmp_path / "tampered_receipt.json"
    tampered_path.write_text(json.dumps(receipt_data), encoding="utf-8")

    cmd = ["python3", "scripts/verify_receipt.py", str(tampered_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode != 0
    res = json.loads(proc.stdout)
    assert res["PASS"] is False
    assert any("SELF_HASH_MISMATCH" in e for e in res["errors"])
