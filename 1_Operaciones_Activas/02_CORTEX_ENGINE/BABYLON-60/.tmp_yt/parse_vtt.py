# C5-REAL EXERGY CERTIFIED
import sys
import re

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

text_lines = []
last_line = ""

for line in lines:
    line = line.strip()
    if not line: continue
    # Skip VTT header and timestamps
    if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or line.startswith('Style:') or '-->' in line or re.match(r'^[0-9:\.]+$', line):
        continue
    # Remove tags like <c>, <i>, <00:00:00.000>
    clean_line = re.sub(r'<[^>]+>', '', line).strip()
    if clean_line and clean_line != last_line:
        # Check if the clean_line is mostly the same as last_line but with one new word (rolling captions)
        if last_line and clean_line.startswith(last_line):
            # Just take the new part? It's easier to just accumulate.
            # Actually, standard youtube vtt has this:
            # 00:00:00.000 --> 00:00:01.000
            # hello
            # 00:00:01.000 --> 00:00:02.000
            # hello world
            # So `clean_line` might be "hello world" and `last_line` was "hello".
            pass
        text_lines.append(clean_line)
        last_line = clean_line

# Since Youtube rolling captions are very redundant, let's do a better deduplication
# For every line, if it starts with the previous line, we can just replace the previous line
final_lines = []
for line in text_lines:
    if final_lines and line.startswith(final_lines[-1]):
        final_lines[-1] = line
    else:
        # sometimes it overlaps partially
        final_lines.append(line)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Transcripción: Superdotado con 165 de CI\n\n")
    paragraph = []
    for line in final_lines:
        paragraph.append(line)
        if len(paragraph) >= 15:
            f.write(" ".join(paragraph) + "\n\n")
            paragraph = []
    if paragraph:
        f.write(" ".join(paragraph) + "\n\n")
