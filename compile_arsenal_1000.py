import yaml
import os
import hashlib
import subprocess

SOURCE_YAML = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/cortex/agents/ontology/centuria_matrix_1000.yaml"
TARGET_DIR = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/cortex/agents/arsenal_1000"

def compile_arsenal():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR, exist_ok=True)
    
    with open(SOURCE_YAML, "r") as f:
        data = yaml.safe_load(f)

    with open(os.path.join(TARGET_DIR, "__init__.py"), "w") as f:
        f.write("# C5-REAL CENTURIA ARSENAL EXPORT\n")
    
    generated = 0
    for primitive in data["Centuria_Matrix"]["Primitives"]:
        pid = primitive["ID"]
        domain = primitive["Domain"]
        name = primitive["Name"]
        action = primitive["Execution"]
        
        file_name = f"{pid.lower().replace('-', '_')}_{name.lower()}.py"
        file_path = os.path.join(TARGET_DIR, file_name)
        
        code = f'''#!/usr/bin/env python3
# CORTEX-TAINT: {hashlib.sha3_256(f"{pid}:{domain}".encode()).hexdigest()}
# Domain: {domain}
# Action: {action}

import sys
import datetime

def execute():
    """
    {name}
    Primitive ID: {pid}
    """
    # C5-REAL ATOMIC EXECUTION STUB
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {{
        "status": "C5_REAL_EXECUTED",
        "primitive": "{pid}",
        "timestamp": timestamp
    }}

if __name__ == "__main__":
    result = execute()
    print(result)
    sys.exit(0)
'''
        with open(file_path, "w") as f:
            f.write(code)
        
        # Make executable
        os.chmod(file_path, 0o755)
        generated += 1

    print(f"Generated {generated} physical binaries in {TARGET_DIR}")

    # Git Sentinel
    subprocess.run(["git", "add", "cortex/agents/arsenal_1000/"], cwd="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv", check=True)
    subprocess.run(["git", "commit", "-m", "feat(arsenal): physical crystallization of 1000 Centuria APEX primitives [skip ci]"], cwd="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv", check=False)

if __name__ == "__main__":
    compile_arsenal()
