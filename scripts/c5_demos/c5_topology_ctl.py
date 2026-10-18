#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ UNIFIED TOPOLOGY & VOICE CONTROLLER (C5-REAL) | DOMAIN: antigravity.ctl
# ============================================================================
"""
Consola unificada de control topológico, enrutamiento causal, estado de
transducción acústica (clon de voz de Borja) y telemetría de exergía.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

BABYLON_ROOT = Path(os.environ.get("BABYLON_HOME", Path(__file__).resolve().parent.parent.parent))
MODELS_CACHE_DIR = BABYLON_ROOT / "assets" / "voice_samples" / "models"
VOICE_SCRIPT = BABYLON_ROOT / "scripts" / "c5_demos" / "c5_model_voice_announcer.py"
ROUTER_POC = BABYLON_ROOT / "scripts" / "c5_demos" / "poc_antigravity_model_router.py"


def cmd_status() -> None:
    print("=" * 72)
    print("█ BABYLON-60 / ANTIGRAVITY TOPOLOGY STATUS (C5-REAL)")
    print("=" * 72)

    # 1. Verificar daemon de voz
    res = subprocess.run(["pgrep", "-fl", "c5_model_voice_announcer.py"], capture_output=True, text=True)
    daemon_running = len(res.stdout.strip()) > 0
    status_icon = "🟢 ACTIVO" if daemon_running else "🔴 INACTIVO"
    print(f"[*] Voice Watcher Daemon:       {status_icon}")

    # 2. Banco de firmas en caché
    if MODELS_CACHE_DIR.exists():
        wavs = list(MODELS_CACHE_DIR.glob("*.wav"))
        print(f"[*] Firmas de Clon de Borja:    {len(wavs)} archivos sincronizados")
        for w in sorted(wavs):
            print(f"    - {w.name} ({w.stat().st_size // 1024} KB)")
    else:
        print("[!] Directorio de firmas no encontrado.")

    # 3. Enlace en ~/Music
    music_link = Path.home() / "Music" / "Borja_Voice_Models"
    music_status = "🟢 ENLAZADO" if music_link.is_symlink() or music_link.exists() else "🔴 NO ENLAZADO"
    print(f"[*] Centralización ~/Music:     {music_status} -> {music_link}")
    print("=" * 72)


def cmd_speak(phrase: str) -> None:
    print(f"[*] Disparando locución de voz y banner para: '{phrase}'")
    cmd = ["python3", str(VOICE_SCRIPT), "--say", f"Topología activa: {phrase}."]
    subprocess.run(cmd, check=False)


def cmd_route(prompt: str) -> None:
    print("=" * 72)
    print(f"[*] Evaluando vector causal para prompt: '{prompt[:60]}...'")
    print("=" * 72)

    # Importar router localmente
    sys.path.insert(0, str(BABYLON_ROOT / "scripts" / "c5_demos"))
    from poc_antigravity_model_router import (
        AntigravityModelRouter, TaskVector, ContextSize, DeductiveDepth, Sovereignty
    )

    p_lower = prompt.lower()
    has_secrets = any(w in p_lower for w in ["token", "secret", "clave", "privkey", "ed25519", "touchid", "password"])
    sov = Sovereignty.S2_AIRGAP_CRYPTO if has_secrets else Sovereignty.S0_PUBLIC
    deduct = (
        DeductiveDepth.D3_AXIOMATIC_FORMAL if any(w in p_lower for w in ["lean", "lean4", "teorema", "z3", "formal", "curry-howard"])
        else (DeductiveDepth.D2_SYSTEMS_TYPES if any(w in p_lower for w in ["rust", "c-ffi", "seqlock", "mypy", "64b", "borrow"])
        else DeductiveDepth.D0_MECHANICAL_IO)
    )

    task = TaskVector(
        task_id="cli-eval-001",
        ctx=ContextSize.C0_UNDER_32K,
        deduct=deduct,
        sov=sov,
        is_multimodal=False,
        is_swarm_worker=False,
        is_epistemic_halt=False,
        contains_unredacted_secrets=has_secrets,
    )

    router = AntigravityModelRouter()
    d = router.route(task)

    print(f"[+] Regla Activada:            {d.rule_id}")
    print(f"[+] Modelo Seleccionado:       {d.model_name}")
    print(f"[+] Régimen Deliberativo:      {d.regime}")
    print(f"[+] Selector en Antigravity:   {d.target_selector}")
    print(f"[+] Target de Failover:        {d.failover_model}")
    print(f"[+] Recibo HMAC SCITT:         {d.receipt_hmac}")
    print(f"[+] Latencia de Evaluación:    {d.latency_ns} ns")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity Topology & Voice Controller")
    subparsers = parser.add_subparsers(dest="action")

    subparsers.add_parser("status", help="Consultar estado de topología y daemon de voz")

    p_speak = subparsers.add_parser("speak", help="Disparar locución con el clon de Borja")
    p_speak.add_argument("phrase", type=str, help="Nombre del modelo o frase (ej: 'Claude Sonnet 4.6 Thinking')")

    p_route = subparsers.add_parser("route", help="Evaluar prompt y determinar modelo óptimo")
    p_route.add_argument("prompt", type=str, help="Prompt o tarea técnica a evaluar")

    subparsers.add_parser("bench", help="Ejecutar benchmark de estrés del router")

    args = parser.parse_args()

    if args.action == "status":
        cmd_status()
    elif args.action == "speak":
        cmd_speak(args.phrase)
    elif args.action == "route":
        cmd_route(args.prompt)
    elif args.action == "bench":
        subprocess.run(["python3", str(ROUTER_POC)], check=False)
    else:
        cmd_status()


if __name__ == "__main__":
    main()
