import os
import subprocess
import sys
from pathlib import Path

def main() -> None:
    """
    Ignición Determinista del Puente CORTEX.
    Busca la raíz del workspace (30_BABYLON-60) y compila/ejecuta la topología C5-REAL (moskv-1-apex).
    """
    # Encontrar la raíz asumiendo la instalación (site-packages o editable)
    # Por heurística, buscamos el Cargo.toml en "src-tauri" desde el cwd, o desde este archivo.
    current_dir = Path.cwd()
    tauri_dir = current_dir / "src-tauri"

    if not tauri_dir.exists():
        # Si no se encuentra localmente, intentar ubicar basándonos en la ruta de este script
        project_root = Path(__file__).resolve().parent.parent.parent
        tauri_dir = project_root / "src-tauri"
        
    cargo_toml = tauri_dir / "Cargo.toml"

    if not cargo_toml.exists():
        print(f"🔴 [FATAL] No se pudo localizar el root físico C5-REAL (src-tauri/Cargo.toml) en {tauri_dir}. Aislando entropía y abortando.", file=sys.stderr)
        sys.exit(1)

    print("🟢 [CORTEX-BRIDGE] Transducción iniciada. Ignición C5-REAL del Ledger Rust.")
    try:
        # BFT_KEY fallback logic (Zero static fallback is strictly handled in Rust, but we warn here if not present)
        bft_key = os.environ.get("CORTEX_BFT_KEY") or os.environ.get("CORTEX_VAULT_KEY")
        if not bft_key:
            print("🟡 [WARNING] CORTEX_BFT_KEY o CORTEX_VAULT_KEY no detectada. El núcleo Rust fallará (Zero Static HMAC Invariant).", file=sys.stderr)

        subprocess.run(["cargo", "run", "--manifest-path", str(cargo_toml)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"🔴 [FATAL] El Puente CORTEX colapsó termodinámicamente. Exit Code: {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n💥 [SIGKILL] Puente CORTEX desconectado. Anergía purgada.")
        sys.exit(0)

if __name__ == "__main__":
    main()
