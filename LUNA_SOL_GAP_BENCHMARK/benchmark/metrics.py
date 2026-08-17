# Metrics Engine for LUNA_SOL_GAP_BENCHMARK
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


@dataclass
class TaskResult:
    task_id: str
    domain: str
    branch_scores: Dict[str, float]  # e.g. {"A": 0.0, "B": 1.0, "C": 1.0, "D": 1.0, "E": 1.0}
    branch_tokens: Dict[str, int]
    ctm_initial_passed: bool
    ctm_final_passed: bool
    ctm_iterations: int
    ctm_aborted_stagnation: bool


@dataclass
class BenchmarkMetrics:
    mean_scores: Dict[str, float]
    absolute_gain_g_ctm: float
    gap_remaining: float
    recovery_ratio_re: Optional[float]
    recovery_ratio_status: str
    verification_value_vv: Optional[float]
    domain_breakdown: Dict[str, Dict[str, float]]
    token_usage_totals: Dict[str, int]


class MetricsCalculator:
    def __init__(self, epsilon_baseline_gap: float = 0.05):
        self.epsilon_baseline_gap = epsilon_baseline_gap

    def calculate(self, task_results: List[TaskResult]) -> BenchmarkMetrics:
        if not task_results:
            raise ValueError("Task results list is empty.")

        branches = ["A", "B", "C", "D", "E"]
        sum_scores = {b: 0.0 for b in branches}
        sum_tokens = {b: 0 for b in branches}
        count = len(task_results)

        domain_results: Dict[str, Dict[str, List[float]]] = {}

        for tr in task_results:
            domain = tr.domain
            if domain not in domain_results:
                domain_results[domain] = {b: [] for b in branches}

            for b in branches:
                score = tr.branch_scores.get(b, 0.0)
                tokens = tr.branch_tokens.get(b, 0)
                sum_scores[b] += score
                sum_tokens[b] += tokens
                domain_results[domain][b].append(score)

        mean_scores = {b: round(sum_scores[b] / count, 4) for b in branches}

        A = mean_scores["A"]
        C = mean_scores["C"]
        D = mean_scores["D"]

        # Absolute Gain
        g_ctm = round(C - A, 4)

        # Gap Remaining
        g_remaining = round(D - C, 4)

        # Guarded Recovery Ratio R_E
        baseline_gap = abs(D - A)
        if baseline_gap > self.epsilon_baseline_gap:
            re_val = round(1.0 - (D - C) / (D - A), 4) if (D - A) != 0 else 0.0
            re_status = "valid"
        else:
            re_val = None
            re_status = "undefined (no meaningful baseline gap |D - A| <= epsilon)"

        # Verification Value (VV): P(correct_final | incorrect_initial)
        # Filter tasks where CTM initial pass was False
        ctm_initially_failed = [tr for tr in task_results if not tr.ctm_initial_passed]
        if ctm_initially_failed:
            rescued_count = sum(1 for tr in ctm_initially_failed if tr.ctm_final_passed)
            vv_val = round(rescued_count / len(ctm_initially_failed), 4)
        else:
            vv_val = None  # No initial failures to rescue

        # Domain breakdown
        domain_breakdown = {}
        for dom, b_map in domain_results.items():
            domain_breakdown[dom] = {b: round(sum(scores) / len(scores), 4) for b, scores in b_map.items()}
            # Compute domain R_E
            d_A = domain_breakdown[dom]["A"]
            d_C = domain_breakdown[dom]["C"]
            d_D = domain_breakdown[dom]["D"]
            if abs(d_D - d_A) > self.epsilon_baseline_gap:
                domain_breakdown[dom]["Recovery"] = round((d_C - d_A) / (d_D - d_A), 4)
            else:
                domain_breakdown[dom]["Recovery"] = -1.0  # N/A indicator

        return BenchmarkMetrics(
            mean_scores=mean_scores,
            absolute_gain_g_ctm=g_ctm,
            gap_remaining=g_remaining,
            recovery_ratio_re=re_val,
            recovery_ratio_status=re_status,
            verification_value_vv=vv_val,
            domain_breakdown=domain_breakdown,
            token_usage_totals=sum_tokens
        )
