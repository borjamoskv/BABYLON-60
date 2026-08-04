#!/usr/bin/env python3
import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADER_CONTENT_PY = """# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""

HEADER_CONTENT_RS = """// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
"""

MYTHOLOGICAL_REPLACEMENTS = {
    r'\bmagia\b': 'determinismo causal',
    r'\bmagical\b': 'deterministic',
    r'\bmagic\b': 'deterministic',
    r'\boráculo\b': 'atestador',
    r'\boracle\b': 'attestor',
    r'\bBFT\s*Local\b': 'Causal Mesh Attestation',
    
    r'\bMagia\b': 'Determinismo Causal',
    r'\bMagical\b': 'Deterministic',
    r'\bMagic\b': 'Deterministic',
    r'\bOráculo\b': 'Atestador',
    r'\bOracle\b': 'Attestor'
}

def fix_file(filepath, issues):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 1. Replace Mythological Terms
        for issue in issues:
            if issue['type'] == 'MythologicalTerm':
                for pattern, replacement in MYTHOLOGICAL_REPLACEMENTS.items():
                    content = re.sub(pattern, replacement, content)
                    
        # 2. Add Missing Headers
        has_missing_header = any(i['type'] == 'MissingHeader' for i in issues)
        if has_missing_header:
            if filepath.endswith('.py'):
                # Avoid inserting before a shebang or encoding declaration
                lines = content.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines[:5]):
                    if line.startswith('#!') or 'coding:' in line:
                        insert_idx = i + 1
                
                content = '\n'.join(lines[:insert_idx]) + ('' if insert_idx == 0 else '\n') + HEADER_CONTENT_PY + '\n'.join(lines[insert_idx:])
            elif filepath.endswith('.rs'):
                content = HEADER_CONTENT_RS + content
                
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Failed to fix {filepath}: {e}")
        return False

def main():
    report_path = os.path.join(REPO_ROOT, 'scratch', 'audit_report.json')
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
        
    fixed_count = 0
    for item in report:
        filepath = item['file']
        issues = item.get('issues', [])
        if any(i['type'] in ('MythologicalTerm', 'MissingHeader') for i in issues):
            if fix_file(filepath, issues):
                fixed_count += 1
                
    print(f"Successfully fixed {fixed_count} files.")

if __name__ == '__main__':
    main()
