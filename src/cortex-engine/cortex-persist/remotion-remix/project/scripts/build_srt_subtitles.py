# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import json

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
SUBTITLES_FILE = os.path.join(PUBLIC_DIR, "sequel_subtitles.json")
ASS_FILE = os.path.join(PROJECT_DIR, "subtitles.ass")

print("=== GENERATING ADVANCED SUBSTATION ALPHA (.ASS) SUBTITLES ===")

with open(SUBTITLES_FILE, "r", encoding="utf-8") as f:
    subtitles = json.load(f)

# Convert BGR/ABGR hex for ASS format
def hex_to_ass_color(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        r, g, b = hex_str[0:2], hex_str[2:4], hex_str[4:6]
        return f"&H00{b}{g}{r}&"  # BGR order in ASS
    return "&H00FFFFFF&"

def format_ass_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

# Define Character Styles with distinct colors and sizes
styles_header = """[Script Info]
Title: El Intervalo Prohibido 2 Character Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

unique_speakers = {}
for sub in subtitles:
    spk = sub.get("speaker", "GON")
    color = sub.get("color", "#00F0FF")
    unique_speakers[spk] = hex_to_ass_color(color)

style_lines = []
for spk, ass_color in unique_speakers.items():
    style_lines.append(f"Style: {spk},Arial,32,{ass_color},&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,60,60,260,1")

events_header = """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

dialogue_lines = []
for sub in subtitles:
    start = format_ass_time(sub["startTime"])
    end = format_ass_time(sub["endTime"])
    spk = sub.get("speaker", "GON")
    avatar = sub.get("avatar", "🎙️")
    text = sub.get("text", "")
    dialogue_lines.append(f"Dialogue: 0,{start},{end},{spk},,0,0,0,,{avatar} {spk}\\N{text}")

ass_content = styles_header + "\n".join(style_lines) + events_header + "\n".join(dialogue_lines)

with open(ASS_FILE, "w", encoding="utf-8") as f:
    f.write(ass_content)

print("Generated Character ASS Subtitles file at:", ASS_FILE)
