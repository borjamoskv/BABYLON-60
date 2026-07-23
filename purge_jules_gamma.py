import glob
import re

dirs = [
    '/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/*.md',
    '/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/artifacts/*.md'
]

files = []
for d in dirs:
    files.extend(glob.glob(d))

# Regex patterns for the TAINT
patterns = [
    r'\s*\|\s*\*CORTEX-TAINT:\*\s*`?[^`|\n]+`?\s*',
    r'(?m)^CORTEX_TAINT:\s*\[CORTEX-TAINT:[^\]]+\]\n?',
    r'\[CORTEX-TAINT:[^\]]+\]'
]

changed_files = 0

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for p in patterns:
            new_content = re.sub(p, '', new_content)
            
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            changed_files += 1
            print(f"Purged TAINT from: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

print(f"Total files purged: {changed_files}")
