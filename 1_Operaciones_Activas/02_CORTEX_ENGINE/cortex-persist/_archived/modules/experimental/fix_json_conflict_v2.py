import re

with open("config/llm_presets.json", "r") as f:
    lines = f.readlines()

new_lines = []
in_head = False
in_origin = False

for line in lines:
    if line.startswith("<<<<<<< HEAD"):
        in_head = True
        continue
    elif line.startswith("======="):
        in_head = False
        in_origin = True
        continue
    elif line.startswith(">>>>>>> feat/llm-routing-hardened"):
        in_origin = False
        continue

    if in_head:
        # We will keep HEAD
        new_lines.append(line)
        continue
    if in_origin:
        # We discard origin
        continue

    new_lines.append(line)

with open("config/llm_presets.json", "w") as f:
    f.writelines(new_lines)

with open("babylon60/extensions/llm/_presets.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_head = False
in_origin = False

for line in lines:
    if line.startswith("<<<<<<< HEAD"):
        in_head = True
        continue
    elif line.startswith("======="):
        in_head = False
        in_origin = True
        continue
    elif line.startswith(">>>>>>> feat/llm-routing-hardened"):
        in_origin = False
        continue

    if in_head:
        new_lines.append(line)
        continue
    if in_origin:
        continue

    new_lines.append(line)

with open("babylon60/extensions/llm/_presets.py", "w") as f:
    f.writelines(new_lines)
