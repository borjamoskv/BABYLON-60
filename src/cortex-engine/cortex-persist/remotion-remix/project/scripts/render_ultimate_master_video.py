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

print("=== C5-REAL ULTIMATE MASTER VIDEO RENDER PIPELINE ===")

with open(SUBTITLES_FILE, "r", encoding="utf-8") as f:
    subtitles = json.load(f)

last_sub = subtitles[-1]
total_frames = last_sub["endFrame"] + 30
fps = 30
width, height = 1080, 1920

# Map speakers to meme images
def get_meme_filename(speaker):
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
    return mapping.get(speaker, "the_dude_escohotado.svg")

# Pre-render SVG memes to PNG for ultra-fast composition
def convert_svgs():
    for f in os.listdir(MEMES_DIR):
        if f.endswith(".svg"):
            svg_path = os.path.join(MEMES_DIR, f)
            png_path = os.path.join(MEMES_DIR, f.replace(".svg", ".png"))
            cmd = ["ffmpeg", "-y", "-i", svg_path, "-vf", "scale=900:600", png_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

convert_svgs()
print("SVG Meme graphics converted to high-res PNG cards.")

print(f"Rendering {total_frames} frames of full UI composition...")

# Render frame sequence
for frame_idx in range(0, total_frames, 2):
    sub = next((s for s in subtitles if s["startFrame"] <= frame_idx <= s["endFrame"]), subtitles[0])
    color_hex = sub.get("color", "#00F0FF")
    speaker = sub.get("speaker", "GON")
    avatar = sub.get("avatar", "🎙️")
    text = sub.get("text", "")

    # Base Background Image
    img = Image.new("RGBA", (width, height), (8, 9, 17, 255))
    draw = ImageDraw.Draw(img)

    # Grid Lines
    for y in range(0, height, 160):
        draw.line([(0, y), (width, y)], fill=(0, 240, 255, 25), width=1)
    for x in range(0, width, 160):
        draw.line([(x, 0), (x, height)], fill=(0, 240, 255, 25), width=1)

    # Header Title
    draw.text((width//2, 100), "EL INTERVALO PROHIBIDO 2", fill="#00F0FF", anchor="mm", font_size=44)
    draw.text((width//2, 155), "LA REBELIÓN DE LOS FOTONES // SAGITTARIUS A*", fill="#CCCCCC", anchor="mm", font_size=22)

    # Overlay Meme Image Card if available
    meme_filename = get_meme_filename(speaker).replace(".svg", ".png")
    meme_path = os.path.join(MEMES_DIR, meme_filename)
    if os.path.exists(meme_path):
        try:
            meme_img = Image.open(meme_path).convert("RGBA").resize((900, 600))
            img.paste(meme_img, (90, 220), meme_img)
        except Exception as e:
            pass

    # Subtitle Speaker Card Box
    draw.rounded_rectangle([60, 1100, 1020, 1560], radius=28, fill=(18, 20, 32, 240), outline=color_hex, width=5)

    # Speaker Avatar Badge Circle
    draw.ellipse([width//2 - 65, 1035, width//2 + 65, 1165], fill=(24, 28, 48, 255), outline=color_hex, width=5)
    draw.text((width//2, 1100), avatar, fill="#FFFFFF", anchor="mm", font_size=52)

    # Speaker Name & Dialogue Lines
    draw.text((width//2, 1205), speaker, fill=color_hex, anchor="mm", font_size=34)

    lines = [text[i:i+32] for i in range(0, len(text), 32)]
    for l_idx, line in enumerate(lines[:4]):
        draw.text((width//2, 1285 + l_idx * 52), line, fill="#FFFFFF", anchor="mm", font_size=28)

    img.save(os.path.join(TEMP_FRAMES_DIR, f"frame_{frame_idx:05d}.png"))

print("All UI frames generated successfully!")

# Final FFmpeg Master Encoding: Merge PNG Frames + Dual Spectrum Audio Reactivity + Master Audio
filter_complex = (
    "[0:v]fps=30[vbase];"
    "[1:a]showwaves=s=1080x280:mode=line:colors=0x00F0FF|0xFF00FF[waves];"
    "[vbase][waves]overlay=0:1640[vmaster];"
    "[1:a]volume=2.2,pan=stereo|c0=c0|c1=c0[aout]"
)

cmd = [
    "ffmpeg", "-y",
    "-framerate", "15",
    "-i", os.path.join(TEMP_FRAMES_DIR, "frame_%05d.png"),
    "-i", AUDIO_FILE,
    "-filter_complex", filter_complex,
    "-map", "[vmaster]",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "256k",
    "-shortest",
    OUTPUT_FILE
]

print("Executing Final Master FFmpeg Compilation...")
subprocess.run(cmd, check=True)
print("=== ULTIMATE MASTER VIDEO RENDER COMPLETE ===")
print("Master video created at:", OUTPUT_FILE)
