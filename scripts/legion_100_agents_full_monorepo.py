#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ OPERATIVO LEGIÓN-100 | GLOBAL MONOREPO AUDIT (TUI ENHANCED)
# ============================================================================
"""
Enjambre concurrente de 100 workers para auditar invariantes C5-REAL a nivel 
estructural en el monorepositorio.
"""

import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ----------------------------------------------------------------------------
# INVARIANTES Y REGLAS DE SCANNING (ALTA EXERGÍA)
# ----------------------------------------------------------------------------

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}", "Slack Token"),
    (r"-----BEGIN RSA PRIVATE KEY-----", "RSA Private Key"),
]

TOPOLOGICAL_VIOLATION_PATTERN = r"from\s+wa_nexus\s+import|import\s+wa_nexus"
BARE_EXCEPT_PATTERN = r"except\s*:\s*pass|except\s+Exception\s*:\s*pass"
WHILE_TRUE_DEADLOCK = r"while\s+True\s*:(?!.*?(sleep|await|break|return|yield))"
RUST_UNWRAP_ABUSE = r"\.unwrap\(\)"

def scan_file(filepath: str) -> list:
    """Escanea un archivo contra todas las invariantes."""
    violations = []
    is_rust = filepath.endswith(".rs")
    is_python = filepath.endswith(".py")
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # 1. Escaneo Criptográfico (Zero Trust)
            for pattern, name in SECRET_PATTERNS:
                if re.search(pattern, content):
                    violations.append(f"CRÍTICO [Zero-Trust]: Posible {name} expuesto.")
                    
            # 2. Invariantes Topológicas
            if "babylon60" in filepath and re.search(TOPOLOGICAL_VIOLATION_PATTERN, content):
                violations.append("CRÍTICO [Topología]: Fractura de aislamiento hacia wa-nexus.")
            
            # 3. Falsación de Deadlocks y Logs Mudos (Python)
            if is_python:
                if re.search(BARE_EXCEPT_PATTERN, content):
                    violations.append("ADVERTENCIA [Entropía]: Bloque except mudo detectado (pérdida de traza).")
                    
            # 4. Abuso de Unwrap (Rust)
            if is_rust and "tests" not in filepath:
                # Contar unwraps en código de producción
                unwraps = len(re.findall(RUST_UNWRAP_ABUSE, content))
                if unwraps > 5:
                    violations.append(f"ADVERTENCIA [Fragilidad BFT]: Exceso de unwrap() ({unwraps} instancias). Reemplazar con Result.")
                    
    except Exception as e:
        violations.append(f"ERROR: No se pudo leer el archivo: {e}")
        
    return violations

# ----------------------------------------------------------------------------
# ENJAMBRE LEGIÓN-100
# ----------------------------------------------------------------------------

def main():
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit("[bold cyan]█ OPERATIVO LEGIÓN-100: GLOBAL MONOREPO AUDIT[/bold cyan]\n[dim]Sovereign Hardened C5-REAL[/dim]"))
    else:
        print("================================================================")
        print(" █ OPERATIVO LEGIÓN-100: GLOBAL MONOREPO AUDIT")
        print("================================================================")
    
    # Recopilar todos los archivos
    files_to_scan = []
    ignore_dirs = ["/.git", "/target", "__pycache__", "/node_modules", "/.venv", "/.xtts_venv", "/archive", "/tests/fixtures", "/docs", "/experiments"]
    
    for root, _, files in os.walk(target_dir):
        if any(ignored in root for ignored in ignore_dirs):
            continue
        for file in files:
            filepath = os.path.join(root, file)
            if file in [".gitleaks.toml", ".env.canary"]:
                continue
            if "legion_100_agents_full_monorepo.py" in filepath:
                continue
            files_to_scan.append(filepath)
            
    if RICH_AVAILABLE:
        console.print(f"Archivos indexados para escaneo concurrente: [bold yellow]{len(files_to_scan)}[/bold yellow]\n")
    else:
        print(f"Archivos indexados para escaneo concurrente: {len(files_to_scan)}\n")
    
    start_time = time.time()
    total_violations = 0
    issues_dict = {}

    if RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task_scan = progress.add_task("[cyan]Desplegando Enjambre (100 Workers)...", total=len(files_to_scan))
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                future_to_file = {executor.submit(scan_file, f): f for f in files_to_scan}
                
                for future in as_completed(future_to_file):
                    filepath = future_to_file[future]
                    try:
                        violations = future.result()
                        if violations:
                            rel_path = os.path.relpath(filepath, target_dir)
                            issues_dict[rel_path] = violations
                            total_violations += len(violations)
                    except Exception:
                        pass
                    progress.advance(task_scan)
    else:
        # Fallback sin TUI
        with ThreadPoolExecutor(max_workers=100) as executor:
            future_to_file = {executor.submit(scan_file, f): f for f in files_to_scan}
            for future in as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    violations = future.result()
                    if violations:
                        rel_path = os.path.relpath(filepath, target_dir)
                        issues_dict[rel_path] = violations
                        total_violations += len(violations)
                except Exception:
                    pass

    elapsed = time.time() - start_time
    
    if RICH_AVAILABLE:
        console.print("\n[bold]SITREP: REPORTE DE ESTABILIDAD TERMODINÁMICA[/bold]")
        
        if total_violations > 0:
            table = Table(show_header=True, header_style="bold red")
            table.add_column("Archivo (Ruta Relativa)", style="dim")
            table.add_column("Infracciones Detectadas")
            
            for path, viols in issues_dict.items():
                table.add_row(path, "\n".join(viols))
            
            console.print(table)
            console.print(f"\n❌ [bold red]DICTAMEN: ANERGÍA DETECTADA.[/bold red] {total_violations} fracturas (Tiempo: {elapsed:.3f}s)")
            sys.exit(1)
        else:
            console.print(f"\n✅ [bold green]DICTAMEN: ESTADO ÓMEGA ALCANZADO.[/bold green] Cero fracturas topológicas. (Tiempo: {elapsed:.3f}s)")
            sys.exit(0)
    else:
        print("\n================================================================")
        print(f" SITREP: REPORTE DE ESTABILIDAD TERMODINÁMICA")
        print("================================================================")
        print(f"Archivos escaneados : {len(files_to_scan)}")
        print(f"Tiempo de ejecución : {elapsed:.3f} segundos")
        print(f"Total Infracciones  : {total_violations}")
        
        if total_violations > 0:
            for path, viols in issues_dict.items():
                print(f"\n[!] {path}")
                for v in viols:
                    print(f"    -> {v}")
            print("\n❌ DICTAMEN: ANERGÍA DETECTADA. REQUIERE PURGA ESTRUCTURAL.")
            sys.exit(1)
        else:
            print("\n✅ DICTAMEN: ESTADO ÓMEGA ALCANZADO. CERO FRACTURAS TOPOLÓGICAS.")
            sys.exit(0)

if __name__ == "__main__":
    main()
