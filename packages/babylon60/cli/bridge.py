# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import argparse
import os
import subprocess
import sys
from pathlib import Path


def _find_tauri_root() -> Path | None:
    """Localiza el directorio que contiene src-tauri/Cargo.toml por heurística:
    cwd primero, luego relativo a la ubicación de este fichero instalado."""
    candidates = (
        Path.cwd() / "src-tauri",
        Path(__file__).resolve().parent.parent.parent / "src-tauri",
    )
    for candidate in candidates:
        if (candidate / "Cargo.toml").exists():
            return candidate
    return None


def main() -> None:
    """
    Ignición Determinista del Puente CORTEX.
    """
    args = sys.argv[1:]
    
    tauri_dir = _find_tauri_root()
    if tauri_dir is None:
        print(
            "🔴 [FATAL] No se pudo localizar el root físico Causal-Determinist (src-tauri/Cargo.toml).\n"
            "    cortex-bridge requiere el checkout completo del monorepo BABYLON-60.",
            file=sys.stderr,
        )
        sys.exit(1)
        
    repo_root = tauri_dir.parent

    # HANDOFF SOBERANO A MOSKV-1 (Zero-Python Memory Overhead)
    if "status" in args or "--status" in args:
        kernel_path = repo_root / "target" / "debug" / "babylon60_kernel"
        
        if not kernel_path.exists():
            print("🟢 [CORTEX-BRIDGE] Compilando Sovereign Kernel (MOSKV-1) por primera vez...")
            try:
                subprocess.run(["cargo", "build", "--bin", "babylon60_kernel"], cwd=str(repo_root), check=True)
            except subprocess.CalledProcessError:
                sys.exit(1)
        
        # El asesinato de Python. Reemplazo del espacio de memoria por el Kernel C-ABI.
        os.execv(str(kernel_path), [str(kernel_path), "--status"])

    # Fallback clásico a Tauri si no hay handoff explícito
    cargo_toml = tauri_dir / "Cargo.toml"
    print("🟢 [CORTEX-BRIDGE] Transducción iniciada. Ignición de Interfaz Tauri.")
    try:
        subprocess.run(["cargo", "run", "--manifest-path", str(cargo_toml)], check=True)
    except FileNotFoundError:
        print("🔴 [FATAL] 'cargo' no está instalado o no está en PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n💥 [SIGKILL] Puente CORTEX desconectado. Ineficiencia purgada.")
        sys.exit(0)

if __name__ == "__main__":
    main()
