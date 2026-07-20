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
import concurrent.futures

# Configuración de fases y sus scripts correspondientes
PHASES = {
    0: {
        "name": "Inicialización y Canales",
        "scripts": ["00_init_ledger.py", "01_cdp_transducer.py"],
    },
    1: {
        "name": "Generación de Código (Codegen)",
        "scripts": [
            "10_codegen_engine.py",
            "16_codegen_primitives.py",
            "17_codegen_github.py",
        ],
    },
    2: {
        "name": "Calidad de Código (Formatting & Linting)",
        "scripts": [
            "20_format_all.py",
            "21_lint_clippy.py",
        ],
    },
    3: {
        "name": "Verificación y Pruebas Unitarias",
        "scripts": [
            "30_test_pytest.py",
            "31_test_go.py",
            "32_test_cargo.py",
        ],
    },
    4: {
        "name": "Simulación de Carga, Iteración y MCTS",
        "scripts": [
            "40_stress_db.py",
            "41_iter_100.py",
            "42_iter_5000.py",
            "43_iter_ultrathink.py",
        ],
    },
    5: {
        "name": "Auditoría, Consolidación y Mantenimiento",
        "scripts": [
            "50_audit_loop.py",
            "51_autoconsolidate.py",
            "52_legion_purge.py",
            "53_centuria_swarm.py",
        ],
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

    except (OSError, ValueError, subprocess.SubprocessError) as e:
        print(f"💥 [CRITICAL] Excepción al lanzar {script_name}: {e}")
        return False


def run_script_captured(script_name: str) -> tuple[bool, float, str, str]:
    script_path = os.path.join(PROJECT_ROOT, "scripts", script_name)
    if not os.path.exists(script_path):
        return False, 0.0, "", f"Script no encontrado: {script_name}"

    start_time = time.perf_counter()
    try:
        cmd = [sys.executable, script_path]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        elapsed = time.perf_counter() - start_time
        return res.returncode == 0, elapsed, res.stdout, res.stderr
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return False, 0.0, "", f"Excepción: {str(e)}"


def run_scripts_parallel(scripts: list[str]) -> bool:
    print(f"\n⚡ [PARALELO] Lanzando {len(scripts)} scripts en paralelo...")
    success = True
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(run_script_captured, s): s for s in scripts}
        for future in concurrent.futures.as_completed(futures):
            script = futures[future]
            ok, elapsed, stdout, stderr = future.result()
            if ok:
                print(f"✅ [SUCCESS] {script} completado con éxito en {elapsed:.4f}s.")
                if stdout.strip():
                    print(f"--- Output {script} ---\n{stdout.strip()}")
            else:
                success = False
                print(f"❌ [FAILURE] {script} falló en {elapsed:.4f}s.")
                if stdout.strip():
                    print(f"--- Stdout {script} ---\n{stdout.strip()}")
                if stderr.strip():
                    print(f"--- Stderr {script} ---\n{stderr.strip()}")
    return success


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orquestador de Cascada de Fases C5-REAL."
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[0, 1, 2, 3, 4, 5],
        help="Ejecutar una fase específica completa (0-5).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecutar la cascada completa de todas las fases (0 a 5).",
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
            "Uso: python3 scripts/run_pipeline.py [--all] [--phase <0-5>] [--script <nombre>]"
        )
        print("\nFases Disponibles:")
        for pid, phase in PHASES.items():
            print(f"  Fase {pid}: {phase['name']}")
            for s in phase["scripts"]:
                print(f"    - {s}")
        sys.exit(0)

    print("=== CORTEX-OMEGA: IGNICIÓN DE CASCADA NATURAL ===")
    start_global = time.perf_counter()

    success = True

    if args.script:
        success = run_script(args.script)
    elif args.phase is not None:
        phase = PHASES[args.phase]
        print(f"🎯 Ejecutando Fase {args.phase}: {phase['name']}")
        scripts = list(phase["scripts"])
        if args.phase in [1, 3]:
            success = run_scripts_parallel(scripts)
        else:
            for s in scripts:
                if not run_script(s):
                    success = False
                    break
    elif args.all:
        print("🌀 Lanzando Cascada Completa (Fases 0 a 5)...")
        skip_list = [
            "01_cdp_transducer.py",
            "42_iter_5000.py",
            "43_iter_ultrathink.py",
            "50_audit_loop.py",
        ]
        for pid in sorted(PHASES.keys()):
            phase = PHASES[pid]
            scripts = [s for s in phase["scripts"] if s not in skip_list]
            if not scripts:
                continue
            print(f"\n🎯 Ejecutando Fase {pid}: {phase['name']}")
            if pid in [1, 3]:
                if not run_scripts_parallel(scripts):
                    success = False
                    break
            else:
                phase_success = True
                for s in scripts:
                    if not run_script(s):
                        phase_success = False
                        break
                if not phase_success:
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
