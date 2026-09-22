#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ BALAG-60 SOVEREIGN ACOUSTICS & PHYSICAL RESONATOR CLI | C5-REAL
# ============================================================================
"""
BALAG-60 Sovereign Acoustics CLI:
  - Microtonal Scala (.scl) scale generation (Just Intonation, Pythagorean, Sexagesimal)
  - Euclidean Bjorklund rhythm computation & inter-pulse entropy evaluation
  - Physical modal resonator audio synthesis (48 kHz / 16-bit stereo PCM)
  - Direct centralization in ~/Music/BALAG60_ACOUSTICS (RULE[music_assets_centralization_invariant])
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Importar motor DSP canónico
from scripts.c5_demos.poc_acoustic_exergy_dsp import (
    run_pipeline,
    build_just_intonation_12,
    build_pythagorean_12,
    build_babylon_sexagesimal_harmonics,
    BjorklundEuclidean,
    compute_sha256,
)


def cmd_synthesize(args: argparse.Namespace) -> int:
    """Ejecuta la pipeline completa de síntesis DSP acústica y centralización."""
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    sitrep = run_pipeline(output_dir=output_dir)

    print(f"\n[✓] SÍNTESIS COMPLETADA CON ÉXITO: {len(sitrep['rendered_audio_assets'])} activos generados.")
    print("[✓] Activos centralizados en: ~/Music/BALAG60_ACOUSTICS")
    return 0


def cmd_scala(args: argparse.Namespace) -> int:
    """Genera y exporta escalas microtonales no temperadas en formato Scala (.scl)."""
    target_dir = Path(args.destination).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    scales = [
        build_just_intonation_12(),
        build_pythagorean_12(),
        build_babylon_sexagesimal_harmonics(),
    ]

    saved = []
    for sc in scales:
        dest = target_dir / f"{sc.name}.scl"
        sc.save(dest)
        saved.append(
            {
                "name": sc.name,
                "path": str(dest),
                "notes": sc.num_notes,
                "sha256": compute_sha256(dest),
            }
        )

    print("=" * 70)
    print(" 🎼 BALAG-60 | GENERADOR DE ESCALAS NO TEMPERADAS SCALA (.SCL)")
    print("=" * 70)
    print(f"[*] Directorio de Destino: {target_dir}")
    for item in saved:
        print(f"  • {item['name'] + '.scl':<35} ({item['notes']} notas) | SHA256: {item['sha256'][:16]}...")

    if args.fl_studio:
        fl_tuning_dir = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Settings" / "Tuning"
        if fl_tuning_dir.exists():
            for sc in scales:
                sc.save(fl_tuning_dir / f"{sc.name}.scl")
            print(f"\n[+] Desplegadas {len(scales)} afinaciones en FL Studio Tuning: {fl_tuning_dir}")
        else:
            print(f"\n[!] Directorio FL Studio no detectado ({fl_tuning_dir}). Despliegue omitido.")

    print("=" * 70)
    return 0


def cmd_euclidean(args: argparse.Namespace) -> int:
    """Calcula y muestra patrones rítmicos euclidianos E(k, n) mediante algoritmo de Bjorklund."""
    k = args.pulses
    n = args.steps
    pattern = BjorklundEuclidean.generate(k, n)
    entropy_val = BjorklundEuclidean.calculate_shannon_entropy(pattern)

    pattern_str = " ".join("X" if bit == 1 else "." for bit in pattern)

    print("=" * 70)
    print(f" 🥁 BALAG-60 | MATRIZ DE RITMO EUCLIDIANO E({k}, {n})")
    print("=" * 70)
    print(f"  Pulsos (k)           : {k}")
    print(f"  Pasos (n)            : {n}")
    print(f"  Secuencia Binaria    : {pattern}")
    print(f"  Visualización        : [ {pattern_str} ]")
    print(f"  Entropía de Shannon  : {entropy_val:.4f} bits")
    print("=" * 70)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="babylon60-acoustics",
        description="BALAG-60 Sovereign Acoustic Synthesis & Physical Resonator CLI (C5-REAL)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # synthesize
    p_synth = subparsers.add_parser("synthesize", help="Síntesis completa de activos de audio, afinaciones y ritmos")
    p_synth.add_argument(
        "--output-dir", "-o", default=None, help="Directorio de destino (por defecto: data/c5_acoustics)"
    )

    # scala
    p_scala = subparsers.add_parser("scala", help="Exportar escalas en formato Scala (.scl)")
    p_scala.add_argument("--destination", "-d", default="data/c5_acoustics/scala_tunings", help="Ruta de salida")
    p_scala.add_argument(
        "--fl-studio", action="store_true", default=False, help="Copiar también a la carpeta Tuning de FL Studio"
    )

    # euclidean
    p_euc = subparsers.add_parser("euclidean", help="Calcular ritmo euclidiano de Bjorklund E(k, n)")
    p_euc.add_argument("pulses", type=int, help="Número de pulsos activos (k)")
    p_euc.add_argument("steps", type=int, help="Número total de pasos en el compás (n)")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "synthesize":
        return cmd_synthesize(args)
    elif args.command == "scala":
        return cmd_scala(args)
    elif args.command == "euclidean":
        return cmd_euclidean(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
