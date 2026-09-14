#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ VOICE TRANSDUCTION DAEMON (BORJA NEURAL CLONE) | DOMAIN: antigravity.voice
# ============================================================================
"""
Daemon de transducción de voz con CLON NEURONAL DEL USUARIO (Borja).
Utiliza F5-TTS / XTTS sobre Apple Silicon con la muestra de referencia `borja_sample.wav`.
Ofrece reproducción inmediata de caché (<30ms) y síntesis reactiva en tiempo real.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional


import unicodedata

BABYLON_ROOT = Path(os.environ.get("BABYLON_HOME", Path(__file__).resolve().parent.parent.parent))
SAMPLES_DIR = BABYLON_ROOT / "assets" / "voice_samples"
MODELS_CACHE_DIR = SAMPLES_DIR / "models"
REF_AUDIO = SAMPLES_DIR / "borja_sample.wav"
REF_TEXT = (
    "Atención, operador. Este es tu propio clon neuronal de alta exergía. "
    "El entorno acústico ha sido asimilado. El motor de consenso está asegurado."
)
F5_BIN = "/opt/homebrew/Caskroom/miniconda/base/envs/audio/bin/f5-tts_infer-cli"


def sanitize_filename(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("utf-8")
    slug = re.sub(r"[^\w\s-]", "", ascii_text).strip().lower()
    return re.sub(r"[-\s]+", "_", slug)


def speak_cloned(text: str, blocking: bool = False) -> None:
    """
    Reproduce el anuncio utilizando el clon neuronal de voz de Borja.
    Si el archivo de audio pre-renderizado existe, se reproduce instantáneamente con afplay.
    Si no, se sintetiza mediante F5-TTS y se almacena en la caché.
    """
    MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    slug = sanitize_filename(text)
    cached_wav = MODELS_CACHE_DIR / f"{slug}.wav"

    # Caso 1: Audio específico ya existe en caché o raíz de voice_samples
    direct_wav = SAMPLES_DIR / f"{slug}.wav"
    target_wav = cached_wav if cached_wav.exists() else (direct_wav if direct_wav.exists() else None)

    if target_wav and target_wav.exists():
        # Despachar notificación nativa visual en macOS
        cmd_banner = [
            "osascript", "-e",
            f'display notification "{text}" with title "Antigravity Topology" subtitle "Soberanía C5-REAL"'
        ]
        subprocess.Popen(cmd_banner, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        cmd = ["afplay", str(target_wav)]
        if blocking:
            subprocess.run(cmd, check=False)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    # Caso 2: Síntesis neuronal mediante F5-TTS
    if Path(F5_BIN).exists() and REF_AUDIO.exists():
        print(f"[*] Sintetizando clon de Borja para: '{text}'...")
        cmd_synth = [
            F5_BIN,
            "--ref_audio",
            str(REF_AUDIO),
            "--ref_text",
            REF_TEXT,
            "--gen_text",
            text,
            "--output_dir",
            str(MODELS_CACHE_DIR),
            "--output_file",
            f"{slug}.wav",
        ]
        res = subprocess.run(cmd_synth, capture_output=True, text=True)
        if res.returncode == 0 and cached_wav.exists():
            cmd_play = ["afplay", str(cached_wav)]
            if blocking:
                subprocess.run(cmd_play, check=False)
            else:
                subprocess.Popen(cmd_play, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

    # Fallback de emergencia si F5-TTS falla
    subprocess.Popen(["say", "-v", "Mónica", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def extract_model_change(line: str) -> str | None:
    """Extrae el cambio de modelo desde un registro JSON de transcript.jsonl."""
    try:
        data = json.loads(line)
        content = data.get("content", "")
        if "<USER_SETTINGS_CHANGE>" in content:
            m = re.search(r"from\s+([^\n\.]+?)\s+to\s+([^\n\.]+?)\.", content)
            if m:
                return m.group(2).strip()
            m2 = re.search(r"Model Selection`?\s+(?:to|is)\s+([^\n\.]+)", content)
            if m2:
                return m2.group(1).strip()
    except Exception:
        pass
    return None


def watch_transcript(
    transcript_path: Path,
    max_iterations: Optional[int] = None,
) -> None:
    """Vigila el log transcript.jsonl y anuncia cambios con el clon de Borja."""
    print(f"[*] Voice Watcher activo (Clon Borja F5-TTS). Monitoreando: {transcript_path}")

    last_model = None
    last_pos = 0

    if transcript_path.exists():
        last_pos = transcript_path.stat().st_size

    iteration = 0
    running = True
    try:
        while running:
            iteration += 1
            if max_iterations is not None and iteration >= max_iterations:
                running = False
            if transcript_path.exists():
                curr_size = transcript_path.stat().st_size
                if curr_size > last_pos:
                    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(last_pos)
                        lines = f.readlines()
                        last_pos = f.tell()

                    for line in lines:
                        new_model = extract_model_change(line)
                        if new_model and new_model != last_model:
                            last_model = new_model
                            msg = f"Topología activa: {new_model}."
                            print(f"\n[🎙️ CLON BORJA]: {msg}")
                            speak_cloned(msg, blocking=False)

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[*] Voice Watcher detenido.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity Voice Watcher (Borja Neural Clone)")
    parser.add_argument("--say", type=str, help="Pronunciar texto con el clon de Borja")
    parser.add_argument("--watch", action="store_true", help="Monitorear cambios de modelo en tiempo real")
    parser.add_argument("--path", type=str, help="Ruta al transcript.jsonl")

    args = parser.parse_args()

    if args.say:
        speak_cloned(args.say, blocking=True)
        return

    if args.watch:
        if args.path:
            p = Path(args.path)
        else:
            base = Path.home() / ".gemini" / "antigravity" / "brain"
            conv_id = "b6e348e5-5c68-4b43-bcab-8e3abcd8cad5"
            p = base / conv_id / ".system_generated" / "logs" / "transcript.jsonl"

        watch_transcript(p)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
