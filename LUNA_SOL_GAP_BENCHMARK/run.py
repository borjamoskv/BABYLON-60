#!/usr/bin/env python3
# CLI Runner for LUNA_SOL_GAP_BENCHMARK (CTM Falsification Final Matrix A-F)
import argparse
import json
import os
import sys
import yaml
from pathlib import Path

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
    parser = argparse.ArgumentParser(description="CTM-FALSIFICATION v4 CLI Runner")
    parser.add_argument("--config", default=str(BASE_DIR / "configs" / "experiment.yaml"), help="Path to config file")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock deterministic runner")
    parser.add_argument("--live", action="store_true", help="Use live LLM API runner")
    parser.add_argument("--output-dir", default=str(BASE_DIR / "results"), help="Directory for JSON results")
    args = parser.parse_args()

    use_mock = not args.live

    print("=" * 70)
    print(" CTM-FALSIFICATION (Final Pre-Live Matrix A-F)")
    print(f" Mode: {'MOCK (Deterministic Test)' if use_mock else 'LIVE LLM API'}")
    print("=" * 70)

    config = load_yaml(args.config)
    task_corpus = load_yaml(str(BASE_DIR / "benchmark" / "tasks" / "task_corpus.yaml"))
    tasks = task_corpus.get("tasks", [])

    print(f"Loaded {len(tasks)} tasks.")

    evaluators = {
        "coding": CodingEvaluator(),
        "math": MathEvaluator(),
        "mathematics": MathEvaluator(),
        "logic": LogicEvaluator(),
        "architecture": ArchitectureEvaluator()
    }
    
    model_name = config.get("model", "gpt-5-luna")
    if use_mock:
        runner = MockRunner(branch="FALSIFICATION", model_name=model_name)
    else:
        runner = LLMRunner(model_name=model_name)

    max_iterations = config.get("budget_constraints", {}).get("max_iterations", 3)
    branches = ["BASE", "EXTRA_COMPUTE", "NULL_ADAPTIVE_CONTROL", "STRUCTURED_CTM", "CTM_TOOL", "PERMUTED_CTM", "SOL_BASELINE"]

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

        for branch in branches:
            if branch == "SOL_BASELINE":
                # Mock SOL_BASELINE for capability score testing
                branch_passed[branch] = True if use_mock else False
                branch_scores[branch] = 1.0 if use_mock else 0.0
                branch_budget[branch] = 100
                continue
                
            res = policy_engine.run_branch(task, policy_name=branch, max_iterations=max_iterations)
            branch_passed[branch] = res.passed
            branch_scores[branch] = res.final_score
            branch_budget[branch] = res.budget_consumed_tokens

        task_results.append(TaskResult(
            task_id=task_id,
            domain=domain,
            branch_passed=branch_passed,
            branch_scores=branch_scores,
            branch_budget=branch_budget
        ))

    calc = MetricsCalculator(weak_oracles=["architecture"])
    metrics = calc.calculate(task_results)

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, "falsification_matrix_af.json")

    json_data = {
        "experiment_name": config["experiment_name"],
        "falsified": metrics.falsified,
        "falsification_reason": metrics.falsification_reason,
        "metrics": {
            "coverage": metrics.coverage,
            "efficiency": metrics.efficiency,
            "regression_rate": metrics.regression_rate,
            "observed_gap_closed": metrics.observed_gap_closed,
            "capability_relative_score_ce": metrics.capability_relative_score_ce,
            "total_budget_tokens": metrics.total_budget_consumed
        },
        "statistical_tests": {
            "h_ctm_vs_placebo": metrics.primary_hypothesis_ctm_vs_placebo,
            "h_ctm_vs_permuted": metrics.primary_hypothesis_ctm_vs_permuted
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    print("\n" + "=" * 70)
    print(" CTM FALSIFICATION BENCHMARK COMPLETE")
    print("=" * 70)
    print(f"Results JSON:  {json_path}")
    print(f"\nFALSIFICATION RESULT: {'FAILED' if metrics.falsified else 'SURVIVED'}")
    print(f"Reasoning: {metrics.falsification_reason}")
    print(f"Coverage BASE:                  {metrics.coverage.get('BASE'):.2%}")
    print(f"Coverage NULL_ADAPTIVE_CONTROL: {metrics.coverage.get('NULL_ADAPTIVE_CONTROL'):.2%}")
    print(f"Coverage PERMUTED_CTM:          {metrics.coverage.get('PERMUTED_CTM'):.2%}")
    print(f"Coverage STRUCTURED_CTM:        {metrics.coverage.get('STRUCTURED_CTM'):.2%}")
    print(f"Regression Rate:                {metrics.regression_rate:.2%}")
    print("=" * 70)

if __name__ == "__main__":
    main()
