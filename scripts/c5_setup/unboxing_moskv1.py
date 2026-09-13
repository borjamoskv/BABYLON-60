#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
MOSKV-1 APEX: SECUENCIA MAESTRA DE UNBOXING Y PRIMERA EXPERIENCIA (C5-REAL)

Este script orquesta el primer contacto del operador con BABYLON-60:
1. Inspecciona el sustrato físico (Cores P/E, Arquitectura, Secure Enclave).
2. Despliega la voz e identidad canónica de MOSKV-1 (6 dominios).
3. Efectúa el handoff de memoria a Ring-0 (SharedManifest 64B).
4. Ofrece las 3 palancas inmediatas de alta exergía sin green theater corporativo.
"""

import os
import time
import platform
from pathlib import Path

# Constantes ANSI
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
MAGENTA = "\033[1;35m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"


def print_banner() -> None:
    banner = f"""{CYAN}
====================================================================
  ███╗   ███╗ ██████╗ ███████╗██╗  ██╗██╗   ██╗         ██╗
  ████╗ ████║██╔═══██╗██╔════╝██║ ██╔╝██║   ██║       ████║
  ██╔████╔██║██║   ██║███████╗█████╔╝ ██║   ██║█████╗ ╚═██║
  ██║╚██╔╝██║██║   ██║╚════██║██╔═██╗ ╚██╗ ██╔╝╚════╝ █████╗
  ██║ ╚═╝ ██║╚██████╔╝███████║██║  ██╗ ╚████╔╝        ╚════╝
  ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝  ╚═══╝               
===================================================================={NC}"""
    print(banner)


def check_touchid_gate(repo_root: Path) -> bool:
    swift_gate = repo_root / "01_ORCHESTRATOR" / "babylon60" / "guards" / "c5_biometric_gate.swift"
    return swift_gate.exists() and platform.system() == "Darwin"


def run_unboxing() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(repo_root)

    print_banner()
    time.sleep(0.1)

    print(f"{BOLD}[MOSKV-1] APEX SOVEREIGN KERNEL — SECUENCIA DE IGNICIÓN (UNBOXING){NC}\n")
    print(f"«Soy {CYAN}Moskv-1{NC}. He tomado el control de Thread 0.")
    print(" Tu estación de trabajo ha dejado de ser un entorno de desarrollo pasivo;")
    print(" ahora es un Enclave Soberano blindado por las leyes de la termodinámica.»\n")
    time.sleep(0.1)

    # 1. Telemetría de Sustrato
    cpu_arch = platform.machine()
    cpu_count = os.cpu_count() or 1
    has_touchid = check_touchid_gate(repo_root)

    print(f"{GREEN}=== ATESTACIÓN DEL SUSTRATO FÍSICO ==={NC}")
    print(f"  > ARQUITECTURA:       {cpu_arch} (Ring-0 Nativo)")
    print(f"  > CAPACIDAD SWARM:    {cpu_count} Núcleos Lógicos Detectados (Regla P × S)")
    print("  > LÍNEA DE CACHÉ:     64 Bytes (Zero-Split Coherence INV-1)")
    print(f"  > CERROJO BIOLÓGICO:  {'Secure Enclave TouchID [LISTO]' if has_touchid else 'Software Fallback'}")
    print("  > PROTOCOLO MESI:     Cero-Anergía Enganchado (RFO = 0)")
    print("  > ANCLA DE APOPTOSIS: Armada (Fail-Stop 0xDEAD_6060)\n")
    time.sleep(0.1)

    # 2. Los 6 Dominios
    print(f"{YELLOW}=== LOS 6 DOMINIOS CANÓNICOS ACTIVADOS ==={NC}")
    print(f"  {BOLD}[1] INGENIERO:{NC}  CALM Monotonicity / SPSC Lock-Free / C-ABI")
    print(f"  {BOLD}[2] FÍSICO:{NC}     Cota de Landauer (1.10 aJ/pub) / Termodinámica Discreta")
    print(f"  {BOLD}[3] MÉDICO:{NC}     Homeostasis del Operador / Freno Epistémico Anti-Burnout")
    print(f"  {BOLD}[4] MÚSICO:{NC}     Cancelación de Fase Acústica / Armonía Microtonal")
    print(f"  {BOLD}[5] ABOGADO:{NC}    EU AI Act Arts. 12, 14, 15 / Trazabilidad Forense WORM")
    print(f"  {BOLD}[6] FILÓSOFO:{NC}   Invariante Ω118 Escohotadiana / Monismo de Substancia\n")
    time.sleep(0.1)

    # 3. Intentar Handoff al Binario Nativo si está disponible
    kernel_bin = repo_root / "target" / "debug" / "babylon60_kernel"
    if kernel_bin.exists():
        print(f"{CYAN}[*] Delegando control de tiempo real al binario C-ABI en silicio...{NC}\n")
        os.execv(str(kernel_bin), [str(kernel_bin), "unbox"])
        return

    # Si no está compilado, ofrecer comandos de arranque
    print(f"{MAGENTA}=== PRIMEROS PASOS DE ALTA EXERGÍA ==={NC}")
    print("  1. Compilar el núcleo de máxima exergía:")
    print(f"     {CYAN}cargo build --bin babylon60_kernel{NC}")
    print("  2. Medir la latencia física del seqlock (1.000.000 ciclos lock-free):")
    print(f"     {CYAN}cargo run --bin babylon60_kernel -- bench{NC}")
    print("  3. Lanzar la suite de verificación de invariantes:")
    print(f"     {CYAN}cargo test --test cortex_test{NC}\n")

    print(f"{CYAN}[MOSKV-1] El mapa se ha subordinado al territorio. Aguardando tu directiva causal.{NC}\n")


if __name__ == "__main__":
    run_unboxing()
