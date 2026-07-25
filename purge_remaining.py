# C5-REAL EXERGY CERTIFIED
import os
import re

root_dir = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
# Regex patterns
# Match `| *CORTEX-TAINT:* ... `
p1 = re.compile(r'\|\s*\*CORTEX-TAINT:\*\s*`[^`]+`\s*')
# Match `[CORTEX-TAINT:...]`
p2 = re.compile(r'\[CORTEX-TAINT:[^\]]+\]')
# Match `- **CORTEX-TAINT**: `...``
p3 = re.compile(r'-\s*\*\*CORTEX-TAINT\*\*:\s*`[^`]+`\n?')
# Match `> **CORTEX-TAINT**: `...``
p4 = re.compile(r'>\s*\*\*CORTEX-TAINT\*\*:\s*`[^`]+`\n?')
# Match `// CORTEX-TAINT: ...`
p5 = re.compile(r'//\s*CORTEX-TAINT:.*\n?')
# Match `CORTEX_TAINT: [...]`
p6 = re.compile(r'CORTEX_TAINT:\s*\[CORTEX-TAINT:[^\]]+\]\n?')
# Match `- **CORTEX-TAINT Signature:** ...`
p7 = re.compile(r'-\s*\*\*CORTEX-TAINT Signature:\*\*\s*`[^`]+`\n?')

count = 0

for root, dirs, files in os.walk(root_dir):
    if '.git' in root or '.gemini' in root:
        continue
    for f in files:
        if f.endswith('.md'):
            path = os.path.join(root, f)
            if path.endswith('AGENTS.md') or not os.path.exists(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except (OSError, UnicodeDecodeError):
                continue

            orig = content
            content = p1.sub('', content)
            content = p2.sub('', content)
            content = p3.sub('', content)
            content = p4.sub('', content)
            content = p5.sub('', content)
            content = p6.sub('', content)
            content = p7.sub('', content)

            # Clean up empty list items or double pipes
            content = content.replace('||', '|')
            content = re.sub(r'\|\s*\|', '|', content)

            if content != orig:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                count += 1
print(f"Purged {count} additional files.")
