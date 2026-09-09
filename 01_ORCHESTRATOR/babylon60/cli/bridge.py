# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import subprocess
import sys
from pathlib import Path


def _find_tauri_root() -> Path | None:
    """Localiza el directorio que contiene src-tauri/Cargo.toml por heurística:
    cwd primero, luego relativo a la ubicación de este fichero instalado."""
    candidates = (
        Path.cwd() / "apps" / "src-tauri",
        Path.cwd() / "apps" / "babylon60-ide" / "src-tauri",
        Path.cwd() / "src-tauri",
        Path(__file__).resolve().parent.parent.parent.parent / "apps" / "src-tauri",
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

    # The actual rust workspace root is BABYLON-60 (donde está el target dir general)
    repo_root = tauri_dir
    while (
        not (repo_root / "Cargo.toml").exists()
        or not (repo_root / "target").exists()
        and repo_root.name != "BABYLON-60"
    ):
        if repo_root.parent == repo_root:
            # Fallback to tauri_dir parent if we reach filesystem root
            repo_root = tauri_dir.parent.parent
            break
        repo_root = repo_root.parent

    if not (repo_root / "target").exists():
        repo_root = Path.cwd()

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
