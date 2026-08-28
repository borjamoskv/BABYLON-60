#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - AUTOMATED CI VERIFIER FOR MCP C-ABI
# file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/scripts/verify_mcp_cabi.py

import sys
import os
import json
import subprocess

def main():
    print("=== C5-REAL AUTOMATED CI VERIFIER: MCP C-ABI & LANDAUER PURGE ===")
    mcp_script = "src/06_apps/mcp_c5_abi_bridge/mcp_server.py"

    if not os.path.exists(mcp_script):
        print(f"FAIL: {mcp_script} not found!")
        sys.exit(1)

    proc = subprocess.Popen(
        ["python3", mcp_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 1. Test Initialize
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    init_resp = json.loads(proc.stdout.readline())
    assert init_resp["result"]["serverInfo"]["name"] == "mcp-c5-abi-bridge-gen2"
    print("✓ Initialize Handshake: PASS")

    # 2. Test Purge Context
    test_text = "IMPORTANTE: Verificación de CI extremadamente rápida y básicamente genial."
    purge_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "c5_purge_context",
            "arguments": {"raw_text": test_text}
        }
    }
    proc.stdin.write(json.dumps(purge_req) + "\n")
    proc.stdin.flush()
    purge_resp = json.loads(proc.stdout.readline())
    content = json.loads(purge_resp["result"]["content"][0]["text"])
    assert "purged_text" in content
    print(f"✓ Landauer Context Purge ({content['anergy_reduction_pct']} saved): PASS")

    # 3. Test SCITT COSE Attestation
    exec_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "c5_abi_execute",
            "arguments": {"command_id": "CI_GATE_VERIFY", "payload": "COMMITTING_GREEN_CI"}
        }
    }
    proc.stdin.write(json.dumps(exec_req) + "\n")
    proc.stdin.flush()
    exec_resp = json.loads(proc.stdout.readline())
    exec_content = json.loads(exec_resp["result"]["content"][0]["text"])
    assert exec_content["attestation"]["status"] == "ATTESTED_GEN2"
    print(f"✓ SCITT COSE Attestation Digest ({exec_content['attestation']['scitt_receipt']['digest_sha3_256'][:8]}...): PASS")

    proc.terminate()
    print("\nSUCCESS: All C5-REAL MCP C-ABI Gate Verifications PASSED cleanly.")

if __name__ == "__main__":
    main()
