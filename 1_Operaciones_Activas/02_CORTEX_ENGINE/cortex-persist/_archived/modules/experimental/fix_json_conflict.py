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
    elif line.startswith(">>>>>>> origin/main"):
        in_origin = False
        continue

    if in_origin:
        continue

    new_lines.append(line)

with open("config/llm_presets.json", "w") as f:
    f.writelines(new_lines)
