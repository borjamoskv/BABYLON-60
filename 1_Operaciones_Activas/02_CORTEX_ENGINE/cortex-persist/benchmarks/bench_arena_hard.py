# [C5-REAL] Exergy-Maximized
# Author: borjamoskv
# License: Apache-2.0
"""
Arena-Hard Local Evaluation Pipeline for BABYLON-60.

Orchestrates the full Arena-Hard-Auto v2.0 benchmark pipeline:
  Phase 1: Verify model endpoint is alive
  Phase 2: Generate answers (gen_answer.py)
  Phase 3: Judge answers (gen_judgment.py)
  Phase 4: Parse results, compute ELO, emit to Ledger

Usage:
    python benchmarks/bench_arena_hard.py --config benchmarks/arena_eval_config.yaml
    python benchmarks/bench_arena_hard.py --config benchmarks/arena_eval_config.yaml --dry-run
    python benchmarks/bench_arena_hard.py --config benchmarks/arena_eval_config.yaml --phase 4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("babylon60.benchmarks.arena_hard")

# ─── Constants ────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = ROOT_DIR / "benchmarks"
DEFAULT_CONFIG = BENCHMARKS_DIR / "arena_eval_config.yaml"


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate arena evaluation config."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    required_keys = ["target_model", "judge", "evaluation", "system_prompt"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        msg = f"Missing required config keys: {missing}"
        raise ValueError(msg)

    return config


def sha256_str(data: str) -> str:
    """Compute SHA-256 hex digest of a string."""
    return hashlib.sha256(data.encode()).hexdigest()


# ─── Phase 1: Verify Endpoint ────────────────────────────────────────
def phase_1_verify_endpoint(config: dict[str, Any]) -> bool:
    """Verify that the target model API endpoint is reachable."""
    import urllib.error
    import urllib.request

    api_base = config["target_model"]["api_base"].rstrip("/")
    models_url = f"{api_base}/models"

    logger.info("[Phase 1] Verifying endpoint: %s", models_url)

    try:
        req = urllib.request.Request(models_url, method="GET")
        api_key = config["target_model"].get("api_key", "not-needed")
        req.add_header("Authorization", f"Bearer {api_key}")

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("data", [])
            model_ids = [m.get("id", "unknown") for m in models]
            logger.info("[Phase 1] Endpoint alive. Models available: %s", model_ids)
            return True
    except urllib.error.URLError as e:
        logger.error("[Phase 1] Endpoint unreachable: %s", e)
        logger.error(
            "[Phase 1] Start your model server first:\n"
            "  ./benchmarks/serve_mlx.sh           # MLX\n"
            "  ollama serve && ollama run moskv-1   # Ollama"
        )
        return False


# ─── Phase 2: Generate Answers ───────────────────────────────────────
def phase_2_generate_answers(config: dict[str, Any], dry_run: bool = False) -> bool:
    """Generate model answers using arena-hard-auto gen_answer.py."""
    arena_path = ROOT_DIR / config.get("arena_hard_path", "benchmarks/arena-hard")
    gen_answer = arena_path / "gen_answer.py"

    if not gen_answer.exists():
        logger.error("[Phase 2] gen_answer.py not found at: %s", gen_answer)
        return False

    # Build the arena-hard config for our model
    model_name = config["target_model"]["name"]
    api_base = config["target_model"]["api_base"]
    model_id = config["target_model"].get("model_id", model_name)
    api_key = config["target_model"].get("api_key", "not-needed")
    max_tokens = config["target_model"].get("max_tokens", 4096)
    temperature = config["target_model"].get("temperature", 0.7)
    system_prompt = config.get("system_prompt", "").strip()

    # Write temporary API config for arena-hard-auto
    api_config = {
        model_name: {
            "model_name": model_id,
            "endpoints": [
                {
                    "api_base": api_base,
                    "api_key": api_key,
                }
            ],
            "api_type": "openai",
            "parallel": config["evaluation"].get("max_parallel_requests", 4),
        }
    }

    api_config_path = arena_path / "config" / "api_config_babylon60.yaml"
    api_config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(api_config_path, "w") as f:
        yaml.dump(api_config, f, default_flow_style=False)

    logger.info("[Phase 2] API config written: %s", api_config_path)
    logger.info("[Phase 2] Model: %s (id: %s)", model_name, model_id)
    logger.info("[Phase 2] System prompt hash: %s", sha256_str(system_prompt)[:16])

    if dry_run:
        logger.info("[Phase 2] DRY RUN — skipping answer generation")
        return True

    # Build gen_answer command
    cmd = [
        sys.executable,
        str(gen_answer),
        "--config",
        str(api_config_path),
        "--model",
        model_name,
        "--max-tokens",
        str(max_tokens),
        "--temperature",
        str(temperature),
    ]

    # Inject system prompt if supported
    if system_prompt:
        # Write system prompt to temp file for injection
        prompt_file = arena_path / "config" / "system_prompt_babylon60.txt"
        with open(prompt_file, "w") as f:
            f.write(system_prompt)
        logger.info("[Phase 2] System prompt written: %s", prompt_file)

    # Limit prompts if configured
    max_prompts = config["evaluation"].get("max_prompts")
    if max_prompts:
        cmd.extend(["--num-prompts", str(max_prompts)])

    logger.info("[Phase 2] Running: %s", " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=str(arena_path),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("[Phase 2] gen_answer failed:\n%s", result.stderr)
        return False

    logger.info("[Phase 2] Answer generation complete")
    if result.stdout:
        logger.info("[Phase 2] Output:\n%s", result.stdout[-500:])

    return True


# ─── Phase 3: Judge Answers ──────────────────────────────────────────
def phase_3_judge_answers(config: dict[str, Any], dry_run: bool = False) -> bool:
    """Run LLM-as-a-Judge evaluation via gen_judgment.py."""
    arena_path = ROOT_DIR / config.get("arena_hard_path", "benchmarks/arena-hard")
    gen_judgment = arena_path / "gen_judgment.py"

    if not gen_judgment.exists():
        logger.error("[Phase 3] gen_judgment.py not found at: %s", gen_judgment)
        return False

    judge_config = config["judge"]
    judge_model = judge_config["model_id"]
    api_key_env = judge_config.get("api_key_env", "GEMINI_API_KEY")

    if not os.environ.get(api_key_env):
        logger.error("[Phase 3] Judge API key not set. Export %s first.", api_key_env)
        return False

    model_name = config["target_model"]["name"]

    if dry_run:
        logger.info("[Phase 3] DRY RUN — skipping judgment (judge: %s)", judge_model)
        return True

    cmd = [
        sys.executable,
        str(gen_judgment),
        "--model",
        model_name,
        "--judge-model",
        judge_model,
    ]

    # Style control
    if config["evaluation"].get("style_control"):
        features = config["evaluation"].get("style_features", [])
        if features:
            cmd.extend(["--control-features"] + features)

    logger.info("[Phase 3] Running judgment: %s", " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=str(arena_path),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("[Phase 3] gen_judgment failed:\n%s", result.stderr)
        return False

    logger.info("[Phase 3] Judgment complete")
    return True


# ─── Phase 4: Results & Ledger ───────────────────────────────────────
def phase_4_results(config: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    """Parse results, compute ELO, emit to Ledger."""
    arena_path = ROOT_DIR / config.get("arena_hard_path", "benchmarks/arena-hard")
    show_result = arena_path / "show_result.py"

    model_name = config["target_model"]["name"]
    judge_model = config["judge"]["model_id"]
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    results_payload = {
        "model": model_name,
        "judge": judge_model,
        "arena_version": config.get("arena_hard_version", "v2.0"),
        "system_prompt_hash": sha256_str(config.get("system_prompt", "")),
        "timestamp": timestamp,
        "win_rate": None,
        "elo_estimate": None,
        "categories": {},
    }

    if dry_run:
        logger.info("[Phase 4] DRY RUN — generating mock results")
        results_payload["win_rate"] = 0.0
        results_payload["elo_estimate"] = 0
        _emit_results_report(results_payload, config)
        return results_payload

    if show_result.exists():
        cmd = [
            sys.executable,
            str(show_result),
            "--judge-names",
            judge_model,
        ]

        style_features = config["evaluation"].get("style_features", [])
        if style_features:
            cmd.extend(["--control-features"] + style_features)

        logger.info("[Phase 4] Running: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            cwd=str(arena_path),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and result.stdout:
            results_payload["raw_output"] = result.stdout
            win_rate = _parse_win_rate(result.stdout, model_name)
            results_payload["win_rate"] = win_rate
            results_payload["elo_estimate"] = _estimate_elo(win_rate)
            logger.info(
                "[Phase 4] Win Rate: %.1f%% | ELO Estimate: %d",
                win_rate * 100,
                results_payload["elo_estimate"],
            )
        else:
            logger.warning("[Phase 4] show_result failed or empty output")
            if result.stderr:
                logger.warning("[Phase 4] stderr: %s", result.stderr[-300:])

    # Emit results
    _emit_results_report(results_payload, config)

    # Ledger integration
    if config.get("ledger", {}).get("enabled", False):
        _emit_to_ledger(results_payload, config)

    return results_payload


def _parse_win_rate(output: str, model_name: str) -> float:
    """Extract win rate from show_result.py output."""
    for line in output.splitlines():
        if model_name in line:
            parts = line.split()
            for _i, part in enumerate(parts):
                try:
                    val = float(part.strip("%"))
                    if 0 <= val <= 100:
                        return val / 100.0
                except ValueError:
                    continue
    logger.warning("Could not parse win rate for %s from output", model_name)
    return 0.0


def _estimate_elo(win_rate: float, baseline_elo: int = 1200) -> int:
    """Estimate ELO from win rate against baseline (GPT-4.1 ~ 1200 in Arena-Hard)."""
    import math

    if win_rate <= 0.0:
        return baseline_elo - 400
    if win_rate >= 1.0:
        return baseline_elo + 400

    # ELO formula: E_a = 1 / (1 + 10^((R_b - R_a)/400))
    # Solving for R_a: R_a = R_b - 400 * log10(1/E_a - 1)
    elo_diff = -400 * math.log10(1.0 / win_rate - 1.0)
    return int(baseline_elo + elo_diff)


def _emit_results_report(results: dict[str, Any], config: dict[str, Any]) -> None:
    """Write results to markdown report."""
    output_dir = ROOT_DIR / config["evaluation"].get("output_dir", "benchmarks/arena-hard-results")
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"arena_eval_{ts}.md"

    win_rate = results.get("win_rate", 0) or 0
    elo = results.get("elo_estimate", 0) or 0

    report = f"""# Arena-Hard Evaluation Report
# [C5-REAL] Generated by BABYLON-60
# Author: borjamoskv

| Field | Value |
|:---|:---|
| **Model** | {results["model"]} |
| **Judge** | {results["judge"]} |
| **Arena Version** | {results["arena_version"]} |
| **Win Rate** | {win_rate:.1%} |
| **ELO Estimate** | {elo} |
| **System Prompt Hash** | `{results["system_prompt_hash"][:16]}...` |
| **Timestamp** | {results["timestamp"]} |
| **Results Hash** | `{sha256_str(json.dumps(results, default=str))[:16]}...` |
"""

    if "raw_output" in results:
        report += f"\n## Raw Output\n\n```\n{results['raw_output']}\n```\n"

    with open(report_path, "w") as f:
        f.write(report)

    logger.info("[Phase 4] Report written: %s", report_path)


def _emit_to_ledger(results: dict[str, Any], config: dict[str, Any]) -> None:
    """Emit evaluation results to BABYLON-60 Ledger."""
    try:
        from babylon60.audit.ledger import MasterLedger

        event = {
            "type": config.get("ledger", {}).get("event_type", "ARENA_EVAL_COMPLETED"),
            "model": results["model"],
            "arena_version": results["arena_version"],
            "judge": results["judge"],
            "win_rate": results.get("win_rate"),
            "elo_estimate": results.get("elo_estimate"),
            "system_prompt_hash": results["system_prompt_hash"],
            "results_hash": sha256_str(json.dumps(results, default=str)),
            "timestamp": results["timestamp"],
        }

        ledger = MasterLedger()
        ledger.append(event)
        logger.info("[Ledger] Event emitted: %s", event["type"])
    except ImportError:
        logger.warning("[Ledger] babylon60.audit.ledger not available — skipping")
    except Exception as e:  # noqa: BLE001
        logger.warning("[Ledger] Failed to emit: %s", e)


# ─── Main ────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Arena-Hard Local Evaluation Pipeline for BABYLON-60"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to arena evaluation config YAML",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and pipeline without generating/judging",
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run only a specific phase (1-4)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("=" * 60)
    logger.info("ARENA-HARD LOCAL EVALUATION — BABYLON-60")
    logger.info("=" * 60)

    config = load_config(args.config)
    logger.info("Config loaded: %s", args.config)
    logger.info("Target model: %s", config["target_model"]["name"])
    logger.info("Judge: %s", config["judge"]["model_id"])

    if args.dry_run:
        logger.info("MODE: DRY RUN")

    phases = [args.phase] if args.phase else [1, 2, 3, 4]
    t0 = time.monotonic()

    for phase in phases:
        logger.info("-" * 40)

        if phase == 1:
            if not phase_1_verify_endpoint(config):
                if not args.dry_run:
                    logger.error("Phase 1 FAILED — endpoint not reachable. Aborting.")
                    sys.exit(1)
                logger.warning("Phase 1 FAILED (dry-run, continuing)")

        elif phase == 2:
            if not phase_2_generate_answers(config, dry_run=args.dry_run):
                logger.error("Phase 2 FAILED — answer generation failed. Aborting.")
                sys.exit(1)

        elif phase == 3:
            if not phase_3_judge_answers(config, dry_run=args.dry_run):
                logger.error("Phase 3 FAILED — judgment failed. Aborting.")
                sys.exit(1)

        elif phase == 4:
            results = phase_4_results(config, dry_run=args.dry_run)
            if results.get("win_rate") is not None:
                logger.info(
                    "FINAL: Win Rate=%.1f%% ELO=%d",
                    (results["win_rate"] or 0) * 100,
                    results.get("elo_estimate", 0) or 0,
                )

    elapsed = time.monotonic() - t0
    logger.info("=" * 60)
    logger.info("Pipeline complete in %.1fs", elapsed)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
