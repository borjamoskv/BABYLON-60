#!/usr/bin/env python3
# CLI Runner for LUNA_SOL_GAP_BENCHMARK v1 (Falsification Edition)
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
from benchmark.ctm import CTMPolicyEngine
from benchmark.runners.mock_runner import MockRunner
from benchmark.runners.llm_runner import LLMRunner
from benchmark.metrics import MetricsCalculator, TaskResult

def load_yaml(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="CTM-FALSIFICATION v1 CLI Runner")
    parser.add_argument("--config", default=str(BASE_DIR / "configs" / "experiment.yaml"), help="Path to config file")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock deterministic runner (default: True)")
    parser.add_argument("--live", action="store_true", help="Use live LLM API runner")
    parser.add_argument("--output-dir", default=str(BASE_DIR / "results"), help="Directory for JSON results")
    args = parser.parse_args()

    use_mock = not args.live

    print("=" * 70)
    print(" CTM-FALSIFICATION v1 Execution Engine")
    print(f" Mode: {'MOCK (Deterministic Test)' if use_mock else 'LIVE LLM API'}")
    print("=" * 70)

    # Load configuration & corpus
    config = load_yaml(args.config)
    task_corpus = load_yaml(str(BASE_DIR / "benchmark" / "tasks" / "task_corpus.yaml"))
    tasks = task_corpus.get("tasks", [])

    print(f"Loaded {len(tasks)} tasks across domains.")

    # Initialize evaluator
    evaluators = {
        "coding": CodingEvaluator(),
        "math": MathEvaluator(),
        "mathematics": MathEvaluator(),
        "logic": LogicEvaluator(),
        "architecture": ArchitectureEvaluator()
    }
    
    # We use a single constant model for falsification
    model_name = config.get("model", "gpt-5-luna")
    if use_mock:
        runner = MockRunner(branch="FALSIFICATION", model_name=model_name)
    else:
        runner = LLMRunner(model_name=model_name)

    max_iterations = config.get("budget_constraints", {}).get("max_iterations", 3)
    branches = ["BASE", "BASE-N", "CTM"]

    task_results = []

    for idx, task in enumerate(tasks, 1):
        task_id = task["id"]
        domain = task["domain"]
        evaluator = evaluators.get(domain, evaluators["logic"])

        print(f"[{idx}/{len(tasks)}] Running Task {task_id} ({domain.upper()}: '{task['title']}')...")

        if use_mock:
            runner.set_task(task)
            
        policy_engine = CTMPolicyEngine(runner=runner, checker=evaluator)
        
        branch_passed = {}
        branch_scores = {}
        branch_budget = {}

        # 1. BASE Policy
        res_base = policy_engine.run_base(task)
        branch_passed["BASE"] = res_base.passed
        branch_scores["BASE"] = res_base.final_score
        branch_budget["BASE"] = res_base.budget_consumed_tokens

        # 2. BASE-N Policy (Random Retry)
        res_basen = policy_engine.run_random_retry(task, max_iterations=max_iterations)
        branch_passed["BASE-N"] = res_basen.passed
        branch_scores["BASE-N"] = res_basen.final_score
        branch_budget["BASE-N"] = res_basen.budget_consumed_tokens

        # 3. CTM Policy (Guided Retry)
        res_ctm = policy_engine.run_ctm(task, max_iterations=max_iterations)
        branch_passed["CTM"] = res_ctm.passed
        branch_scores["CTM"] = res_ctm.final_score
        branch_budget["CTM"] = res_ctm.budget_consumed_tokens

        task_results.append(TaskResult(
            task_id=task_id,
            domain=domain,
            branch_passed=branch_passed,
            branch_scores=branch_scores,
            branch_budget=branch_budget
        ))

    # Calculate falsification metrics
    calc = MetricsCalculator()
    metrics = calc.calculate(task_results)

    # Output directory creation
    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, "falsification_results.json")

    # Save JSON results
    json_data = {
        "experiment_name": config["experiment_name"],
        "falsified": metrics.falsified,
        "falsification_reason": metrics.falsification_reason,
        "metrics": {
            "coverage": metrics.coverage,
            "recovery_rate": metrics.recovery,
            "regression_rate": metrics.regression,
            "g_strategy_gain": metrics.g_strategy,
            "total_budget_tokens": metrics.total_budget_consumed
        },
        "domain_breakdown": metrics.domain_breakdown
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    print("\n" + "=" * 70)
    print(" CTM FALSIFICATION BENCHMARK COMPLETE")
    print("=" * 70)
    print(f"Results JSON:  {json_path}")
    print(f"\nFALSIFICATION RESULT: {'FAILED' if metrics.falsified else 'SURVIVED'}")
    print(f"Reasoning: {metrics.falsification_reason}")
    print(f"Coverage BASE:   {metrics.coverage.get('BASE'):.2%}")
    print(f"Coverage BASE-N: {metrics.coverage.get('BASE-N'):.2%}")
    print(f"Coverage CTM:    {metrics.coverage.get('CTM'):.2%}")
    print(f"Regression Rate: {metrics.regression:.2%}")
    print("=" * 70)

if __name__ == "__main__":
    main()
