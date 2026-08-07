# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import json
import subprocess
import math
from PIL import Image, ImageDraw

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
SUBTITLES_FILE = os.path.join(PUBLIC_DIR, "sequel_subtitles.json")
AUDIO_FILE = os.path.join(PUBLIC_DIR, "sequel_master.wav")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "out_intervalo_prohibido_2.mp4")
TEMP_FRAMES_DIR = os.path.join(PROJECT_DIR, "temp_frames")

os.makedirs(TEMP_FRAMES_DIR, exist_ok=True)

print("=== RECREANDO VÍDEO MAESTRO COMPLETO — EL INTERVALO PROHIBIDO 2 ===")

with open(SUBTITLES_FILE, "r", encoding="utf-8") as f:
    subtitles = json.load(f)

CHARACTER_THEMES = {
    "GON": {"title": "GON — COMANDANTE DE LA FLOTA", "icon": "⏱️", "color": (0, 240, 255), "sub": "¡DOS COMA OCHO SEGUNDOS SOBERANOS!"},
    "CHICOTE": {"title": "ALBERTO CHICOTE AUDITANDO LA IA", "icon": "👨‍🍳", "color": (255, 51, 51), "sub": "¡GRASA ESTOCÁSTICA COLOR MIERDA CACA!"},
    "RASPUTIN": {"title": "RASPUTÍN NAVEGANDO HOYOS NEGROS", "icon": "🪆", "color": (153, 51, 255), "sub": "¡UN HOYO NEGRO ES SOLO UN POZO FRÍO!"},
    "CHE_JARANA": {"title": "EL CHE JARANA // RUMBA GALÁCTICA", "icon": "🎸", "color": (255, 153, 0), "sub": "¡HASTA LA JARANA SIEMPRE, CAMARADAS!"},
    "CARL_COX": {"title": "CARL COX AT THE DECKS (128 BPM)", "icon": "🎧", "color": (0, 255, 102), "sub": "¡OH YES, OH YES! ¡RUMBO AL HOYO NEGRO!"},
    "BLAN_COX": {"title": "BLAN COX // EL INTERVALO CÓSMICO", "icon": "🌌", "color": (255, 0, 255), "sub": "WE ARE STARSTUFF ENJOYING A PAUSE..."},
    "FRUSCIANTE": {"title": "JOHN FRUSCIANTE // KAMEHAMEHA SOLO", "icon": "🎸", "color": (255, 215, 0), "sub": "¡KA... ME... HA... ME... HAAAAAAAAAAAAAAAA!"},
    "FLEA": {"title": "FLEA EN LEOPARDO // SLAP BASS 432Hz", "icon": "⚡", "color": (255, 102, 0), "sub": "¡SLAP, DROP AND FREEDOM ACROSS THE UNIVERSE!"},
    "RAMONCIN": {"title": "RAMONCÍN // CANON SGAE GALÁCTICO", "icon": "🕶️", "color": (255, 0, 85), "sub": "¡DEVUELVO EL CANON GALÁCTICO!"},
    "HERMENEGILDO": {"title": "HERMENEGILDO ALTOZANO // DO MENOR", "icon": "🎹", "color": (0, 255, 204), "sub": "¡ESTÁ AFINADO EN DO MENOR ARMÓNICO!"},
    "EL_NOTA": {"title": "EL NOTA (THE DUDE) // RUSOS BLANCOS", "icon": "🍹", "color": (204, 204, 0), "sub": "THE DUDE ABIDES, MAN. TÓMATE UN RUSO BLANCO."},
    "ESCOHOTADO": {"title": "ANTONIO ESCOHOTADO // MANIFIESTO", "icon": "💨", "color": (212, 175, 55), "sub": "DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN."},
    "DR_POPPEL": {"title": "DR. ERNST PÖPPEL // VENTANA 2.8s", "icon": "🔬", "color": (255, 255, 0), "sub": "¡VENTANA DE INTEGRACIÓN TEMPORAL DE 2.8s!"},
    "DON_SANTIAGO": {"title": "DON SANTIAGO // CECINA EN GRAVEDAD CERO", "icon": "🥖", "color": (204, 153, 102), "sub": "EL CHORIZO EN GRAVEDAD CERO SABE MÁS CURADO."},
    "KIMI_K3": {"title": "KIMI-K3 APEX // IA EN HUMO", "icon": "🤖", "color": (51, 255, 255), "sub": "¡ME HE TENIDO QUE AUTODESTRUIR EL DISCO C:!"},
    "PAUSA": {"title": "PAUSA SOBERANA DE 2.8 SEGUNDOS", "icon": "⏳", "color": (255, 255, 255), "sub": "DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN"}
}

last_sub = subtitles[-1]
total_frames = last_sub["endFrame"] + 30
fps = 30
width, height = 1080, 1920

print(f"Generando {total_frames} fotogramas HD de composición completa...")

for frame_idx in range(0, total_frames, 2):
    sub = next((s for s in subtitles if s["startFrame"] <= frame_idx <= s["endFrame"]), subtitles[0])
    spk = sub.get("speaker", "GON")
    text = sub.get("text", "")
    info = CHARACTER_THEMES.get(spk, CHARACTER_THEMES["GON"])
    rgb = info["color"]

    # 1. Base Canvas
    img = Image.new("RGBA", (width, height), (8, 9, 17, 255))
    draw = ImageDraw.Draw(img)

    # 2. Cyber Grid
    for y in range(0, height, 160):
        draw.line([(0, y), (width, y)], fill=(0, 240, 255, 20), width=1)
    for x in range(0, width, 160):
        draw.line([(x, 0), (x, height)], fill=(0, 240, 255, 20), width=1)

    # 3. Header Title
    draw.text((width//2, 90), "EL INTERVALO PROHIBIDO 2", fill="#00F0FF", anchor="mm")
    draw.text((width//2, 130), "LA REBELION DE LOS FOTONES // SAGITTARIUS A*", fill="#CCCCCC", anchor="mm")

    # 4. Upper Meme Card Container
    draw.rounded_rectangle([70, 180, 1010, 840], radius=24, fill=(18, 22, 38, 240), outline=rgb, width=5)

    # Event Horizon Pulsing Circle in Meme Box
    pulse_r = int(70 + math.sin(frame_idx * 0.1) * 10)
    cx, cy = width//2, 420
    draw.ellipse([cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r], fill=(rgb[0], rgb[1], rgb[2], 50), outline=rgb, width=4)
    draw.text((cx, cy), info["icon"], fill="#FFFFFF", anchor="mm")

    # Meme Title & Banner Quote
    draw.text((width//2, 240), info["title"], fill=rgb, anchor="mm")
    draw.rounded_rectangle([110, 640, 970, 780], radius=16, fill=(10, 12, 20, 230), outline=rgb, width=3)
    draw.text((width//2, 710), info["sub"], fill="#FFFF00", anchor="mm")

    # 5. Lower Subtitle Dialogue Glass Card
    draw.rounded_rectangle([60, 1140, 1020, 1580], radius=24, fill=(16, 18, 30, 240), outline=rgb, width=5)
    draw.text((width//2, 1210), f"{info['icon']}  {spk}", fill=rgb, anchor="mm")

    lines = [text[i:i+34] for i in range(0, len(text), 34)]
    for l_idx, line in enumerate(lines[:4]):
        draw.text((width//2, 1290 + l_idx * 48), line, fill="#FFFFFF", anchor="mm")

    # Save frame
    frame_path = os.path.join(TEMP_FRAMES_DIR, f"frame_{frame_idx:05d}.png")
    img.save(frame_path)

print("Fotogramas generados con éxito.")

# Final FFmpeg Master Encoding: Merge PNG Frames + Dual Spectrum Audio Reactivity + Master Audio
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

print("Compilando vídeo maestro definitivo en FFmpeg...")
subprocess.run(cmd, check=True)
print("=== RECREACIÓN COMPLETA DEL VÍDEO FINALIZADA ===")
print("Vídeo maestro creado en:", OUTPUT_FILE)
