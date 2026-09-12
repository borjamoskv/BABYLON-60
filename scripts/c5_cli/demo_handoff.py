#!/usr/bin/env python3
import sys
import subprocess
import os

def main() -> None:
    # Simulamos el entrypoint del paquete instalado por pip (babylon60)
    args = sys.argv[1:]
    
    if args and args[0] == "status":
        # Aquí ocurre el HANDOFF. Python delega instantáneamente la ejecución
        # al binario nativo compilado de Rust en Ring-0.
        
        # Obtenemos la ruta absoluta al binario compilado
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        kernel_path = os.path.join(repo_root, "target", "debug", "babylon60_kernel")
        
        if not os.path.exists(kernel_path):
            print("[PYTHON] Compilando el Kernel Soberano por primera vez...")
            subprocess.run(["cargo", "build", "--bin", "babylon60_kernel"], cwd=repo_root, check=True)
            
        # Reemplazamos el proceso Python actual por el binario de Rust usando execv.
        # Esto asesina el intérprete de Python y le da el control absoluto a Rust.
        os.execv(kernel_path, [kernel_path, "--status"])
    else:
        print("[PYTHON] CLI de BABYLON-60. Comandos disponibles: status")

if __name__ == "__main__":
    main()
