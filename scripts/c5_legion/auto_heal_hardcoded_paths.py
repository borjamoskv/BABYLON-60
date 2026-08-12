#!/usr/bin/env python3
"""
c5_legion_auto_heal.py - Auto-remediation for hardcoded absolute paths.
Uses Regex to safely extract the string content and wrap it in Path.home()
"""

import os
import re
from pathlib import Path

WORKSPACE_DIR = str(Path.home() / "10_PROJECTS" / "20_VAULT")
# Matches exactly a string literal containing the home path, e.g. "<home>/foo/bar"
# Group 1: Quote char (' or ")
# Group 2: The rest of the path after borjafernandezangulo/
# Group 3: Closing quote char (should match Group 1, but we'll assume it's valid code)
_HOME = str(Path.home())
PATTERN = re.compile(r'([\'"])' + re.escape(_HOME) + r'/([^\'"]*)([\'"])')

def heal_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False
        
    if _HOME + "/" not in content:
        return False
        
    lines = content.split('\n')
    has_pathlib = any("from pathlib import Path" in line for line in lines)
    has_os = any("import os" in line for line in lines)
    
    new_lines = []
    modified = False
    
    for line in lines:
        if _HOME + "/" in line:
            # We skip lines that might be docstrings or complex if they don't match simple quotes
            # or if they are already using f-strings (f")
            if 'f"' in line or "f'" in line:
                new_lines.append(line)
                continue
                
            # Replace: "<home>/path" -> str(Path.home() / "path")
            new_line = PATTERN.sub(r'str(Path.home() / "\2")', line)
            if new_line != line:
                modified = True
            line = new_line
            
        new_lines.append(line)
        
    if modified:
        # Add import if missing
        if not has_pathlib:
            if new_lines and new_lines[0].startswith("#!"):
                new_lines.insert(1, "from pathlib import Path")
            else:
                new_lines.insert(0, "from pathlib import Path")
                
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    return False

def main():
    print("[*] Initiating Auto-Heal Swarm on 20_VAULT for hardcoded paths (SAFE REGEX MODE)...")
    healed_count = 0
    for root, _, files in os.walk(WORKSPACE_DIR):
        if ".git" in root or "__pycache__" in root or "node_modules" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                filepath = os.path.join(root, f)
                if heal_file(filepath):
                    print(f"  [+] Healed: {os.path.relpath(filepath, WORKSPACE_DIR)}")
                    healed_count += 1
                    
    print(f"[*] Auto-Heal Complete. {healed_count} files remediated.")

if __name__ == "__main__":
    main()
