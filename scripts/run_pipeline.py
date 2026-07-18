#!/usr/bin/env python3
"""
CORTEX Phase Cascade Runner / Transductor de Ejecución en Cascada (C5-REAL).
Orquestador determinista para ignición secuencial de las 4 fases del sistema.
"""

import os
import sys
import subprocess
import time
import argparse

# Configuración de fases y sus scripts correspondientes
PHASES = {
    0: {
        "name": "Inicialización y Canales",
        "scripts": ["00_init_ledger.py", "01_cdp_transducer.py"],
    },
    1: {
        "name": "Generación de Código (Codegen)",
        "scripts": [
            "10_codegen_constants.py",
            "11_codegen_noether.py",
            "12_codegen_observer.py",
            "13_codegen_haskell.py",
            "14_codegen_neuro.py",
            "15_codegen_tts.py",
            "16_codegen_primitives.py",
            "18_codegen_kimi.py",
        ],
    },
    2: {
        "name": "Validación, Simulación e Iteración",
        "scripts": [
            "20_stress_db.py",
            "21_iter_100.py",
            "22_iter_5000.py",
            "23_iter_ultrathink.py",
        ],
    },
    3: {
        "name": "Auditoría, Consolidación y Mantenimiento",
        "scripts": ["30_audit_loop.py", "31_autoconsolidate.py", "32_legion_purge.py"],
    },
}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(script_name: str) -> bool:
    script_path = os.path.join(PROJECT_ROOT, "scripts", script_name)
    if not os.path.exists(script_path):
        print(f"❌ [ERROR] Script no encontrado físicamente: {script_name}")
        return False

    print(f"\n⚡ [EJECUCIÓN] Iniciando: {script_name}...")
    start_time = time.perf_counter()

    try:
        # Ejecutar script heredando el python environment
        cmd = [sys.executable, script_path]
        # Para iteraciones largas, dejamos que impriman en vivo
        process = subprocess.Popen(
            cmd, stdout=sys.stdout, stderr=sys.stderr, cwd=PROJECT_ROOT
        )
        exit_code = process.wait()

        elapsed = time.perf_counter() - start_time
        if exit_code == 0:
            print(f"✅ [SUCCESS] {script_name} completado con éxito en {elapsed:.4f}s.")
            return True
        else:
            print(
                f"❌ [FAILURE] {script_name} falló con código de salida {exit_code} después de {elapsed:.4f}s."
            )
            return False

    except Exception as e:
        print(f"💥 [CRITICAL] Excepción al lanzar {script_name}: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orquestador de Cascada de Fases C5-REAL."
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[0, 1, 2, 3],
        help="Ejecutar una fase específica completa (0-3).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecutar la cascada completa de todas las fases (0 a 3).",
    )
    parser.add_argument(
        "--script",
        type=str,
        help="Ejecutar un script individual por su nombre de archivo.",
    )

    args = parser.parse_args()

    if not (args.all or args.phase is not None or args.script):
        print("=== CORTEX-OMEGA: PIPELINE RUNNER ===")
        print(
            "Uso: python3 scripts/run_pipeline.py [--all] [--phase <0-3>] [--script <nombre>]"
        )
        print("\nFases Disponibles:")
        for pid, phase in PHASES.items():
            print(f"  Fase {pid}: {phase['name']}")
            for s in phase["scripts"]:
                print(f"    - {s}")
        sys.exit(0)

    print("=== CORTEX-OMEGA: IGNICIÓN DE CASCADA NATURAL ===")
    start_global = time.perf_counter()

    scripts_to_run: list[str] = []

    if args.script:
        scripts_to_run = [args.script]
    elif args.phase is not None:
        phase = PHASES[args.phase]
        print(f"🎯 Ejecutando Fase {args.phase}: {phase['name']}")
        scripts_to_run = list(phase["scripts"])
    elif args.all:
        print("🌀 Lanzando Cascada Completa (Fases 0, 1, 2, 3)...")
        for pid in sorted(PHASES.keys()):
            # Saltamos scripts interactivos o de bucle infinito (como cdp transducer o iter_5000/ultrathink si no tienen argumentos cortos)
            # Nota: cdp_transducer intenta abrir conexión con puerto 9222.
            # En la cascada automática, si no hay chrome corriendo, puede fallar o continuar.
            # Los scripts de iteración larga o estrés pueden limitarse si es necesario.
            for s in PHASES[pid]["scripts"]:
                scripts_to_run.append(s)

    # Ejecución secuencial en cascada
    success = True
    for script in scripts_to_run:
        # Si ejecutamos --all, saltamos cdp_transducer y stress_db / itera5000 / itera_ultrathink / audit_loop de forma automática para evitar bloqueos
        if args.all and script in [
            "01_cdp_transducer.py",
            "22_iter_5000.py",
            "23_iter_ultrathink.py",
            "30_audit_loop.py",
        ]:
            print(
                f"⏩ [SKIP] Saltando {script} en cascada general para evitar bloqueos/esperas de puerto o bucles infinitos."
            )
            continue

        res = run_script(script)
        if not res:
            success = False
            break

    elapsed_global = time.perf_counter() - start_global
    print("\n=== FIN DE LA CASCADA ===")
    print(f"Resultado General: {'ÉXITO (C5-REAL)' if success else 'FALLO (ANERGÍA)'}")
    print(f"Tiempo Total Transcurrido: {elapsed_global:.4f}s")

    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
