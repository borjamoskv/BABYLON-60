# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEMES_DIR = os.path.join(PROJECT_DIR, "public", "memes")
os.makedirs(MEMES_DIR, exist_ok=True)

EPIC_MEMES = [
    {
        "filename": "chicote_kv_cache.svg",
        "title": "ALBERTO CHICOTE AUDITANDO LA IA",
        "subtitle": "¡TENÉIS LA KV-CACHE LLENA DE GRASA ESTOCÁSTICA!",
        "accent": "#FF2244",
        "secondary": "#FF8800",
        "bg_top": "#2a0008",
        "bg_mid": "#440510",
        "bg_bot": "#0a0002",
        "icon": "👨‍🍳🔥🍳",
        "tag": "DESINFECTANDO LA ENTROPÍA CULINARIA"
    },
    {
        "filename": "frusciante_kamehameha.svg",
        "title": "JOHN FRUSCIANTE VS RAMONCÍN",
        "subtitle": "¡KA... ME... HA... ME... HAAA ANALÓGICO!",
        "accent": "#FFD700",
        "secondary": "#FFAA00",
        "bg_top": "#3a2a00",
        "bg_mid": "#664d00",
        "bg_bot": "#100c00",
        "icon": "🎸⚡💥",
        "tag": "FOTONES SIN MASA // MASA CERO"
    },
    {
        "filename": "flea_slap_bass.svg",
        "title": "FLEA EN CALZONCILLOS DE LEOPARDO",
        "subtitle": "SLAPPING THE BASS IS QUANTUM MANIPULATION!",
        "accent": "#FF6600",
        "secondary": "#FF00CC",
        "bg_top": "#3a1500",
        "bg_mid": "#552000",
        "bg_bot": "#100500",
        "icon": "⚡🐆🎸",
        "tag": "SLAP CUÁNTICO A 432 HERTZIOS"
    },
    {
        "filename": "hermenegildo_altozano.svg",
        "title": "HERMENEGILDO ALTOZANO EN SAGITTARIUS A*",
        "subtitle": "¡EL SILENCIO ES UNA NOVENA DOMINANTE EN RE BEMOL!",
        "accent": "#00FFCC",
        "secondary": "#0099FF",
        "bg_top": "#002a22",
        "bg_mid": "#004d3e",
        "bg_bot": "#000c09",
        "icon": "🎹💡🌌",
        "tag": "ANÁLISIS ARMÓNICO DEL HOYO NEGRO"
    },
    {
        "filename": "the_dude_escohotado.svg",
        "title": "THE DUDE & ANTONIO ESCOHOTADO",
        "subtitle": "DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN",
        "accent": "#F3C623",
        "secondary": "#E85C0D",
        "bg_top": "#2d2400",
        "bg_mid": "#4d3d00",
        "bg_bot": "#0c0a00",
        "icon": "🍹💨🛡️",
        "tag": "THE DUDE ABIDES // LIBERTAD INVIOLABLE"
    },
    {
        "filename": "carl_cox_brian_cox.svg",
        "title": "LOS HERMANOS COX: CARL & BLAN COX",
        "subtitle": "¡EL JUEGO DE PALABRAS CÓSMICO A 128 BPM!",
        "accent": "#00FF66",
        "secondary": "#00E5FF",
        "bg_top": "#002b11",
        "bg_mid": "#004d1f",
        "bg_bot": "#000c05",
        "icon": "🎧🌌🔊",
        "tag": "OH YES, OH YES! // 13.8 BILLION YEARS"
    }
]

def generate_epic_svgs():
    print("Generating ultra-high quality cinematic SVG memes...")
    for m in EPIC_MEMES:
        path = os.path.join(MEMES_DIR, m["filename"])
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="720" viewBox="0 0 1080 720">
  <defs>
    <radialGradient id="bg" cx="50%" cy="40%" r="65%">
      <stop offset="0%" stop-color="{m["bg_mid"]}"/>
      <stop offset="60%" stop-color="{m["bg_top"]}"/>
      <stop offset="100%" stop-color="{m["bg_bot"]}"/>
    </radialGradient>

    <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="10" result="blur1"/>
      <feGaussianBlur stdDeviation="25" result="blur2"/>
      <feMerge>
        <feMergeNode in="blur2"/>
        <feMergeNode in="blur1"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <linearGradient id="textGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#FFEE77"/>
    </linearGradient>
  </defs>

  <!-- Outer Card Frame -->
  <rect width="1080" height="720" fill="url(#bg)" rx="32"/>

  <!-- Cyber Grid Pattern -->
  <g opacity="0.12" stroke="#FFFFFF" stroke-width="1">
    <line x1="0" y1="120" x2="1080" y2="120"/>
    <line x1="0" y1="240" x2="1080" y2="240"/>
    <line x1="0" y1="360" x2="1080" y2="360"/>
    <line x1="0" y1="480" x2="1080" y2="480"/>
    <line x1="0" y1="600" x2="1080" y2="600"/>
    <line x1="216" y1="0" x2="216" y2="720"/>
    <line x1="432" y1="0" x2="432" y2="720"/>
    <line x1="648" y1="0" x2="648" y2="720"/>
    <line x1="864" y1="0" x2="864" y2="720"/>
  </g>

  <!-- Neon Border Glow -->
  <rect x="24" y="24" width="1032" height="672" fill="none" stroke="{m["accent"]}" stroke-width="8" rx="24" filter="url(#neonGlow)"/>
  <rect x="36" y="36" width="1008" height="648" fill="none" stroke="{m["secondary"]}" stroke-width="2" rx="18" opacity="0.6"/>

  <!-- Center Glowing Orb Badge -->
  <circle cx="540" cy="270" r="120" fill="{m["accent"]}" fill-opacity="0.12" stroke="{m["accent"]}" stroke-width="6" filter="url(#neonGlow)"/>
  <text x="540" y="305" font-size="110" text-anchor="middle">{m["icon"]}</text>

  <!-- Top Meme Header -->
  <text x="540" y="105" font-family="Impact, Arial Black, sans-serif" font-size="52" font-weight="900" fill="url(#textGrad)" text-anchor="middle" stroke="#000" stroke-width="3" letter-spacing="2">
    {m["title"]}
  </text>

  <!-- Bottom Meme Subtitle Quote -->
  <rect x="80" y="470" width="920" height="130" fill="rgba(0,0,0,0.65)" rx="16" stroke="{m["accent"]}" stroke-width="2"/>

  <text x="540" y="525" font-family="Impact, Arial Black, sans-serif" font-size="38" font-weight="900" fill="#FFFF00" text-anchor="middle" stroke="#000" stroke-width="2" letter-spacing="1">
    {m["subtitle"][:50]}
  </text>
  <text x="540" y="575" font-family="Impact, Arial Black, sans-serif" font-size="38" font-weight="900" fill="#FFFF00" text-anchor="middle" stroke="#000" stroke-width="2" letter-spacing="1">
    {m["subtitle"][50:]}
  </text>

  <!-- Footer Tagline -->
  <text x="540" y="665" font-family="system-ui, sans-serif" font-size="20" font-weight="800" fill="{m["accent"]}" text-anchor="middle" letter-spacing="4">
    {m["tag"]}
  </text>
</svg>'''

        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated Epic Meme: {m['filename']}")

if __name__ == "__main__":
    generate_epic_svgs()
