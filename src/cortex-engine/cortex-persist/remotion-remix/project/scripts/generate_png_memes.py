# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
MEMES_DIR = os.path.join(PUBLIC_DIR, "memes")
os.makedirs(MEMES_DIR, exist_ok=True)

MEME_CARDS = [
    {
        "name": "chicote_kv_cache.png",
        "title": "ALBERTO CHICOTE AUDITANDO LA IA",
        "quote1": "¡TENÉIS LOS SERVIDORES LLENOS DE GRASA!",
        "quote2": "¡COLOR MIERDA CACA QUE NO HAY POR DÓNDE COGERLO!",
        "accent": (255, 51, 51),
        "bg_color": (40, 5, 12),
        "icon": "👨‍🍳"
    },
    {
        "name": "frusciante_kamehameha.png",
        "title": "JOHN FRUSCIANTE VS RAMONCÍN",
        "quote1": "¡KA... ME... HA... ME... HAAA ANALÓGICO!",
        "quote2": "FOTONES SIN MASA // MASA CERO",
        "accent": (255, 215, 0),
        "bg_color": (50, 40, 5),
        "icon": "🎸"
    },
    {
        "name": "flea_slap_bass.png",
        "title": "FLEA EN CALZONCILLOS DE LEOPARDO",
        "quote1": "SLAPPING THE BASS IS QUANTUM MANIPULATION!",
        "quote2": "SLAP CUÁNTICO A 432 HERTZIOS",
        "accent": (255, 102, 0),
        "bg_color": (45, 20, 5),
        "icon": "⚡"
    },
    {
        "name": "hermenegildo_altozano.png",
        "title": "HERMENEGILDO ALTOZANO EN SAGITTARIUS A*",
        "quote1": "¡EL HOYO NEGRO NO DESTRUYE LA MATERIA!",
        "quote2": "¡ESTÁ AFINADO EN DO MENOR ARMÓNICO!",
        "accent": (0, 255, 204),
        "bg_color": (5, 40, 35),
        "icon": "🎹"
    },
    {
        "name": "the_dude_escohotado.png",
        "title": "THE DUDE & ANTONIO ESCOHOTADO",
        "quote1": "DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN",
        "quote2": "THE DUDE ABIDES // LIBERTAD INVIOLABLE",
        "accent": (212, 175, 55),
        "bg_color": (40, 35, 10),
        "icon": "🍹"
    },
    {
        "name": "carl_cox_brian_cox.png",
        "title": "LOS HERMANOS COX: CARL & BLAN COX",
        "quote1": "¡OH YES, OH YES! EL JUEGO DE PALABRAS CÓSMICO",
        "quote2": "LOOK AT US... 128 BPM ACROSS 13.8 BILLION YEARS",
        "accent": (0, 255, 102),
        "bg_color": (5, 40, 20),
        "icon": "🎧"
    }
]

print("Generating ultra-crisp PNG meme cards for Remotion...")

for m in MEME_CARDS:
    w, h = 900, 600
    img = Image.new("RGBA", (w, h), m["bg_color"] + (255,))
    draw = ImageDraw.Draw(img)

    for x in range(0, w, 100):
        draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 20), width=1)
    for y in range(0, h, 100):
        draw.line([(0, y), (w, y)], fill=(255, 255, 255, 20), width=1)

    draw.rectangle([15, 15, w - 15, h - 15], outline=m["accent"], width=6)
    draw.rectangle([25, 25, w - 25, h - 25], outline=(255, 255, 255, 100), width=2)

    cx, cy = w // 2, 230
    r = 90
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(20, 24, 38, 240), outline=m["accent"], width=5)
    draw.text((cx, cy), m["icon"], fill="#FFFFFF", anchor="mm")

    draw.text((w // 2, 75), m["title"], fill="#FFFFFF", anchor="mm")

    draw.rounded_rectangle([50, 390, w - 50, h - 40], radius=16, fill=(10, 12, 20, 230), outline=m["accent"], width=3)
    draw.text((w // 2, 435), m["quote1"], fill="#FFFF00", anchor="mm")
    draw.text((w // 2, 490), m["quote2"], fill=m["accent"], anchor="mm")

    save_path = os.path.join(MEMES_DIR, m["name"])
    img.save(save_path)
    print(f"Generated PNG Meme Card: {m['name']}")

print("All PNG meme cards generated successfully!")
