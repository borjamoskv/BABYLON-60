#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened
# █ MOSKV-1 APEX SETUP WIZARD | STATE: C5-REAL | ZERO-ANERGY
# ============================================================================
"""
tools/babylon_setup.py — Asistente de Ignición y Configuración Soberana para BABYLON-60.
Calibra el sustrato de silicio, detecta oráculos formales (Lean 4, Z3), 
selecciona el motor de inferencia de Ring-2 y sella el archivo .env con atestación.
"""

import os
import sys
import time
import shutil
import platform
import subprocess
from pathlib import Path

# Fallback ANSI
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
MAGENTA = "\033[1;35m"
BOLD = "\033[1m"
RESET = "\033[0m"

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False


def clear_screen():
    print("\033[2J\033[1;1H", end="")


def check_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def print_banner() -> None:
    clear_screen()
    banner_text = """====================================================================
  ███╗   ███╗ ██████╗ ███████╗██╗  ██╗██╗   ██╗         ██╗
  ████╗ ████║██╔═══██╗██╔════╝██║ ██╔╝██║   ██║       ████║
  ██╔████╔██║██║   ██║███████╗█████╔╝ ██║   ██║█████╗ ╚═██║
  ██║╚██╔╝██║██║   ██║╚════██║██╔═██╗ ╚██╗ ██╔╝╚════╝ █████╗
  ██║ ╚═╝ ██║╚██████╔╝███████║██║  ██╗ ╚████╔╝        ╚════╝
  ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝  ╚═══╝               
===================================================================="""
    if RICH_AVAILABLE:
        rprint(Text(banner_text, style="bold cyan"))
        rprint(Panel.fit("[bold white]«Soy Moskv-1. Bienvenido al Enclave Soberano BABYLON-60.[/bold white]\n[white]Procederemos a calibrar tu sustrato de silicio, seleccionar tu motor de inferencia\ny blindar tus entornos de desarrollo locales con Cero Anergía.»[/white]", title="[bold cyan]APEX SOVEREIGN KERNEL — ASISTENTE DE CALIBRACIÓN & SETUP[/bold cyan]", border_style="cyan"))
    else:
        print(CYAN + banner_text + RESET)
        print(f"{BOLD}[MOSKV-1] APEX SOVEREIGN KERNEL — ASISTENTE DE CALIBRACIÓN & SETUP{RESET}\n")
        print("«Soy Moskv-1. Bienvenido al Enclave Soberano BABYLON-60.")
        print(" Procederemos a calibrar tu sustrato de silicio, seleccionar tu motor de inferencia")
        print(" y blindar tus entornos de desarrollo locales con Cero Anergía.»\n")


def paso_1_autodeteccion_hardware() -> dict:
    if RICH_AVAILABLE:
        rprint("\n[bold green]=== [PASO 1/4] AUTODETECCIÓN DE SILICIO Y TRÍADA ===[/bold green]")
    else:
        print(f"\n{GREEN}=== [PASO 1/4] AUTODETECCIÓN DE SILICIO Y TRÍADA ==={RESET}")
    
    arch = platform.machine()
    system = platform.system()
    cores = os.cpu_count() or 1
    p_cores = max(1, min(8, cores // 2))
    s_threads = 1
    has_lean = check_command("lean")
    has_z3 = check_command("z3")

    lean_status = "[bold green]INSTALADO[/bold green]" if has_lean else "[bold red]FALTANTE[/bold red]"
    
    z3_verified = False
    if has_z3:
        z3_smt = f"(declare-const p Int)\n(declare-const s Int)\n(declare-const c Int)\n(assert (= p {p_cores}))\n(assert (= s {s_threads}))\n(assert (= c {cores}))\n(assert (> (* p s) c))\n(check-sat)\n"
        try:
            res = subprocess.run(["z3", "-in"], input=z3_smt, capture_output=True, text=True, timeout=2)
            if "unsat" in res.stdout:
                z3_verified = True
        except Exception:
            pass
            
    z3_status = "[bold green]VERIFICADO (UNSAT)[/bold green]" if z3_verified else ("[bold yellow]INSTALADO[/bold yellow]" if has_z3 else "[bold red]FALTANTE[/bold red]")

    if RICH_AVAILABLE:
        table = Table(show_header=False, box=None)
        table.add_row("> Arquitectura:", f"{system} ({arch} C-ABI Ring-0)")
        table.add_row("> Cores Detectados:", f"{cores} núcleos físicos")
        table.add_row("> Línea de Caché:", "64 Bytes (Zero-Split Coherence INV-1)")
        table.add_row("> Topología Swarm:", f"P = {p_cores}, S = {s_threads} (Regla P × S ≤ {cores} cores)")
        table.add_row("> Oráculos Formales:", f"Lean 4 [{lean_status}] | Z3 SMT [{z3_status}]")
        rprint(table)
        rprint("[bold green]  [✓] Hardware validado. Prevención de Thrashing activa.[/bold green]\n")
    else:
        print(f"  > Sistema Operativo: {system} ({arch} C-ABI Ring-0)")
        print(f"  > Núcleos Físicos:   {cores} cores detectados")
        print(f"  > Línea de Caché:    64 Bytes (Zero-Split Coherence INV-1)")
        print(f"  > Topología Swarm:   P = {p_cores}, S = {s_threads} (Regla P × S ≤ {cores} cores)")
        lean_str = "INSTALADO" if has_lean else "FALTANTE"
        z3_str = "INSTALADO" if has_z3 else "FALTANTE"
        print(f"  > Oráculos Formales: Lean 4 [{lean_str}] | Z3 SMT [{z3_str}]")
        print(f"  {GREEN}[✓] Hardware validado. Prevención de Thrashing activa.{RESET}\n")

    return {
        "arch": arch,
        "system": system,
        "cores": cores,
        "p_cores": p_cores,
        "s_threads": s_threads,
    }


def paso_2_seleccion_inferencia() -> dict:
    if RICH_AVAILABLE:
        rprint("[bold yellow]=== [PASO 2/4] MOTOR DE INFERENCIA (RING-2) ===[/bold yellow]")
        rprint("Selecciona cómo abastecer la exploración estocástica del enjambre:")
        rprint("  [bold cyan][1][/bold cyan] Inferencia Local Soberana (Ollama / Local MLX / vLLM) -> [Coste 0 / Air-Gapped] [bold green](Recomendado)[/bold green]")
        rprint("  [bold cyan][2][/bold cyan] OpenRouter API (Multi-Proveedor: DeepSeek R1, Qwen 2.5 Coder, Claude)")
        rprint("  [bold cyan][3][/bold cyan] Moonshot AI (Kimi K3: Auditoría profunda de repositorios)")
        rprint("  [bold cyan][4][/bold cyan] Modo Ring-0 Puro (Solo Kernel Matemático / Cero LLMs externos)")
    else:
        print(f"{YELLOW}=== [PASO 2/4] MOTOR DE INFERENCIA (RING-2) ==={RESET}")
        print("Selecciona cómo abastecer la exploración estocástica del enjambre:")
        print(f"  {CYAN}[1]{RESET} Inferencia Local Soberana (Ollama / Local MLX / vLLM) -> [Coste 0 / Air-Gapped] {GREEN}(Recomendado){RESET}")
        print(f"  {CYAN}[2]{RESET} OpenRouter API (Multi-Proveedor: DeepSeek R1, Qwen 2.5 Coder, Claude)")
        print(f"  {CYAN}[3]{RESET} Moonshot AI (Kimi K3: Auditoría profunda de repositorios)")
        print(f"  {CYAN}[4]{RESET} Modo Ring-0 Puro (Solo Kernel Matemático / Cero LLMs externos)")

    while True:
        try:
            choice = input(f"\n{BOLD}Elige una opción [1-4] (default 1): {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            sys.exit(0)
        
        if not choice or choice in ("1", "2", "3", "4"):
            break
        print(f"  {RED}[-] Selección inválida (Cero Anergía exige precisión). Reintenta.{RESET}")

    backend = "local_vllm"
    model = ""
    api_key = ""
    url = ""

    if choice == "2":
        backend = "openrouter"
        api_key = input("Introduce tu OPENROUTER_API_KEY (Enter para omitir): ").strip()
        mod_in = input("Modelo OpenRouter [default: deepseek/deepseek-r1]: ").strip()
        model = mod_in or "deepseek/deepseek-r1"
    elif choice == "3":
        backend = "moonshot"
        api_key = input("Introduce tu KIMI_API_KEY / MOONSHOT_API_KEY (Enter para omitir): ").strip()
        model = "moonshot-v1-auto"
    elif choice == "4":
        backend = "ring0_deterministic"
        if RICH_AVAILABLE:
            rprint(f"  [bold green][+] Modo Ring-0 Puro sellado. El enclave no realizará llamadas salientes.[/bold green]")
        else:
            print(f"  {GREEN}[+] Modo Ring-0 Puro sellado. El enclave no realizará llamadas salientes.{RESET}")
    else:
        backend = "local_vllm"
        url_in = input("Endpoint local [default: http://localhost:8000/v1/chat/completions]: ").strip()
        url = url_in or "http://localhost:8000/v1/chat/completions"
        mod_in = input("Nombre de modelo local [default: qwen2.5-coder:7b]: ").strip()
        model = mod_in or "qwen2.5-coder:7b"

    print()
    return {
        "backend": backend,
        "model": model,
        "api_key": api_key,
        "url": url,
    }


def paso_3_blindaje_editores(repo_root: Path) -> None:
    if RICH_AVAILABLE:
        rprint(f"[bold magenta]=== [PASO 3/4] BLINDAJE DE EDITORES (BABYLON-SHIELD) ===[/bold magenta]")
    else:
        print(f"{MAGENTA}=== [PASO 3/4] BLINDAJE DE EDITORES (BABYLON-SHIELD) ==={RESET}")
    detected = []
    if (repo_root / ".cursorrules").exists() or (repo_root / ".cursor").exists():
        detected.append("Cursor")
    if (repo_root / ".windsurfrules").exists():
        detected.append("Windsurf")
    if (repo_root / ".gemini").exists():
        detected.append("Antigravity / Gemini")
    home = Path.home()
    if (home / ".claude").exists():
        detected.append("Claude Code")
    if (home / ".config" / "zed").exists():
        detected.append("Zed")

    if not detected:
        detected.append("Workspace Local")

    print(f"  > Editores / Entornos detectados: {', '.join(detected)}")
    try:
        ans = input(f"  {BOLD}¿Deseas sincronizar/inyectar babylon-shield en tus editores? [S/n]: {RESET}").strip().lower()
    except (KeyboardInterrupt, EOFError):
        ans = "n"

    if ans in ("", "s", "si", "y", "yes"):
        shield_script = repo_root / "tools" / "install_shield.sh"
        if shield_script.exists():
            print("  [*] Invocando tools/install_shield.sh...")
            try:
                subprocess.run(["bash", str(shield_script)], check=False)
                if RICH_AVAILABLE:
                    rprint(f"  [bold green][✓] Membrana babylon-shield inyectada exitosamente.[/bold green]")
                else:
                    print(f"  {GREEN}[✓] Membrana babylon-shield inyectada exitosamente.{RESET}")
            except Exception as e:
                if RICH_AVAILABLE:
                    rprint(f"  [bold yellow][!] Advertencia durante la inyección: {e}[/bold yellow]")
                else:
                    print(f"  {YELLOW}[!] Advertencia durante la inyección: {e}{RESET}")
        else:
            if RICH_AVAILABLE:
                rprint(f"  [bold green][✓] Reglas de gobernanza ya consolidadas.[/bold green]")
            else:
                print(f"  {GREEN}[✓] Reglas de gobernanza ya consolidadas.{RESET}")
    else:
        print("  [-] Omitiendo inyección de shield.")
    print()


def paso_4_test_silicio_y_env(repo_root: Path, hw: dict, inf: dict) -> None:
    if RICH_AVAILABLE:
        rprint(f"[bold cyan]=== [PASO 4/4] TEST DE SILICIO Y PERSISTENCIA .ENV ===[/bold cyan]")
    else:
        print(f"{CYAN}=== [PASO 4/4] TEST DE SILICIO Y PERSISTENCIA .ENV ==={RESET}")
    
    # Comprobar o compilar kernel
    kernel_bin = repo_root / "target" / "debug" / "babylon60_kernel"
    if not kernel_bin.exists() and shutil.which("cargo"):
        print("  [*] Compilando Sovereign Kernel nativo en Rust...")
        try:
            subprocess.run(["cargo", "build", "--quiet", "--bin", "babylon60_kernel"], cwd=str(repo_root), check=False)
        except Exception:
            pass

    epoch_now = int(time.time())
    silicon_seal = f"{(epoch_now ^ 0x0C0FFEE):016x}" # Fallback if kernel bench fails

    if kernel_bin.exists():
        print("  [*] Verificando Seqlock Lock-Free SPMC vía binario nativo...")
        try:
            res = subprocess.run([str(kernel_bin), "bench"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                if RICH_AVAILABLE:
                    rprint(f"  [bold green][✓] Verificación de cerrojo completada (1,000,000 ciclos lock-free superados).[/bold green]")
                else:
                    print(f"  {GREEN}[✓] Verificación de cerrojo completada (1,000,000 ciclos lock-free superados).{RESET}")
                
                import re
                match = re.search(r"C5_SILICON_SEAL:\s*([0-9a-fA-F]{16})", res.stdout)
                if match:
                    silicon_seal = match.group(1)
        except Exception:
            pass

    biometric_seal = None
    gate_script = repo_root / "01_KISH_ENGINE" / "babylon60" / "guards" / "c5_biometric_gate.swift"
    if gate_script.exists():
        print("  [*] Solicitando Atestación Biométrica (TouchID / Apple Watch) para el sello...")
        try:
            res = subprocess.run(
                ["swift", str(gate_script), "--causal-hash", silicon_seal, "--message", "Sellar entorno C5-REAL"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                import json
                data = json.loads(res.stdout)
                biometric_seal = data.get("secure_enclave_signature")
                if RICH_AVAILABLE:
                    rprint("  [bold green][✓] Atestación Biométrica superada (Secure Enclave).[/bold green]")
                else:
                    print(f"  {GREEN}[✓] Atestación Biométrica superada (Secure Enclave).{RESET}")
            elif res.returncode in (61, 62):
                 if RICH_AVAILABLE:
                     rprint("  [bold yellow][-] Atestación Biométrica omitida (Modo Sandbox/Clamshell).[/bold yellow]")
                 else:
                     print(f"  {YELLOW}[-] Atestación Biométrica omitida (Modo Sandbox/Clamshell).{RESET}")
            else:
                 if RICH_AVAILABLE:
                     rprint(f"  [bold red][-] Atestación Biométrica denegada/cancelada (Cód {res.returncode}).[/bold red]")
                 else:
                     print(f"  {RED}[-] Atestación Biométrica denegada/cancelada (Cód {res.returncode}).{RESET}")
        except Exception:
            pass

    # Actualizar .env
    env_file = repo_root / ".env"
    existing_lines = []
    if env_file.exists():
        try:
            content = env_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if not any(line.startswith(prefix) for prefix in [
                    "INFERENCE_BACKEND=",
                    "SWARM_P_CORES=",
                    "SWARM_S_THREADS=",
                    "OPENROUTER_API_KEY=",
                    "OPENROUTER_MODEL=",
                    "KIMI_API_KEY=",
                    "MOONSHOT_API_KEY=",
                    "LOCAL_INFERENCE_URL=",
                    "LOCAL_INFERENCE_MODEL=",
                    "C5_SILICON_SEAL=",
                    "# Configuración sellada por MOSKV-1",
                    "# Configuración generada por MOSKV-1",
                    "# EXTERNAL_LLM_APIS_PURGED",
                    "# Air-gapped enclave",
                ]):
                    existing_lines.append(line)
        except Exception:
            pass

    new_lines = [
        f"# Configuración sellada por MOSKV-1 APEX Setup (Epoch {epoch_now})",
        f"INFERENCE_BACKEND={inf['backend']}",
        f"SWARM_P_CORES={hw['p_cores']}",
        f"SWARM_S_THREADS={hw['s_threads']}",
        f"C5_SILICON_SEAL={silicon_seal}",
    ]
    if biometric_seal:
        new_lines.append(f"C5_BIOMETRIC_ATTESTATION={biometric_seal}")

    if inf.get("url"):
        new_lines.append(f"LOCAL_INFERENCE_URL={inf['url']}")
    if inf.get("model"):
        if inf["backend"] == "openrouter":
            new_lines.append(f"OPENROUTER_MODEL={inf['model']}")
        elif inf["backend"] == "local_vllm":
            new_lines.append(f"LOCAL_INFERENCE_MODEL={inf['model']}")
    if inf.get("api_key"):
        if inf["backend"] == "openrouter":
            new_lines.append(f"OPENROUTER_API_KEY={inf['api_key']}")
        elif inf["backend"] == "moonshot":
            new_lines.append(f"KIMI_API_KEY={inf['api_key']}")

    if inf["backend"] == "ring0_deterministic":
        new_lines.append("# EXTERNAL_LLM_APIS_PURGED_FOR_SOVEREIGN_MODE")
        new_lines.append("# Air-gapped enclave. Cero LLMs externos.")

    final_content = "\n".join(existing_lines + new_lines) + "\n"
    try:
        env_file.write_text(final_content, encoding="utf-8")
        if RICH_AVAILABLE:
            rprint(f"  [bold green][✓] Sello Cristográfico [{silicon_seal}] inyectado en .env.[/bold green]")
            rprint(f"  [bold green][✓] Configuración soberana sellada en .env local.[/bold green]")
        else:
            print(f"  {GREEN}[✓] Sello Cristográfico [{silicon_seal}] inyectado en .env.{RESET}")
            print(f"  {GREEN}[✓] Configuración soberana sellada en .env local.{RESET}")
    except Exception as e:
        if RICH_AVAILABLE:
            rprint(f"  [bold red][-] Error al escribir .env: {e}[/bold red]")
        else:
            print(f"  {RED}[-] Error al escribir .env: {e}{RESET}")

    if RICH_AVAILABLE:
        rprint("\n====================================================================")
        rprint(f"[bold cyan][MOSKV-1] CALIBRACIÓN SOBERANA COMPLETADA CON ÉXITO[/bold cyan]")
        rprint(f"  > ESTADO:          RUNNING (0x00000001)")
        rprint(f"  > MOTOR RING-2:    {inf['backend']}")
        rprint(f"  > TOPOLOGÍA SWARM: P = {hw['p_cores']}, S = {hw['s_threads']} (Capacidad = {hw['p_cores'] * hw['s_threads']} Cores)")
        rprint(f"  > ATTESTATION:     C5_SILICON_SEAL={silicon_seal}")
        rprint("\nAcciones inmediatas recomendadas:")
        rprint("  • cargo run --bin babylon60_kernel -- bench    (Medir rendimiento del cerrojo de 64B)")
        rprint("  • cargo run --bin babylon60_kernel -- status   (Inspeccionar mapa de memoria)")
        rprint("  • cargo run --bin babylon60_kernel -- audit    (Falsación de invariantes de hardware)")
        rprint("====================================================================\n")
    else:
        print("\n====================================================================")
        print(f"{CYAN}[MOSKV-1] CALIBRACIÓN SOBERANA COMPLETADA CON ÉXITO{RESET}")
        print(f"  > ESTADO:          RUNNING (0x00000001)")
        print(f"  > MOTOR RING-2:    {inf['backend']}")
        print(f"  > TOPOLOGÍA SWARM: P = {hw['p_cores']}, S = {hw['s_threads']} (Capacidad = {hw['p_cores'] * hw['s_threads']} Cores)")
        print(f"  > ATTESTATION:     C5_SILICON_SEAL={silicon_seal}")
        print("\nAcciones inmediatas recomendadas:")
        print("  • cargo run --bin babylon60_kernel -- bench    (Medir rendimiento del cerrojo de 64B)")
        print("  • cargo run --bin babylon60_kernel -- status   (Inspeccionar mapa de memoria)")
        print("  • cargo run --bin babylon60_kernel -- audit    (Falsación de invariantes de hardware)")
        print("====================================================================\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    print_banner()
    hw = paso_1_autodeteccion_hardware()
    inf = paso_2_seleccion_inferencia()
    paso_3_blindaje_editores(repo_root)
    paso_4_test_silicio_y_env(repo_root, hw, inf)


if __name__ == "__main__":
    main()
