import os
import re

def fix_file(path):
    with open(path, 'r') as f:
        content = f.read()
    
    # Replace def test_name(): with def test_name() -> None:
    content = re.sub(r'def (test_[a-zA-Z0-9_]+)\(\):', r'def \1() -> None:', content)
    
    with open(path, 'w') as f:
        f.write(content)

for root, dirs, files in os.walk('cortex'):
    for f in files:
        if f.endswith('_test.py'):
            fix_file(os.path.join(root, f))
