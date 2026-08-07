# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import json
import subprocess
from PIL import Image, ImageDraw

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
SUBTITLES_FILE = os.path.join(PUBLIC_DIR, "sequel_subtitles.json")
MEMES_DIR = os.path.join(PUBLIC_DIR, "memes")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "sequel_master.wav")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "out_intervalo_prohibido_2.mp4")
TEMP_FRAMES_DIR = os.path.join(PROJECT_DIR, "temp_frames")

os.makedirs(TEMP_FRAMES_DIR, exist_ok=True)

print("=== C5-REAL CHARACTER MEME & UI VIDEO COMPILER ===")

with open(SUBTITLES_FILE, "r", encoding="utf-8") as f:
    subtitles = json.load(f)

CHARACTER_DATA = {
    "GON": {"title": "GON — COMANDANTE DE LA FLOTA", "icon": "⏱️", "color": (0, 240, 255), "meme": "carl_cox_brian_cox.png"},
    "CHICOTE": {"title": "ALBERTO CHICOTE AUDITANDO LA IA", "icon": "👨‍🍳", "color": (255, 51, 51), "meme": "chicote_kv_cache.png"},
    "RASPUTIN": {"title": "RASPUTÍN NAVEGANDO HOYOS NEGROS", "icon": "🪆", "color": (153, 51, 255), "meme": "hermenegildo_altozano.png"},
    "CHE_JARANA": {"title": "EL CHE JARANA // RUMBA GALÁCTICA", "icon": "🎸", "color": (255, 153, 0), "meme": "flea_slap_bass.png"},
    "CARL_COX": {"title": "CARL COX AT THE DECKS (128 BPM)", "icon": "🎧", "color": (0, 255, 102), "meme": "carl_cox_brian_cox.png"},
    "BLAN_COX": {"title": "BLAN COX // EL INTERVALO CÓSMICO", "icon": "🌌", "color": (255, 0, 255), "meme": "carl_cox_brian_cox.png"},
    "FRUSCIANTE": {"title": "JOHN FRUSCIANTE // KAMEHAMEHA SOLO", "icon": "🎸", "color": (255, 215, 0), "meme": "frusciante_kamehameha.png"},
    "FLEA": {"title": "FLEA EN LEOPARDO // SLAP BASS 432Hz", "icon": "⚡", "color": (255, 102, 0), "meme": "flea_slap_bass.png"},
    "RAMONCIN": {"title": "RAMONCÍN // CANON SGAE GALÁCTICO", "icon": "🕶️", "color": (255, 0, 85), "meme": "frusciante_kamehameha.png"},
    "HERMENEGILDO": {"title": "HERMENEGILDO ALTOZANO // DO MENOR", "icon": "🎹", "color": (0, 255, 204), "meme": "hermenegildo_altozano.png"},
    "EL_NOTA": {"title": "EL NOTA (THE DUDE) // RUSOS BLANCOS", "icon": "🍹", "color": (204, 204, 0), "meme": "the_dude_escohotado.png"},
    "ESCOHOTADO": {"title": "ANTONIO ESCOHOTADO // MANIFIESTO", "icon": "💨", "color": (212, 175, 55), "meme": "the_dude_escohotado.png"},
    "DR_POPPEL": {"title": "DR. ERNST PÖPPEL // VENTANA 2.8s", "icon": "🔬", "color": (255, 255, 0), "meme": "carl_cox_brian_cox.png"},
    "DON_SANTIAGO": {"title": "DON SANTIAGO // CECINA EN GRAVEDAD CERO", "icon": "🥖", "color": (204, 153, 102), "meme": "the_dude_escohotado.png"},
    "KIMI_K3": {"title": "KIMI-K3 APEX // IA EN HUMO", "icon": "🤖", "color": (51, 255, 255), "meme": "chicote_kv_cache.png"},
    "PAUSA": {"title": "PAUSA SOBERANA DE 2.8 SEGUNDOS", "icon": "⏳", "color": (255, 255, 255), "meme": "the_dude_escohotado.png"}
}

last_sub = subtitles[-1]
total_frames = last_sub["endFrame"] + 30
width, height = 1080, 1920

print(f"Rendering {total_frames} frames with full character cards...")

for frame_idx in range(0, total_frames, 2):
    sub = next((s for s in subtitles if s["startFrame"] <= frame_idx <= s["endFrame"]), subtitles[0])
    spk = sub.get("speaker", "GON")
    text = sub.get("text", "")
    info = CHARACTER_DATA.get(spk, CHARACTER_DATA["GON"])
    rgb_color = info["color"]

    img = Image.new("RGBA", (width, height), (8, 9, 17, 255))
    draw = ImageDraw.Draw(img)

    # Background Grid
    for y in range(0, height, 160):
        draw.line([(0, y), (width, y)], fill=(0, 240, 255, 20), width=1)
    for x in range(0, width, 160):
        draw.line([(x, 0), (x, height)], fill=(0, 240, 255, 20), width=1)

    # Header Title
    draw.text((width//2, 90), "EL INTERVALO PROHIBIDO 2", fill="#00F0FF", anchor="mm")
    draw.text((width//2, 130), "LA REBELION DE LOS FOTONES // SAGITTARIUS A*", fill="#CCCCCC", anchor="mm")

    # Character Card Box in Upper Half (Meme Card Area)
    draw.rounded_rectangle([70, 180, 1010, 840], radius=24, fill=(18, 22, 38, 240), outline=rgb_color, width=5)

    # Overlay Meme Image Card if exists
    meme_file = info.get("meme", "the_dude_escohotado.png")
    meme_path = os.path.join(MEMES_DIR, meme_file)
    if os.path.exists(meme_path):
        try:
            meme_img = Image.open(meme_path).convert("RGBA").resize((880, 580))
            img.paste(meme_img, (100, 220), meme_img)
        except Exception:
            pass

    # Lower Dialogue Card Box
    draw.rounded_rectangle([60, 1140, 1020, 1580], radius=24, fill=(16, 18, 30, 240), outline=rgb_color, width=5)
    draw.text((width//2, 1210), f"{info['icon']}  {spk}", fill=rgb_color, anchor="mm")

    lines = [text[i:i+34] for i in range(0, len(text), 34)]
    for l_idx, line in enumerate(lines[:4]):
        draw.text((width//2, 1290 + l_idx * 48), line, fill="#FFFFFF", anchor="mm")

    frame_path = os.path.join(TEMP_FRAMES_DIR, f"frame_{frame_idx:05d}.png")
    img.save(frame_path)

print("All character UI frames generated!")

filter_complex = (
    "[0:v]fps=30[vbase];"
    "[1:a]showwaves=s=1080x260:mode=line:colors=0x00F0FF|0xFF00FF[waves];"
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

print("Executing Character UI Master Video Render...")
subprocess.run(cmd, check=True)
print("=== CHARACTER UI MASTER RENDER COMPLETE ===")
print("Master video created at:", OUTPUT_FILE)
