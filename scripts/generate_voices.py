# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
from gtts import gTTS
import os

# Textos extraídos de GoedelBrosComposition.tsx
dialogos = {
    "goedel": "Aiba la hostia, bro. Tu sistema de captación de leads no puede demostrar su propio ROI desde dentro. Necesitas un axioma externo, un billete de 500 pavos en ads de Meta, para que el chiringuito no sea inconsistente. ¡La madre que me parió con los funnels circulares!",
    "turing": "Illo, escúchame una cosita. Que yo he montao una máquina universal y te digo que el problema de la parada es tu tasa de rebote, mi arma. El algoritmo se queda colgao pensando si el pavo va a comprar el ticket o no. ¡Que no computa, picha, que no computa!",
    "cantor": "¡Aleph-sub-cero leads! ¡Estáis pensando muy pequeño! El verdadero crecimiento orgánico requiere cardinalidades transfinitas. Si metes un infinito no numerable en la parte alta del funnel, la conversión en la diagonal colapsa tu Stripe. ¡Es poético!",
    "xokas": "Pero vamos a ver, pandilla de fracasados. ¿Qué cojones me estáis contando de axiomas y Alephs? Si no hacéis directos de 14 horas picando piedra, no vais a vender ni un puto curso de matemáticas. ¡Menos teoremas y más currar, que sois unos NPCs de la lógica!",
}

# Crear directorio si no existe
out_dir = "web/public/audio"
os.makedirs(out_dir, exist_ok=True)

for name, text in dialogos.items():
    print(f"Generando voz para {name}...")
    # Usamos acentos locales (aunque gTTS solo soporta tld limitados, usamos es-es o es-us para variar)
    tld = "es"
    if name == "xokas":
        tld = "com.mx"  # Para darle otro tono

    tts = gTTS(text, lang="es", tld=tld)
    tts.save(f"{out_dir}/{name}.mp3")

print("Voces generadas en web/public/audio/")
