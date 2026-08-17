#!/usr/bin/env python3
# CLI Runner for LUNA_SOL_GAP_BENCHMARK v0.1
import argparse
import json
import os
import sys
import yaml
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from benchmark.evaluators.coding_evaluator import CodingEvaluator
from benchmark.evaluators.math_evaluator import MathEvaluator
from benchmark.evaluators.logic_evaluator import LogicEvaluator
from benchmark.evaluators.architecture_evaluator import ArchitectureEvaluator
from benchmark.ctm import CTM
from benchmark.runners.mock_runner import MockRunner
from benchmark.runners.llm_runner import LLMRunner
from benchmark.metrics import MetricsCalculator, TaskResult
from benchmark.statistics import StatisticsEngine


def load_yaml(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="LUNA_SOL_GAP_BENCHMARK v0.1 CLI Runner")
    parser.add_argument("--config", default=str(BASE_DIR / "configs" / "experiment.yaml"), help="Path to config file")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock deterministic runner (default: True)")
    parser.add_argument("--live", action="store_true", help="Use live LLM API runner")
    parser.add_argument("--output-dir", default=str(BASE_DIR / "results"), help="Directory for JSON results")
    parser.add_argument("--report-dir", default=str(BASE_DIR / "reports"), help="Directory for Markdown report")
    args = parser.parse_args()

    use_mock = not args.live

    print("=" * 70)
    print(" LUNA_SOL_GAP_BENCHMARK v0.1 Execution Engine")
    print(f" Mode: {'MOCK (Deterministic Test)' if use_mock else 'LIVE LLM API'}")
    print("=" * 70)

    # Load configuration & corpus
    config = load_yaml(args.config)
    task_corpus = load_yaml(str(BASE_DIR / "benchmark" / "tasks" / "task_corpus.yaml"))
    tasks = task_corpus.get("tasks", [])

    print(f"Loaded {len(tasks)} tasks across domains.")

    # Initialize evaluators
    evaluators = {
        "coding": CodingEvaluator(),
        "math": MathEvaluator(),
        "mathematics": MathEvaluator(),
        "logic": LogicEvaluator(),
        "architecture": ArchitectureEvaluator()
    }

    # Setup runners
    branches = ["A", "B", "C", "D", "E"]
    runners = {}

    for b in branches:
        b_conf = config["branches"][b]
        model_key = b_conf["model"]
        model_name = config["models"].get(model_key, model_key)
        if use_mock:
            runners[b] = MockRunner(branch=b, model_name=model_name)
        else:
            runners[b] = LLMRunner(model_name=model_name)

    ctm_settings = config.get("ctm_settings", {})
    max_iterations = ctm_settings.get("max_iterations", 3)

    task_results = []

    for idx, task in enumerate(tasks, 1):
        task_id = task["id"]
        domain = task["domain"]
        evaluator = evaluators.get(domain, evaluators["coding"])

        print(f"[{idx}/{len(tasks)}] Running Task {task_id} ({domain.upper()}: '{task['title']}')...")

        branch_scores = {}
        branch_tokens = {}

        # Branch A: Luna Single Pass
        if use_mock:
            runners["A"].set_task(task)
        out_a, tok_a = runners["A"].generate(task["prompt"], use_think=False)
        res_a = evaluator.evaluate(out_a, task)
        branch_scores["A"] = res_a.score
        branch_tokens["A"] = tok_a

        # Branch B: Luna Think
        if use_mock:
            runners["B"].set_task(task)
        out_b, tok_b = runners["B"].generate(task["prompt"], use_think=True)
        res_b = evaluator.evaluate(out_b, task)
        branch_scores["B"] = res_b.score
        branch_tokens["B"] = tok_b

        # Branch C: Luna CTM (Think + CTM)
        if use_mock:
            runners["C"].set_task(task)
        ctm_c = CTM(
            runner=runners["C"],
            evaluator=evaluator,
            max_iterations=max_iterations,
            epsilon_semantic_delta=ctm_settings.get("epsilon_semantic_delta", 0.05),
            epsilon_score_delta=ctm_settings.get("epsilon_score_delta", 0.01)
        )
        c_res = ctm_c.run(task, use_think=True)
        branch_scores["C"] = c_res.final_score
        branch_tokens["C"] = c_res.tokens_used

        # Branch D: Sol Baseline
        if use_mock:
            runners["D"].set_task(task)
        out_d, tok_d = runners["D"].generate(task["prompt"], use_think=True)
        res_d = evaluator.evaluate(out_d, task)
        branch_scores["D"] = res_d.score
        branch_tokens["D"] = tok_d

        # Branch E: Luna CTM No Think (Standard + CTM)
        if use_mock:
            runners["E"].set_task(task)
        ctm_e = CTM(
            runner=runners["E"],
            evaluator=evaluator,
            max_iterations=max_iterations
        )
        e_res = ctm_e.run(task, use_think=False)
        branch_scores["E"] = e_res.final_score
        branch_tokens["E"] = e_res.tokens_used

        task_results.append(TaskResult(
            task_id=task_id,
            domain=domain,
            branch_scores=branch_scores,
            branch_tokens=branch_tokens,
            ctm_initial_passed=c_res.initial_passed,
            ctm_final_passed=c_res.passed,
            ctm_iterations=c_res.iterations,
            ctm_aborted_stagnation=c_res.aborted_stagnation
        ))

    # Calculate metrics & statistics
    calc = MetricsCalculator(epsilon_baseline_gap=config["metrics_settings"].get("epsilon_baseline_gap", 0.05))
    metrics = calc.calculate(task_results)
    stats = StatisticsEngine()

    md_report = stats.generate_markdown_report(metrics, experiment_name=config["experiment_name"])

    # Output directory creation
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.report_dir, exist_ok=True)

    json_path = os.path.join(args.output_dir, "results.json")
    report_path = os.path.join(args.report_dir, "summary.md")

    # Save JSON results
    json_data = {
        "experiment_name": config["experiment_name"],
        "mean_scores": metrics.mean_scores,
        "absolute_gain_g_ctm": metrics.absolute_gain_g_ctm,
        "gap_remaining": metrics.gap_remaining,
        "recovery_ratio_re": metrics.recovery_ratio_re,
        "recovery_ratio_status": metrics.recovery_ratio_status,
        "verification_value_vv": metrics.verification_value_vv,
        "domain_breakdown": metrics.domain_breakdown,
        "token_usage_totals": metrics.token_usage_totals
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print("\n" + "=" * 70)
    print(" BENCHMARK EXECUTION COMPLETE")
    print("=" * 70)
    print(f"Results JSON:  {json_path}")
    print(f"Report Summary:{report_path}\n")
    print(md_report)


if __name__ == "__main__":
    main()
