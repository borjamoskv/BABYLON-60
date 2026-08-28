#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - VERIFICATION SUITE
# file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/06_apps/mcp_c5_abi_bridge/test_poc.py

import subprocess
import json

def run_test():
    proc = subprocess.Popen(
        ["python3", "src/06_apps/mcp_c5_abi_bridge/mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 1. Initialize
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    init_resp = json.loads(proc.stdout.readline())
    print("=== 1. INITIALIZE RESPONSE ===")
    print(json.dumps(init_resp, indent=2))

    # 2. List Tools
    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    proc.stdin.write(json.dumps(list_req) + "\n")
    proc.stdin.flush()
    list_resp = json.loads(proc.stdout.readline())
    print("\n=== 2. TOOLS/LIST RESPONSE ===")
    tools_names = [t["name"] for t in list_resp["result"]["tools"]]
    print(f"Herramientas expuestas ({len(tools_names)}): {tools_names}")

    # 3. Test c5_purge_context
    raw_payload = (
        "IMPORTANTE: El sistema de auditoría es increíblemente rápido y básicamente "
        "comprueba que el rendimiento es excelente y muy estable, lo cual es obviamente genial."
    )
    purge_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "c5_purge_context",
            "arguments": {"raw_text": raw_payload}
        }
    }
    proc.stdin.write(json.dumps(purge_req) + "\n")
    proc.stdin.flush()
    purge_resp = json.loads(proc.stdout.readline())
    print("\n=== 3. C5_PURGE_CONTEXT TEST ===")
    purged_data = json.loads(purge_resp["result"]["content"][0]["text"])
    print(json.dumps(purged_data, indent=2))

    # 4. Test c5_abi_execute with SCITT Receipt
    exec_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "c5_abi_execute",
            "arguments": {
                "command_id": "CMD_KERNEL_STATE_SYNC",
                "payload": "ESTADO_CRÍTICO: Sincronizando buffers de memoria C-ABI de forma muy segura."
            }
        }
    }
    proc.stdin.write(json.dumps(exec_req) + "\n")
    proc.stdin.flush()
    exec_resp = json.loads(proc.stdout.readline())
    print("\n=== 4. C5_ABI_EXECUTE (SCITT ATTESTATION) TEST ===")
    exec_data = json.loads(exec_resp["result"]["content"][0]["text"])
    print(json.dumps(exec_data, indent=2))

    proc.terminate()

if __name__ == "__main__":
    run_test()
