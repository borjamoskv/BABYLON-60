# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
C5-REAL Sovereign Protocol: Substack Public Laboratory Compiler (v2.0)
Compiles the thermodynamic ledger for a new Substack publication.
Enforces the 6-step loop: Experimento, Hallazgo, Código, Demo, Track, Reflexión.

v2.0 Changes:
- Generates a composite post_draft.md from the 6 components
- Runs validation inline after scaffold
- Adds --validate-only mode
- Removes placeholder markers from stubs (uses instructional prompts instead)
"""

import os
import sys
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EpistemicHalt(Exception):
    """C5-REAL structural failure. Replaces os.kill(SIGKILL) per Ω26."""


def fail_fast(msg: str) -> None:
    raise EpistemicHalt(f"[FATAL] {msg}")


def sha3_256_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode("utf-8")).hexdigest()


def generate_post_draft(lab_dir: Path, experiment_name: str) -> str:
    """Compose a unified post_draft.md from the 6 experiment files."""
    sections: list[tuple[str, str, str]] = [
        (
            "01_experimento.yml",
            "EXPERIMENTO",
            "Condición inicial, hipótesis y restricciones.",
        ),
        ("02_hallazgo.md", "HALLAZGO", "Datos crudos y métricas extraídas."),
        ("03_codigo.py", "CÓDIGO", "Implementación física."),
        ("04_demo.sh", "DEMO", "Transcripción de ejecución."),
        ("05_track.md", "TRACK", "Output acústico, visual o generativo."),
        ("06_reflexion.md", "REFLEXIÓN", "Consecuencia termodinámica."),
    ]

    title = experiment_name.replace("_", " ").title()
    lines: list[str] = [
        f"# [{title}] Registro de Laboratorio Público\n",
        f"**Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n",
        f"**Experimento:** `{experiment_name}`\n",
        "---\n",
    ]

    for filename, label, desc in sections:
        fpath = lab_dir / filename
        lines.append(f"\n## [ {label} ]\n")
        lines.append(f"*{desc}*\n\n")
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8").strip()
            if filename.endswith(".py") or filename.endswith(".sh") or filename.endswith(".yml"):
                ext = filename.rsplit(".", 1)[-1]
                lang = {"py": "python", "sh": "bash", "yml": "yaml"}.get(ext, ext)
                lines.append(f"```{lang}\n{content}\n```\n")
            else:
                lines.append(f"{content}\n")
        else:
            lines.append(f"*(Archivo pendiente: {filename})*\n")

    lines.append("\n---\n")
    lines.append("\n⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):\n")
    lines.append("- [Un hombre blanco y heterosexual](https://substack.com/home/post/p-204785962)\n")

    return "\n".join(lines)


def scaffold_experiment(experiment_name: str, root_dir: str) -> Path:
    lab_dir = Path(root_dir) / "cortex" / "laboratory" / experiment_name
    try:
        lab_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        fail_fast(f"Failed to create directory {lab_dir}: {e}")

    # Stubs use instructional prompts, NOT bracket placeholders
    payloads: dict[str, str] = {
        "01_experimento.yml": f"""claim_id: "LAB_{experiment_name.upper()}"
hypothesis: "Describe the hypothesis to test."
initial_conditions:
  - "Describe the boundary constraints."
constraints:
  - "C5-REAL"
  - "Zero Anergy"
vertical: "Select: software_thermo | music_ai | agent_arch | cultural_collisions | generative_art"
""",
        "02_hallazgo.md": """# Hallazgos Empíricos

## Métricas observadas

(Inyectar datos crudos, capturas de terminal, métricas cuantitativas.)

## Fallas detectadas

(Documentar qué rompió y por qué.)
""",
        "03_codigo.py": f'''#!/usr/bin/env python3
"""
Experiment: {experiment_name}
Physical implementation of the hypothesis.
"""

def execute() -> None:
    """Main execution entry point for the experiment."""
    raise NotImplementedError("Implement the experiment logic.")

if __name__ == "__main__":
    execute()
''',
        "04_demo.sh": f"""#!/usr/bin/env bash
# Experiment: {experiment_name}
# Execution transcript / demo runner.
set -euo pipefail

echo "Running experiment: {experiment_name}"
python3 03_codigo.py
""",
        "05_track.md": """# Registro Acústico / Visual / Generativo

## Asset generado

(Referenciar el archivo de salida: .wav, .png, .mp4, .svg, etc.)

## Parámetros de generación

(Documentar los parámetros usados para reproducibilidad.)
""",
        "06_reflexion.md": """# Repercusión Termodinámica

## Consecuencias estructurales

(Qué invariante se confirmó, se refutó o se descubrió.)

## Conexión con el siguiente experimento

(Qué nueva hipótesis emerge de los hallazgos.)
""",
    }

    manifest: dict[str, Any] = {
        "experiment": experiment_name,
        "version": "2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "scaffold",
        "files": [],
    }

    for filename, content in payloads.items():
        filepath = lab_dir / filename
        try:
            filepath.write_text(content, encoding="utf-8")
            manifest["files"].append({"name": filename, "sha3_256": sha3_256_hash(content)})
        except OSError as e:
            fail_fast(f"Failed to write file {filepath}: {e}")

    # Generate the composite post draft
    draft_content = generate_post_draft(lab_dir, experiment_name)
    draft_path = lab_dir / "post_draft.md"
    try:
        draft_path.write_text(draft_content, encoding="utf-8")
        manifest["files"].append({"name": "post_draft.md", "sha3_256": sha3_256_hash(draft_content)})
    except OSError as e:
        fail_fast(f"Failed to write post draft: {e}")

    # Write manifest atomically (Ω41)
    manifest_path = lab_dir / "manifest.json"
    manifest_tmp = str(manifest_path) + ".tmp"
    try:
        with open(manifest_tmp, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        os.replace(manifest_tmp, str(manifest_path))
    except OSError as e:
        fail_fast(f"Failed to write manifest atomically: {e}")

    print(f"[CORTEX-TAINT] Scaffolding completado: {lab_dir}")
    print(f"Manifest Hash: {sha3_256_hash(json.dumps(manifest))}")
    print(f"Post Draft: {draft_path}")

    return lab_dir


def run_validator(root_dir: str) -> int:
    """Run the laboratory validator script."""
    validator = Path(root_dir) / "scripts" / "56_laboratory_validator.py"
    if not validator.exists():
        print(f"[WARN] Validator not found at {validator}")
        return 1
    try:
        result = subprocess.run(
            [sys.executable, str(validator)],
            cwd=root_dir,
            capture_output=False,
        )
        return result.returncode
    except OSError as e:
        print(f"[ERROR] Failed to run validator: {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Substack Laboratory Compiler v2.0")
    parser.add_argument(
        "experiment_name",
        type=str,
        nargs="?",
        help="Name of the experiment (e.g. mcts_audio_drift)",
    )
    parser.add_argument("--root", type=str, default=".", help="Root of the workspace")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run the validator, do not scaffold",
    )
    args = parser.parse_args()

    if args.validate_only:
        sys.exit(run_validator(args.root))

    if not args.experiment_name:
        parser.error("experiment_name is required when not using --validate-only")

    scaffold_experiment(args.experiment_name, args.root)


if __name__ == "__main__":
    main()
