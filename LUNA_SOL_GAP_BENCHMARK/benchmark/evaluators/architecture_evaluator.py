# Architecture Evaluator for LUNA_SOL_GAP_BENCHMARK
import re
from typing import Any, Dict
from benchmark.evaluators.base_evaluator import BaseEvaluator, EvaluationResult


class ArchitectureEvaluator(BaseEvaluator):
    def evaluate(self, candidate_solution: str, task: Dict[str, Any]) -> EvaluationResult:
        gt = task.get("ground_truth", {})
        required_components = gt.get("required_components", [])
        failure_modes = gt.get("failure_modes", [])

        text_lower = candidate_solution.lower().replace("-", "_").replace(" ", "_")

        matched_components = []
        missing_components = []

        for comp in required_components:
            comp_norm = comp.lower().replace("-", "_").replace(" ", "_")
            # Also search fuzzy keyword tokens if comp is multi-word
            comp_tokens = comp_norm.split("_")
            if comp_norm in text_lower or all(tok in text_lower for tok in comp_tokens):
                matched_components.append(comp)
            else:
                missing_components.append(comp)

        matched_failures = []
        missing_failures = []

        for fm in failure_modes:
            fm_norm = fm.lower().replace("-", "_").replace(" ", "_")
            fm_tokens = fm_norm.split("_")
            if fm_norm in text_lower or all(tok in text_lower for tok in fm_tokens):
                matched_failures.append(fm)
            else:
                missing_failures.append(fm)

        total_criteria = len(required_components) + len(failure_modes)
        matched_total = len(matched_components) + len(matched_failures)

        score = round(matched_total / total_criteria, 2) if total_criteria > 0 else 1.0
        passed = score >= 0.85

        feedback_parts = [
            f"Component coverage: {len(matched_components)}/{len(required_components)}",
            f"Failure mode coverage: {len(matched_failures)}/{len(failure_modes)}"
        ]
        if missing_components:
            feedback_parts.append(f"Missing components: {missing_components}")
        if missing_failures:
            feedback_parts.append(f"Missing failure modes: {missing_failures}")

        failure_set = [f"MissingComp:{c}" for c in missing_components] + [f"MissingFM:{f}" for f in missing_failures]

        return EvaluationResult(
            passed=passed,
            score=score,
            feedback=" | ".join(feedback_parts),
            failure_set=failure_set,
            details={
                "matched_components": matched_components,
                "missing_components": missing_components,
                "matched_failures": matched_failures,
                "missing_failures": missing_failures
            }
        )
