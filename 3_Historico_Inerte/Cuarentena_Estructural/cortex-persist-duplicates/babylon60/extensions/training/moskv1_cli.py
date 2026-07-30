#!/usr/bin/env python3
# [C5-REAL] Exergy-Maximized
# Author: borjamoskv
# License: Apache-2.0
"""
MOSKV-1 CLI v2.0 — Interfaz de línea de comandos para el Kernel Cognitivo Híbrido.

Commands:
    compile    — Compilar dataset instruccional desde CORTEX
    train      — Ejecutar LoRA fine-tuning con MLX
    register   — Registrar modelo en Ollama
    validate   — Validar calidad del dataset compilado
    stats      — Mostrar estadísticas del dataset compilado
    health     — Verificar estado de Ollama y modelos disponibles
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections import Counter
from pathlib import Path

logger = logging.getLogger("babylon60.extensions.training.cli")


def cmd_compile(workspace: str | None = None) -> int:
    """Compile the full MOSKV-1 training dataset."""
    from babylon60.extensions.training.moskv1_dataset_compiler import MOSKV1DatasetCompiler

    ws = Path(workspace) if workspace else Path.cwd()
    compiler = MOSKV1DatasetCompiler(workspace_path=ws)

    logging.getLogger(__name__).info("🔧 MOSKV-1 Dataset Compilation v2.0 — C5-REAL")
    logging.getLogger(__name__).info(f"   Workspace: {ws}")
    logging.getLogger(__name__).info("")

    compiler.compile_full_dataset()

    # Export with train/val/test split
    sharegpt_path = compiler.export_sharegpt(split=True)
    alpaca_path = compiler.export_alpaca()

    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info("═══ COMPILATION STATS ═══")
    logging.getLogger(__name__).info(compiler.get_stats_yaml())
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info(f"📁 ShareGPT: {sharegpt_path}")
    logging.getLogger(__name__).info(f"📁 Alpaca:   {alpaca_path}")

    # Show split info
    dataset_dir = compiler.output_dir
    for name in ["train", "valid", "test"]:
        path = dataset_dir / f"{name}.jsonl"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                lines = sum(1 for _ in f)
            logging.getLogger(__name__).info(f"📁 {name}: {lines} entries ({path.stat().st_size / 1024:.1f} KB)")
    return 0


def cmd_train(
    model: str = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
    iters: int = 50,
    batch_size: int = 2,
    lora_layers: int = 16,
    learning_rate: float = 2e-5,
) -> int:
    """Execute MLX LoRA fine-tuning."""
    import subprocess

    dataset_dir = Path.home() / ".babylon60" / "training" / "datasets"
    adapter_path = Path.home() / ".babylon60" / "training" / "adapters"
    adapter_path.mkdir(parents=True, exist_ok=True)

    # Check for train.jsonl (v2 split format) or moskv1_dataset.jsonl
    if not (dataset_dir / "train.jsonl").exists():
        if (dataset_dir / "moskv1_dataset.jsonl").exists():
            logging.getLogger(__name__).info("⚠️ No train/val/test split found. Run 'compile' with v2.0 first.")
            logging.getLogger(__name__).info("   Falling back to moskv1_dataset.jsonl")
        else:
            logging.getLogger(__name__).info("❌ Dataset not found. Run 'compile' first.")
            return 1

    # Use non-deprecated mlx_lm subcommand syntax
    cmd = [
        sys.executable,
        "-m",
        "mlx_lm",
        "lora",
        "--model",
        model,
        "--train",
        "--data",
        str(dataset_dir),
        "--adapter-path",
        str(adapter_path),
        "--fine-tune-type",
        "lora",
        "--optimizer",
        "adamw",
        "--mask-prompt",
        "--num-layers",
        str(lora_layers),
        "--iters",
        str(iters),
        "--batch-size",
        "1",  # Lower batch size to reduce memory usage
        "--grad-accumulation-steps",
        "2",  # Accumulate gradient to maintain effective batch size of 2
        "--learning-rate",
        str(learning_rate),
        "--steps-per-report",
        "10",
        "--steps-per-eval",
        "50",
        "--val-batches",
        "5",
        "--max-seq-length",
        "1280",  # Fit maximum character limit securely
        "--grad-checkpoint",  # Use gradient checkpointing to save VRAM
        "--save-every",
        "100",
        "--seed",
        "42",
    ]

    logging.getLogger(__name__).info(f"🧠 MLX LoRA Training — {model}")
    logging.getLogger(__name__).info(f"   Iterations: {iters} | Batch: 1 (Acc: 2) | Layers: {lora_layers}")
    logging.getLogger(__name__).info(f"   Learning Rate: {learning_rate} | Optimizer: adamw")
    logging.getLogger(__name__).info("   Max Seq Length: 1280 | Mask Prompt: True | Grad Checkpoint: True")
    logging.getLogger(__name__).info(f"   Output: {adapter_path}")
    logging.getLogger(__name__).info("")

    result = subprocess.run(cmd, text=True)
    return result.returncode


def cmd_register() -> int:
    """Register MOSKV-1 model in Ollama."""
    from babylon60.extensions.training.moskv1_core import MOSKV1Core

    core = MOSKV1Core()
    modelfile = core.get_modelfile()

    modelfile_path = Path.home() / ".babylon60" / "training" / "adapters" / "Modelfile"
    modelfile_path.parent.mkdir(parents=True, exist_ok=True)
    modelfile_path.write_text(modelfile, encoding="utf-8")

    logging.getLogger(__name__).info(f"📄 Modelfile written to: {modelfile_path}")
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info("To register in Ollama, run:")
    logging.getLogger(__name__).info(f"  ollama create moskv1-core -f {modelfile_path}")
    return 0


def cmd_validate() -> int:
    """Validate dataset quality with detailed diagnostics."""
    dataset_dir = Path.home() / ".babylon60" / "training" / "datasets"
    dataset_path = dataset_dir / "moskv1_dataset.jsonl"
    if not dataset_path.exists():
        logging.getLogger(__name__).info("❌ No compiled dataset found. Run 'compile' first.")
        return 1

    entries: list[dict] = []
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))

    # ─── Quality Metrics ───────────────────────────────────────────
    output_lengths: list[int] = []
    instruction_lengths: list[int] = []
    has_code = 0
    has_yaml = 0
    has_structure = 0
    html_in_instruction = 0
    anergy_detected = 0

    anergy_words = [
        "hola",
        "buenos días",
        "espero que",
        "por supuesto",
        "aquí tienes",
        "here you go",
        "of course",
        "hope this helps",
    ]

    categories: Counter[str] = Counter()

    for e in entries:
        conversations = e.get("messages") or e.get("conversations") or []
        if len(conversations) < 3:
            continue

        instruction = conversations[1].get("content", "")
        output = conversations[-1].get("content", "")

        output_lengths.append(len(output))
        instruction_lengths.append(len(instruction))

        if "```" in output:
            has_code += 1
        if "yaml" in output.lower() or ": " in output:
            has_yaml += 1
        if "\n- " in output or "\n| " in output or "\n## " in output:
            has_structure += 1
        if "<!--" in instruction:
            html_in_instruction += 1

        for word in anergy_words:
            if word in output.lower():
                anergy_detected += 1
                break

        # Categorize by instruction pattern
        inst_lower = instruction.lower()
        if "clase" in inst_lower:
            categories["code_class"] += 1
        elif "módulo" in inst_lower or "module" in inst_lower:
            categories["code_module"] += 1
        elif "skill" in inst_lower:
            categories["skill"] += 1
        elif "directiva" in inst_lower:
            categories["directive"] += 1
        elif "memory vault" in inst_lower or "vault" in inst_lower:
            categories["memory_vault"] += 1
        elif "workflow" in inst_lower:
            categories["workflow"] += 1
        elif "ledger" in inst_lower or "hecho" in inst_lower:
            categories["ledger"] += 1
        else:
            categories["session/other"] += 1

    n = len(entries)
    avg_out = sum(output_lengths) / n if n else 0
    avg_inst = sum(instruction_lengths) / n if n else 0

    total_length = len(output_lengths)
    length_buckets = {
        "short": sum(1 for x in output_lengths if x < 250),
        "medium": sum(1 for x in output_lengths if 250 <= x < 1000),
        "long": sum(1 for x in output_lengths if x >= 1000),
    }

    from babylon60.extensions.security.utils import calculate_distribution_entropy

    len_entropy = (
        calculate_distribution_entropy(length_buckets, total_length) if total_length > 0 else 0.0
    )

    # ─── Report ────────────────────────────────────────────────────
    logging.getLogger(__name__).info("═══ MOSKV-1 DATASET VALIDATION v2.0 ═══")
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info(f"📊 Total entries: {n}")
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info("── Length Distribution ──")
    logging.getLogger(__name__).info(f"  Avg output length:       {avg_out:.0f} chars")
    logging.getLogger(__name__).info(f"  Avg instruction length:  {avg_inst:.0f} chars")
    logging.getLogger(__name__).info(f"  Min output:              {min(output_lengths) if output_lengths else 0} chars")
    logging.getLogger(__name__).info(f"  Max output:              {max(output_lengths) if output_lengths else 0} chars")
    logging.getLogger(__name__).info(f"  Length entropy:          {len_entropy:.2f} bits")
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info("── Content Quality ──")
    logging.getLogger(__name__).info(f"  Has code blocks:         {has_code} ({has_code / n * 100:.1f}%)")
    logging.getLogger(__name__).info(f"  Has YAML/structured:     {has_yaml} ({has_yaml / n * 100:.1f}%)")
    logging.getLogger(__name__).info(f"  Has lists/tables:        {has_structure} ({has_structure / n * 100:.1f}%)")
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info("── Defects ──")
    logging.getLogger(__name__).info(
        f"  HTML in instructions:    {html_in_instruction} {'✅' if html_in_instruction == 0 else '❌'}"
    )
    logging.getLogger(__name__).info(f"  Anergy detected:         {anergy_detected} {'✅' if anergy_detected == 0 else '⚠️'}")
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info("── Category Distribution ──")
    for cat, count in categories.most_common():
        bar = "█" * (count * 40 // n)
        logging.getLogger(__name__).info(f"  {cat:20s} {count:5d} ({count / n * 100:5.1f}%) {bar}")

    # ─── Split Validation ──────────────────────────────────────────
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info("── Train/Val/Test Split ──")
    for name in ["train", "valid", "test"]:
        path = dataset_dir / f"{name}.jsonl"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                count = sum(1 for _ in f)
            logging.getLogger(__name__).info(f"  {name:8s} {count:5d} entries  ({path.stat().st_size / 1024:.1f} KB)")
        else:
            logging.getLogger(__name__).info(f"  {name:8s} NOT FOUND ❌")

    # ─── Overall Score ─────────────────────────────────────────────
    score = 0
    if html_in_instruction == 0:
        score += 200
    if anergy_detected < n * 0.01:
        score += 200
    score += min(int(has_code / n * 300), 200)  # Code density
    score += min(int(len_entropy * 50), 200)  # Length diversity
    score += min(int(len(categories) * 30), 200)  # Category diversity

    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info(f"🎯 DATASET EXERGY SCORE: {score}/1000")
    if score >= 800:
        logging.getLogger(__name__).info("   ✅ Dataset is production-ready for LoRA training")
    elif score >= 500:
        logging.getLogger(__name__).info("   ⚠️ Dataset is acceptable but could be improved")
    else:
        logging.getLogger(__name__).info("   ❌ Dataset quality is insufficient — review filter settings")

    # ─── Weights Verification ───
    adapter_path = Path.home() / ".babylon60" / "training" / "adapters"
    if (adapter_path / "adapters.safetensors").exists() or (adapter_path / "weights.npz").exists():
        logging.getLogger(__name__).info("")
        logging.getLogger(__name__).info("═══ LoRA WEIGHTS VERIFICATION (C5-REAL) ═══")
        from babylon60.extensions.training.verifier import AdapterVerifier

        verifier = AdapterVerifier()
        base_model = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
        verdict = verifier.verify_adapter(adapter_path, base_model)

        if verdict["success"]:
            metrics = verdict["metrics"]
            logging.getLogger(__name__).info("   Status:        ✅ PASSED")
            logging.getLogger(__name__).info(f"   Total Tensors: {metrics['tensor_count']}")
            logging.getLogger(__name__).info(f"   Parameters:    {metrics['total_params']:,}")
            logging.getLogger(__name__).info("   Layers Check:  All weights finite, zero NaNs/infs.")
        else:
            logging.getLogger(__name__).info("   Status:        ❌ FAILED")
            logging.getLogger(__name__).info(f"   Error:         {verdict['error']}")
    else:
        logging.getLogger(__name__).info("")
        logging.getLogger(__name__).info("💡 Tip: No adapter weights found in adapters/. Run 'train' to generate weights.")
    return 0


def cmd_stats() -> int:
    """Show stats of the last compiled dataset."""
    dataset_path = Path.home() / ".babylon60" / "training" / "datasets" / "moskv1_dataset.jsonl"
    if not dataset_path.exists():
        logging.getLogger(__name__).info("❌ No compiled dataset found.")
        return 1

    entries = []
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))

    total_tokens = (
        sum(
            sum(
                len(m.get("content", ""))
                for m in (e.get("messages") or e.get("conversations") or [])
            )
            for e in entries
        )
        // 4
    )

    logging.getLogger(__name__).info(f"📊 Dataset: {dataset_path}")
    logging.getLogger(__name__).info(f"   Entries: {len(entries)}")
    logging.getLogger(__name__).info(f"   Estimated tokens: {total_tokens:,}")
    logging.getLogger(__name__).info(f"   File size: {dataset_path.stat().st_size / 1024:.1f} KB")

    # Show split info
    dataset_dir = dataset_path.parent
    for name in ["train", "valid", "test"]:
        path = dataset_dir / f"{name}.jsonl"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                count = sum(1 for _ in f)
            logging.getLogger(__name__).info(f"   {name}: {count} entries")
    return 0


def cmd_health() -> int:
    """Check Ollama health and model availability."""
    from babylon60.extensions.training.moskv1_core import MOSKV1Core

    core = MOSKV1Core()
    result = asyncio.run(core.check_ollama_health())

    logging.getLogger(__name__).info("═══ MOSKV-1 HEALTH CHECK ═══")
    logging.getLogger(__name__).info("")
    logging.getLogger(__name__).info(f"Ollama reachable:    {'✅' if result['ollama_reachable'] else '❌'}")
    logging.getLogger(__name__).info(f"MOSKV-1 available:   {'✅' if result['moskv1_available'] else '❌'}")
    logging.getLogger(__name__).info(f"Fallback available:  {'✅' if result['fallback_available'] else '❌'}")
    logging.getLogger(__name__).info("")
    if result["models"]:
        logging.getLogger(__name__).info("Available models:")
        for m in result["models"]:
            marker = " ◀ MOSKV-1" if "moskv1" in m else ""
            logging.getLogger(__name__).info(f"  - {m}{marker}")
    else:
        logging.getLogger(__name__).info("No models available (Ollama may not be running)")
    return 0


def cmd_daemon(interval: int) -> int:
    """Launch the nocturnal daemon process."""
    import os
    import subprocess

    logging.getLogger(__name__).info("🌙 Launching MOSKV-1 Autonomous Training Daemon...")
    script_path = Path(__file__).parent / "run_daemon.py"
    env = os.environ.copy()
    try:
        result = subprocess.run([sys.executable, str(script_path)], env=env)
        return result.returncode
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("🛑 Daemon stopped.")
        return 0


def main() -> None:
    """CLI entry point with argparse support."""
    parser = argparse.ArgumentParser(
        description="MOSKV-1 Cognitive Kernel — CLI v2.0. Author: borjamoskv",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # compile
    compile_parser = subparsers.add_parser(
        "compile", help="Compile CORTEX knowledge into training dataset"
    )
    compile_parser.add_argument("--workspace", help="Path to workspace directory")

    # train
    train_parser = subparsers.add_parser("train", help="Run MLX LoRA fine-tuning")
    train_parser.add_argument(
        "--model",
        default="mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        help="Base model path or name",
    )
    train_parser.add_argument("--iters", type=int, default=50, help="Number of training iterations")
    train_parser.add_argument("--batch-size", type=int, default=2, help="Effective batch size")
    train_parser.add_argument("--lora-layers", type=int, default=16, help="Number of LoRA layers")
    train_parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")

    # register
    subparsers.add_parser("register", help="Generate Ollama Modelfile")

    # validate
    subparsers.add_parser("validate", help="Validate dataset quality with diagnostics")

    # stats
    subparsers.add_parser("stats", help="Show dataset statistics")

    # health
    subparsers.add_parser("health", help="Check Ollama availability")

    # daemon
    daemon_parser = subparsers.add_parser(
        "daemon", help="Run the autonomous nocturnal training daemon loop"
    )
    daemon_parser.add_argument(
        "--interval", type=int, default=3600, help="Scan interval in seconds"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    code = 0
    if args.command == "compile":
        code = cmd_compile(args.workspace)
    elif args.command == "train":
        code = cmd_train(
            model=args.model,
            iters=args.iters,
            batch_size=args.batch_size,
            lora_layers=args.lora_layers,
            learning_rate=args.learning_rate,
        )
    elif args.command == "register":
        code = cmd_register()
    elif args.command == "validate":
        code = cmd_validate()
    elif args.command == "stats":
        code = cmd_stats()
    elif args.command == "health":
        code = cmd_health()
    elif args.command == "daemon":
        code = cmd_daemon(interval=args.interval)
    else:
        logging.getLogger(__name__).info(f"❌ Unknown command: {args.command}")
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()
