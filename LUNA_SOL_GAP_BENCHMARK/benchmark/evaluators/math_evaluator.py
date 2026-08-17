# Mathematics Evaluator for LUNA_SOL_GAP_BENCHMARK
import math
import re
from typing import Any, Dict
from benchmark.evaluators.base_evaluator import BaseEvaluator, EvaluationResult


class MathEvaluator(BaseEvaluator):
    def _extract_numbers_and_exprs(self, text: str) -> list[float]:
        # Extract explicit numbers or simple fractions
        numbers = []
        # Find explicit patterns like 91, 1.75, 7/4, 265, etc.
        frac_matches = re.findall(r"\b(\d+)/(\d+)\b", text)
        for num, denom in frac_matches:
            if float(denom) != 0:
                numbers.append(float(num) / float(denom))

        num_matches = re.findall(r"[-+]?\d*\.\d+|\b[-+]?\d+\b", text)
        for n in num_matches:
            try:
                numbers.append(float(n))
            except ValueError:
                pass
        return numbers

    def evaluate(self, candidate_solution: str, task: Dict[str, Any]) -> EvaluationResult:
        gt = task.get("ground_truth", {})
        target_val = gt.get("value")
        eval_points = gt.get("eval_points")
        target_expr = gt.get("expression")

        extracted_nums = self._extract_numbers_and_exprs(candidate_solution)

        if target_val is not None:
            # Check if target numeric value is in the extracted candidate solution
            for num in extracted_nums:
                if math.isclose(num, float(target_val), rel_tol=1e-3, abs_tol=1e-3):
                    return EvaluationResult(
                        passed=True,
                        score=1.0,
                        feedback=f"Target value {target_val} correctly computed.",
                        failure_set=[],
                        details={"target_value": target_val, "matched_num": num}
                    )

            return EvaluationResult(
                passed=False,
                score=0.0,
                feedback=f"Target value {target_val} not found in solution numbers {extracted_nums[-5:]}.",
                failure_set=["NumericMismatch"],
                details={"target_value": target_val, "extracted_nums": extracted_nums}
            )

        if eval_points is not None:
            # Recurrence point verification (e.g. 2^n + 3^n)
            matches = 0
            total = len(eval_points)
            for n_val, expected_res in eval_points.items():
                pattern = rf"\b{expected_res}\b"
                if re.search(pattern, candidate_solution) or any(math.isclose(num, float(expected_res)) for num in extracted_nums):
                    matches += 1

            if matches == total or target_expr.lower() in candidate_solution.lower().replace(" ", ""):
                return EvaluationResult(
                    passed=True,
                    score=1.0,
                    feedback=f"All {total} evaluation points matched expected recurrence values.",
                    failure_set=[],
                    details={"matched": matches, "total": total}
                )
            else:
                score = round(matches / total, 2)
                return EvaluationResult(
                    passed=score >= 0.8,
                    score=score,
                    feedback=f"Matched {matches}/{total} recurrence evaluation points.",
                    failure_set=["RecurrenceMismatch"] if score < 0.8 else [],
                    details={"matched": matches, "total": total}
                )

        return EvaluationResult(
            passed=False,
            score=0.0,
            feedback="Ground truth definition invalid for math evaluator.",
            failure_set=["InvalidGroundTruth"],
            details={}
        )
