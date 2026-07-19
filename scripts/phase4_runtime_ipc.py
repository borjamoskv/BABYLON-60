import os
import ast
import json
import re

def analyze_ipc_and_runtime(target_dir):
    report = {
        "network_endpoints": [],
        "ffi_bindings": [],
        "database_locks": [],
        "multiprocessing_ipc": []
    }
    
    for root, dirs, files in os.walk(target_dir):
        if any(x in root for x in ['.venv', 'node_modules', '__pycache__', '.git']):
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, target_dir)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        source = f.read()
                    
                    # 1. Detect Network endpoints & sockets
                    if "FastAPI" in source or "APIRouter" in source or "@app." in source or "@router." in source:
                        report["network_endpoints"].append({"file": rel_path, "type": "FastAPI Router"})
                    if "urllib.request" in source or "requests." in source or "httpx." in source:
                        report["network_endpoints"].append({"file": rel_path, "type": "HTTP Client"})
                    if "socket." in source:
                        report["network_endpoints"].append({"file": rel_path, "type": "Raw Socket"})
                        
                    # 2. Detect FFI / Rust / C bindings
                    if "ctypes" in source or "cffi" in source:
                        report["ffi_bindings"].append({"file": rel_path, "type": "C-FFI"})
                    # If it imports something that looks compiled
                    if re.search(r'import\s+(strike_rs|moskv_core)', source):
                        report["ffi_bindings"].append({"file": rel_path, "type": "Rust PyO3"})
                        
                    # 3. Detect SQLite Pragmas
                    if "busy_timeout" in source or "WAL" in source.upper():
                        report["database_locks"].append({"file": rel_path, "type": "SQLite WAL/Timeout"})
                        
                    # 4. Multiprocessing / Queue
                    if "asyncio.Queue" in source or "multiprocessing" in source or "threading" in source:
                        report["multiprocessing_ipc"].append({"file": rel_path, "type": "Concurrency primitive"})
                        
                except Exception:
                    pass
                    
    out_json = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/artifacts/reports/BABYLON_60_RUNTIME_IPC.json"
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, 'w') as f:
        json.dump(report, f, indent=2)
    print(out_json)

if __name__ == "__main__":
    analyze_ipc_and_runtime("/Users/borjafernandezangulo/BABYLON-60")
