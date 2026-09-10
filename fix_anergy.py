import os
import re

target_dir = "."

def fix_rust_unwraps(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return
    
    changed = False
    
    if "exergy_binary_ipc.rs" in filepath:
        new_content = re.sub(
            r'\.try_into\(\)\.unwrap\(\)',
            r'.try_into().map_err(|_| anyhow::anyhow!("B60IPC slice bounds violation"))?',
            content
        )
        if new_content != content:
            content = new_content
            changed = True
    
    if "hypervisor.rs" in filepath:
        new_content = re.sub(
            r'h\.join\(\)\.unwrap\(\);',
            r'if let Err(e) = h.join() { tracing::error!("Worker thread paniqued: {:?}", e); }',
            content
        )
        if new_content != content:
            content = new_content
            changed = True
            
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def fix_python_excepts(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return
        
    changed = False
    if re.search(r'except\s*:\s*pass|except\s+Exception\s*:\s*pass', content):
        if "import logging" not in content:
            content = "import logging\n" + content
            
        content = re.sub(
            r'(except\s*:\s*)pass',
            r'\g<1>logging.error("Traza Epistémica Perdida: Excepción silenciosa capturada.")',
            content
        )
        content = re.sub(
            r'(except\s+Exception)\s*:\s*pass',
            r'\g<1> as e:\n            logging.error(f"Traza Epistémica Perdida: {e}")',
            content
        )
        changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

for root, _, files in os.walk(target_dir):
    if any(ignored in root for ignored in ["/.git", "/target", "/fluid_lean", "/.xtts_venv", "/.venv", "/node_modules"]):
        continue
    for file in files:
        filepath = os.path.join(root, file)
        if file.endswith(".rs") and "tests" not in filepath:
            fix_rust_unwraps(filepath)
        elif file.endswith(".py") and "test_" not in file:
            fix_python_excepts(filepath)

print("Anergy purge completed.")
