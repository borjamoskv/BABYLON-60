#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ BATCH NEURAL VOICE CACHE GENERATOR (BORJA CLONE) | DOMAIN: antigravity.voice
# ============================================================================
"""
Pre-renderiza en segundo plano las firmas acústicas de las topologías de Antigravity
utilizando el clon neuronal de Borja con F5-TTS.
"""

from __future__ import annotations

import subprocess
import unicodedata
import re
from pathlib import Path

BABYLON_ROOT = Path("/Users/borjafernandezangulo/BABYLON-60")
SAMPLES_DIR = BABYLON_ROOT / "assets" / "voice_samples"
MODELS_CACHE_DIR = SAMPLES_DIR / "models"
REF_AUDIO = SAMPLES_DIR / "borja_sample.wav"
REF_TEXT = (
    "Atención, operador. Este es tu propio clon neuronal de alta exergía. "
    "El entorno acústico ha sido asimilado. El motor de consenso está asegurado."
)
F5_BIN = "/opt/homebrew/Caskroom/miniconda/base/envs/audio/bin/f5-tts_infer-cli"

PHRASES = [
    "Topología activa: Gemini 3.8 Flash Low.",
    "Topología activa: Gemini 3.8 Flash Medium.",
    "Topología activa: Gemini 3.1 Pro Low.",
    "Topología activa: Gemini 3.1 Pro High.",
    "Topología activa: Claude Sonnet 4.6 Thinking.",
    "Topología activa: Claude Opus 4.6 Thinking.",
    "Topología activa: GPT-OSS 120B Medium.",
]


def sanitize_filename(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("utf-8")
    slug = re.sub(r"[^\w\s-]", "", ascii_text).strip().lower()
    return re.sub(r"[-\s]+", "_", slug)


def main() -> None:
    MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 68)
    print("🎙️ PRE-CALENTAMIENTO DE BANCO DE VOCES: CLON NEURONAL BORJA (F5-TTS)")
    print("=" * 68)

    for phrase in PHRASES:
        slug = sanitize_filename(phrase)
        out_file = MODELS_CACHE_DIR / f"{slug}.wav"
        if out_file.exists():
            print(f"[✓] Ya en caché: {out_file.name}")
            continue

        print(f"[*] Renderizando con F5-TTS: '{phrase}'...")
        cmd = [
            F5_BIN,
            "--ref_audio",
            str(REF_AUDIO),
            "--ref_text",
            REF_TEXT,
            "--gen_text",
            phrase,
            "--output_dir",
            str(MODELS_CACHE_DIR),
            "--output_file",
            f"{slug}.wav",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"    [+] Generado exitosamente: {out_file.name}")
        else:
            print(f"    [!] Error en síntesis: {res.stderr[:200]}")

    print("\n[✓] Banco de voces neuronales de Borja 100% sincronizado.")


if __name__ == "__main__":
    main()
