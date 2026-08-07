# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEMES_DIR = os.path.join(PROJECT_DIR, "public", "memes")
os.makedirs(MEMES_DIR, exist_ok=True)

MEME_SPECS = [
    {
        "filename": "chicote_kv_cache.svg",
        "title": "CUANDO CHICOTE AUDITA TU IA",
        "subtitle": "¡TENÉIS LA KV-CACHE LLENA DE GRASA ESTOCÁSTICA!",
        "accent": "#FF3333",
        "bg_top": "#440000",
        "bg_bot": "#110000",
        "icon": "👨‍🍳🔥"
    },
    {
        "filename": "frusciante_kamehameha.svg",
        "title": "FRUSCIANTE VS RAMONCÍN",
        "subtitle": "¡KA... ME... HA... ME... HAAA ANALÓGICO!",
        "accent": "#FFD700",
        "bg_top": "#664400",
        "bg_bot": "#1a1100",
        "icon": "🎸⚡"
    },
    {
        "filename": "flea_slap_bass.svg",
        "title": "FLEA EN CALZONCILLOS DE LEOPARDO",
        "subtitle": "SLAPPING THE BASS IS QUANTUM MANIPULATION!",
        "accent": "#FF6600",
        "bg_top": "#441100",
        "bg_bot": "#110500",
        "icon": "⚡🐆"
    },
    {
        "filename": "hermenegildo_altozano.svg",
        "title": "HERMENEGILDO ALTOZANO EN EL PIANO",
        "subtitle": "¡EL SILENCIO ES UNA NOVENA DOMINANTE EN RE BEMOL!",
        "accent": "#00FFCC",
        "bg_top": "#004433",
        "bg_bot": "#00110c",
        "icon": "🎹💡"
    },
    {
        "filename": "the_dude_escohotado.svg",
        "title": "THE DUDE & ANTONIO ESCOHOTADO",
        "subtitle": "DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN. THE DUDE ABIDES.",
        "accent": "#D4AF37",
        "bg_top": "#443300",
        "bg_bot": "#110d00",
        "icon": "🍹💨"
    },
    {
        "filename": "carl_cox_brian_cox.svg",
        "title": "LOS HERMANOS COX: CARL & BLAN COX",
        "subtitle": "¡EL JUEGO DE PALABRAS CÓSMICO! ¡BLAN COX Y CARL COX A 128 BPM!",
        "accent": "#00FF66",
        "bg_top": "#003311",
        "bg_bot": "#001105",
        "icon": "🎧🌌"
    }
]

def generate_svg_memes():
    print("Generating high-res agentic SVG meme cards...")
    for m in MEME_SPECS:
        path = os.path.join(MEMES_DIR, m["filename"])
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{m["bg_top"]}"/>
      <stop offset="100%" stop-color="{m["bg_bot"]}"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Background Card -->
  <rect width="800" height="600" fill="url(#bg)" rx="24"/>
  <rect x="16" y="16" width="768" height="568" fill="none" stroke="{m["accent"]}" stroke-width="6" rx="16" filter="url(#glow)"/>

  <!-- Icon Badge -->
  <circle cx="400" cy="220" r="90" fill="{m["accent"]}" fill-opacity="0.15" stroke="{m["accent"]}" stroke-width="4"/>
  <text x="400" y="245" font-size="80" text-anchor="middle">{m["icon"]}</text>

  <!-- Top Title -->
  <text x="400" y="90" font-family="Impact, Arial Black, sans-serif" font-size="42" font-weight="900" fill="#FFFFFF" text-anchor="middle" stroke="#000" stroke-width="2">
    {m["title"]}
  </text>

  <!-- Subtitle Quote -->
  <text x="400" y="440" font-family="Impact, Arial Black, sans-serif" font-size="32" font-weight="900" fill="#FFFF00" text-anchor="middle" stroke="#000" stroke-width="2">
    {m["subtitle"][:45]}
  </text>
  <text x="400" y="490" font-family="Impact, Arial Black, sans-serif" font-size="32" font-weight="900" fill="#FFFF00" text-anchor="middle" stroke="#000" stroke-width="2">
    {m["subtitle"][45:]}
  </text>

  <!-- Footer Tag -->
  <text x="400" y="550" font-family="monospace" font-size="16" fill="{m["accent"]}" text-anchor="middle" letter-spacing="3">
    EL INTERVALO PROHIBIDO // 2.8s
  </text>
</svg>'''

        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated: {m['filename']}")

if __name__ == "__main__":
    generate_svg_memes()
