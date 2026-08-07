# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import json
import subprocess

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
SUBTITLES_FILE = os.path.join(PUBLIC_DIR, "sequel_subtitles.json")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "sequel_master.wav")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "out_intervalo_prohibido_2.mp4")
SRT_FILE = os.path.join(PROJECT_DIR, "subtitles.srt")

print("=== FFMPEG BURNED SUBTITLE COMPOSITION RENDERER ===")

with open(SUBTITLES_FILE, "r", encoding="utf-8") as f:
    subtitles = json.load(f)

# Convert subtitles.json to standard SRT format for FFmpeg subtitle burning
def format_srt_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

srt_lines = []
for idx, sub in enumerate(subtitles, 1):
    start = format_srt_time(sub["startTime"])
    end = format_srt_time(sub["endTime"])
    speaker = sub.get("speaker", "GON")
    avatar = sub.get("avatar", "🎙️")
    text = sub.get("text", "")
    srt_lines.append(f"{idx}\n{start} --> {end}\n{avatar} [{speaker}]: {text}\n")

with open(SRT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(srt_lines))

print("Created SRT Subtitles file at:", SRT_FILE)

# FFmpeg render: Dual reactive audio visualizer + Burned High-Vis Subtitles + Header Title
filter_complex = (
    "[0:a]showwaves=s=1080x960:mode=line:colors=0x00F0FF|0xFF00FF[waves];"
    "[0:a]showspectrum=s=1080x960:mode=combined:color=rainbow:scale=log:saturation=3[spec];"
    "[waves][spec]vstack[vbase];"
    f"[vbase]subtitles='{SRT_FILE}':force_style='FontSize=24,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=180'[vsub];"
    "[vsub]drawtext=text='EL INTERVALO PROHIBIDO 2':x=(w-text_w)/2:y=80:fontsize=44:fontcolor=0x00F0FF:shadowcolor=black:shadowx=3:shadowy=3[v]"
)

cmd = [
    "ffmpeg", "-y",
    "-i", AUDIO_FILE,
    "-filter_complex", filter_complex,
    "-map", "[v]",
    "-map", "0:a",
    "-c:v", "libx264",
    "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "256k",
    OUTPUT_FILE
]

print("Executing Subtitle Burned Render...")
subprocess.run(cmd, check=True)
print("=== RENDER COMPLETE WITH SUBTITLES ===")
print("Master video created at:", OUTPUT_FILE)
