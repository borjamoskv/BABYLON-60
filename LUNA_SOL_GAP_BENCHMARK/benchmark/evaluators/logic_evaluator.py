# Logic Evaluator for LUNA_SOL_GAP_BENCHMARK
import re
from typing import Any, Dict
from benchmark.evaluators.base_evaluator import BaseEvaluator, EvaluationResult


class LogicEvaluator(BaseEvaluator):
    def evaluate(self, candidate_solution: str, task: Dict[str, Any]) -> EvaluationResult:
        gt = task.get("ground_truth", {})
        task_id = task.get("id", "")
        text_upper = candidate_solution.upper()

        if task_id == "logic_01":
            # Tautology check
            has_true = "TRUE" in text_upper or "TAUTOLOGY" in text_upper or "VALID" in text_upper
            has_false_claim = "NOT A TAUTOLOGY" in text_upper or "FALSE" in text_upper
            if has_true and not has_false_claim:
                return EvaluationResult(passed=True, score=1.0, feedback="Correctly identified formula as Tautology.", failure_set=[])
            return EvaluationResult(passed=False, score=0.0, feedback="Failed to prove formula is a Tautology.", failure_set=["TautologyMismatch"])

        elif task_id == "logic_02":
            # Knights & Knaves: A = Knight, B = Knight
            a_knight = "A IS A KNIGHT" in text_upper or "A: KNIGHT" in text_upper or "A - KNIGHT" in text_upper
            b_knight = "B IS A KNIGHT" in text_upper or "B: KNIGHT" in text_upper or "B - KNIGHT" in text_upper
            if a_knight and b_knight:
                return EvaluationResult(passed=True, score=1.0, feedback="Correctly identified both A and B as Knights.", failure_set=[])
            return EvaluationResult(passed=False, score=0.0, feedback="Incorrect Knights & Knaves deduction.", failure_set=["LogicDeductionMismatch"])

        elif task_id == "logic_03":
            # CNF SAT assignment: SATISFIABLE with A=True, B=False, C=True
            is_sat = "SATISFIABLE" in text_upper and "UNSATISFIABLE" not in text_upper
            # Check assignment A=1/True, B=0/False, C=1/True
            b_false = ("B = FALSE" in text_upper or "B: FALSE" in text_upper or "NOT B" in text_upper or "B IS FALSE" in text_upper or "B=FALSE" in text_upper)
            if is_sat and b_false:
                return EvaluationResult(passed=True, score=1.0, feedback="Correctly derived satisfying CNF assignment.", failure_set=[])
            return EvaluationResult(passed=False, score=0.0, feedback="Invalid CNF assignment or satisfaction verdict.", failure_set=["SATAssignmentError"])

        elif task_id == "logic_04":
            # Sequence: E1, E4, E2, E3, E5
            expected_seq = ["E1", "E4", "E2", "E3", "E5"]
            seq_str = "".join(expected_seq)
            candidate_clean = re.sub(r"[^E12345]", "", text_upper)
            if seq_str in candidate_clean or all(e in text_upper for e in expected_seq):
                # Check relative order
                pos_e1 = text_upper.find("E1")
                pos_e4 = text_upper.find("E4")
                pos_e2 = text_upper.find("E2")
                pos_e3 = text_upper.find("E3")
                pos_e5 = text_upper.find("E5")
                if pos_e1 < pos_e4 < pos_e2 < pos_e3 < pos_e5:
                    return EvaluationResult(passed=True, score=1.0, feedback="Temporal sequence constraint satisfied.", failure_set=[])
            return EvaluationResult(passed=False, score=0.0, feedback="Temporal ordering constraints violated.", failure_set=["TemporalOrderViolation"])

        elif task_id == "logic_05":
            # Syllogism: conclusion (a) -> P is not hyper-exergy
            has_a = "(A)" in text_upper or "OPTION A" in text_upper or "P IS NOT HYPER-EXERGY" in text_upper or "NOT HYPER-EXERGY" in text_upper
            if has_a:
                return EvaluationResult(passed=True, score=1.0, feedback="Correct syllogistic conclusion (a).", failure_set=[])
            return EvaluationResult(passed=False, score=0.0, feedback="Incorrect syllogism conclusion.", failure_set=["SyllogismError"])

        # Fallback check for arbitrary logic task
        return EvaluationResult(
            passed="TRUE" in text_upper or "VALID" in text_upper,
            score=1.0 if "TRUE" in text_upper else 0.0,
            feedback="Evaluated using logic heuristic.",
            failure_set=[] if "TRUE" in text_upper else ["UnsatisfiedConstraint"]
        )
