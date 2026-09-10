import os
import re

target_dir = "."

def fix_python_excepts(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return
        
    changed = False
    
    # Check if the file has any of the patterns
    if re.search(r'^[ \t]*except(?:\s+Exception)?\s*:\s*pass', content, flags=re.MULTILINE):
        if "import logging" not in content:
            content = "import logging\n" + content
            
        def replacer(match):
            indent = match.group(1)
            return f"{indent}except Exception as e:\n{indent}    logging.error(f'Traza Epistémica Perdida: {{e}}')"
            
        # Match indentation, 'except', optional ' Exception', ':', 'pass'
        new_content = re.sub(
            r'^([ \t]*)except(?:\s+Exception)?\s*:\s*pass',
            replacer,
            content,
            flags=re.MULTILINE
        )
        
        if new_content != content:
            content = new_content
            changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

for root, _, files in os.walk(target_dir):
    if any(ignored in root for ignored in ["/.git", "/target", "/fluid_lean", "/.xtts_venv", "/.venv", "/node_modules"]):
        continue
    for file in files:
        filepath = os.path.join(root, file)
        if file.endswith(".py") and "test_" not in file:
            fix_python_excepts(filepath)

print("Anergy purge completed (Python).")
