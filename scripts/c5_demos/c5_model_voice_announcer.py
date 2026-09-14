#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ VOICE TRANSDUCTION DAEMON | DOMAIN: antigravity.voice | STATE: C5-REAL
# ============================================================================
"""
Daemon de transducción de voz para cambios de topología y modelo en Antigravity IDE.
Emite anuncios audibles de baja latencia utilizando el subsistema nativo TTS de macOS (say).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_VOICE = "Mónica"
FALLBACK_VOICE = "Eddy"


def speak_notification(text: str, voice: str = DEFAULT_VOICE, blocking: bool = False) -> None:
    """Emite síntesis de voz en macOS."""
    clean_text = text.replace('"', '\\"').replace("`", "")
    # Comprobar si la voz deseada está instalada
    check = subprocess.run(["say", "-v", voice, ""], capture_output=True)
    selected_voice = voice if check.returncode == 0 else "Samantha"

    cmd = ["say", "-v", selected_voice, clean_text]
    if blocking:
        subprocess.run(cmd, check=False)
    else:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def extract_model_change(line: str) -> str | None:
    """Extrae el cambio de modelo desde un registro JSON de transcript.jsonl."""
    try:
        data = json.loads(line)
        content = data.get("content", "")
        if "<USER_SETTINGS_CHANGE>" in content:
            # Buscar el patrón: from X to Y
            m = re.search(r"from\s+([^\n\.]+?)\s+to\s+([^\n\.]+?)\.", content)
            if m:
                return m.group(2).strip()
            # Buscar mención a Model Selection
            m2 = re.search(r"Model Selection`?\s+(?:to|is)\s+([^\n\.]+)", content)
            if m2:
                return m2.group(1).strip()
    except Exception:
        pass
    return None


def watch_transcript(
    transcript_path: Path,
    voice: str = DEFAULT_VOICE,
    max_iterations: Optional[int] = None,
) -> None:
    """Vigila el log transcript.jsonl en tiempo real y anuncia mutaciones de modelo."""
    print(f"[*] Iniciando Voice Watcher sobre: {transcript_path}")
    print(f"[*] Voz configurada: {voice}")

    if not transcript_path.exists():
        print("[!] Archivo de log no encontrado aún. Esperando inicialización...")

    last_model = None
    last_pos = 0

    # Si ya existe, posicionarse al final para capturar solo nuevos eventos
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
                            msg = f"Topología activa: {new_model}"
                            print(f"\n[🔊 VOZ]: {msg}")
                            speak_notification(msg, voice=voice, blocking=False)

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[*] Voice Watcher detenido por el operador.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity Voice Notification Daemon")
    parser.add_argument("--say", type=str, help="Pronunciar un mensaje directamente y salir")
    parser.add_argument("--watch", action="store_true", help="Vigilar transcript.jsonl de la sesión activa")
    parser.add_argument("--path", type=str, help="Ruta al transcript.jsonl")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE, help="Voz del sistema (default: Mónica)")

    args = parser.parse_args()

    if args.say:
        print(f"[🔊 VOZ DIRECTA]: {args.say}")
        speak_notification(args.say, voice=args.voice, blocking=True)
        return

    if args.watch:
        if args.path:
            p = Path(args.path)
        else:
            # Autodetectar última sesión en antigravity brain
            base = Path("/Users/borjafernandezangulo/.gemini/antigravity/brain")
            conv_id = "b6e348e5-5c68-4b43-bcab-8e3abcd8cad5"
            p = base / conv_id / ".system_generated" / "logs" / "transcript.jsonl"

        watch_transcript(p, voice=args.voice)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
