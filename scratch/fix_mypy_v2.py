import os
import re

def fix_file(path):
    with open(path, 'r') as f:
        content = f.read()
    
    # Simple regex to find function defs missing a return type annotation
    # It looks for "def foo(" and the closing "):" without "->"
    # We will just replace "):" with ") -> None:" for lines that have "def " and don't have "->"
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('def ') and '->' not in line and line.rstrip().endswith(':'):
            lines[i] = line.rstrip()[:-1] + ' -> None:'
            
    with open(path, 'w') as f:
        f.write('\n'.join(lines))

for root, dirs, files in os.walk('cortex'):
    for f in files:
        if f.endswith('.py'):
            fix_file(os.path.join(root, f))
            
for root, dirs, files in os.walk('scripts'):
    for f in files:
        if f.endswith('.py'):
            fix_file(os.path.join(root, f))
