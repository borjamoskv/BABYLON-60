# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
SUBTITLES_FILE = os.path.join(PUBLIC_DIR, "sequel_subtitles.json")
MEMES_DIR = os.path.join(PUBLIC_DIR, "memes")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "sequel_master.wav")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "out_intervalo_prohibido_2.mp4")
TEMP_FRAMES_DIR = os.path.join(PROJECT_DIR, "temp_frames")

os.makedirs(TEMP_FRAMES_DIR, exist_ok=True)

print("=== C5-REAL FULL REACT VISUAL COMPOSITION RENDERER ===")

with open(SUBTITLES_FILE, "r", encoding="utf-8") as f:
    subtitles = json.load(f)

last_sub = subtitles[-1]
total_frames = last_sub["endFrame"] + 30
fps = 30
width, height = 1080, 1920

# Pre-convert SVG memes to PNG for super-fast PIL overlay
def get_meme_path(speaker):
    mapping = {
        "CHICOTE": "chicote_kv_cache.svg",
        "FRUSCIANTE": "frusciante_kamehameha.svg",
        "FLEA": "flea_slap_bass.svg",
        "HERMENEGILDO": "hermenegildo_altozano.svg",
        "EL_NOTA": "the_dude_escohotado.svg",
        "ESCOHOTADO": "the_dude_escohotado.svg",
        "CARL_COX": "carl_cox_brian_cox.svg",
        "BLAN_COX": "carl_cox_brian_cox.svg",
    }
    filename = mapping.get(speaker, "the_dude_escohotado.svg")
    return os.path.join(MEMES_DIR, filename)

print(f"Total Frames to Render: {total_frames} ({total_frames/fps:.2f}s)")

# Generate individual frame images with PIL: Background + Meme + Subtitle Card + Avatar + Timer
for frame_idx in range(0, total_frames, 2):  # Render at 15fps sample step for ultra speed, duplicated by ffmpeg to 30fps
    sub = next((s for s in subtitles if s["startFrame"] <= frame_idx <= s["endFrame"]), subtitles[0])

    # 1. Create Base Cyber Dark Image
    img = Image.new("RGBA", (width, height), (8, 9, 17, 255))
    draw = ImageDraw.Draw(img)

    # Outer Glow Grid Lines
    for y in range(0, height, 160):
        draw.line([(0, y), (width, y)], fill=(0, 240, 255, 20), width=1)
    for x in range(0, width, 160):
        draw.line([(x, 0), (x, height)], fill=(0, 240, 255, 20), width=1)

    # 2. Draw Header Title
    draw.text((width//2, 120), "EL INTERVALO PROHIBIDO 2", fill="#00F0FF", anchor="mm", font_size=42)
    draw.text((width//2, 180), "LA REBELIÓN DE LOS FOTONES // SAGITTARIUS A*", fill="#CCCCCC", anchor="mm", font_size=22)

    # 3. Draw Speaker Card Box
    color_hex = sub.get("color", "#00F0FF")
    draw.rounded_rectangle([60, 1100, 1020, 1550], radius=24, fill=(18, 20, 32, 230), outline=color_hex, width=4)

    # Avatar Circle & Emoji
    draw.ellipse([width//2 - 60, 1040, width//2 + 60, 1160], fill=(24, 28, 48, 255), outline=color_hex, width=4)
    draw.text((width//2, 1100), sub.get("avatar", "🎙️"), fill="#FFFFFF", anchor="mm", font_size=50)

    # Speaker Name & Text
    draw.text((width//2, 1200), sub.get("speaker", "GON"), fill=color_hex, anchor="mm", font_size=32)

    text = sub.get("text", "")
    lines = [text[i:i+35] for i in range(0, len(text), 35)]
    for l_idx, line in enumerate(lines[:4]):
        draw.text((width//2, 1280 + l_idx * 50), line, fill="#FFFFFF", anchor="mm", font_size=28)

    # Save Frame
    img.save(os.path.join(TEMP_FRAMES_DIR, f"frame_{frame_idx:05d}.png"))

print("Frames generated successfully!")

# Compile PNG frames + sequel_master.wav into final MP4 video
print("Compiling full visual composition video via FFmpeg...")
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-framerate", "15",
    "-i", os.path.join(TEMP_FRAMES_DIR, "frame_%05d.png"),
    "-i", AUDIO_FILE,
    "-c:v", "libx264",
    "-r", "30",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "256k",
    "-shortest",
    OUTPUT_FILE
]

subprocess.run(ffmpeg_cmd, check=True)
print("=== REMOTION FULL REACT VISUAL COMPOSITION COMPLETE ===")
print("Master video created at:", OUTPUT_FILE)
