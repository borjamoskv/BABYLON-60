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
    Busca la raíz del workspace (BABYLON-60) y compila/ejecuta la topología C5-REAL (moskv-1-apex).

    Requiere el checkout completo del monorepo BABYLON-60 (con src-tauri/) y Rust/Cargo
    instalados. No es funcional desde una instalación aislada `pip install cortex-persist`.
    """
    argparse.ArgumentParser(
        prog="cortex-bridge",
        description="Ignición del Puente CORTEX (Tauri/Rust). Requiere checkout completo de BABYLON-60.",
    ).parse_args()  # sin opciones propias; solo habilita -h/--help

    tauri_dir = _find_tauri_root()
    if tauri_dir is None:
        print(
            "🔴 [FATAL] No se pudo localizar el root físico C5-REAL (src-tauri/Cargo.toml).\n"
            "    cortex-bridge requiere el checkout completo del monorepo BABYLON-60\n"
            "    (no funciona desde una instalación aislada `pip install cortex-persist`).\n"
            "    Clona el repositorio completo: git clone git@github.com:borjamoskv/BABYLON-60.git",
            file=sys.stderr,
        )
        sys.exit(1)

    cargo_toml = tauri_dir / "Cargo.toml"

    print("🟢 [CORTEX-BRIDGE] Transducción iniciada. Ignición C5-REAL del Ledger Rust.")
    try:
        # BFT_KEY fallback logic (Zero static fallback is strictly handled in Rust, but we warn here if not present)
        bft_key = os.environ.get("CORTEX_BFT_KEY") or os.environ.get("CORTEX_VAULT_KEY")
        if not bft_key:
            print(
                "🟡 [WARNING] CORTEX_BFT_KEY o CORTEX_VAULT_KEY no detectada. "
                "El núcleo Rust fallará (Zero Static HMAC Invariant).",
                file=sys.stderr,
            )

        subprocess.run(["cargo", "run", "--manifest-path", str(cargo_toml)], check=True)
    except FileNotFoundError:
        print(
            "🔴 [FATAL] 'cargo' no está instalado o no está en PATH. Instala Rust: https://rustup.rs",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"🔴 [FATAL] El Puente CORTEX colapsó termodinámicamente. Exit Code: {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n💥 [SIGKILL] Puente CORTEX desconectado. Anergía purgada.")
        sys.exit(0)


if __name__ == "__main__":
    main()
