# C5-REAL EXERGY CERTIFIED
import re

with open('.agents/AGENTS.md', 'r') as f:
    content = f.read()

lines = content.split('\n')
out = []
num = 18

found_first_18 = False

for line in lines:
    if line.startswith('## 18.'):
        if not found_first_18:
            found_first_18 = True
            out.append(line)
        else:
            num += 1
            out.append(re.sub(r'## \d+\.', f'## {num}.', line))
    elif line.startswith('## '):
        match = re.match(r'## (\d+)\.', line)
        if match:
            current = int(match.group(1))
            if current >= 19:
                num += 1
                out.append(re.sub(r'## \d+\.', f'## {num}.', line))
            else:
                out.append(line)
        else:
            out.append(line)
    else:
        out.append(line)

with open('.agents/AGENTS.md', 'w') as f:
    f.write('\n'.join(out))

print("Fixed AGENTS.md")
