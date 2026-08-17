# Metrics Engine for LUNA_SOL_GAP_BENCHMARK (CTM⁵¹-CTM⁶³ Falsification v5)
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import math

@dataclass
class TaskResult:
    task_id: str
    domain: str
    branch_passed: Dict[str, bool]
    branch_scores: Dict[str, float]
    branch_budget: Dict[str, int]

@dataclass
class BenchmarkFalsificationMetrics:
    coverage: Dict[str, float]
    regression_rate: float
    observed_gap_closed: Optional[float]
    capability_relative_score_ce: Optional[float]
    efficiency: Dict[str, float]
    primary_hypothesis_ctm_vs_placebo: bool
    primary_hypothesis_ctm_vs_permuted: bool
    total_budget_consumed: Dict[str, int]
    weak_oracle_excluded_domains: List[str]
    discordance_c_vs_d: Dict[str, int]  # b (C wins), c (D wins), b+c (total discordant pairs)
    discordance_f_vs_d: Dict[str, int]  # b (F wins), c (D wins), b+c (total discordant pairs)
    p_value_c_vs_d: float
    p_value_f_vs_d: float
    falsified: bool
    falsification_reason: str

class MetricsCalculator:
    def __init__(self, weak_oracles: List[str] = None, max_regression_rate: float = 0.05, alpha: float = 0.05):
        self.weak_oracles = weak_oracles or ["architecture"]
        self.max_regression_rate = max_regression_rate
        self.alpha = alpha

    def exact_mcnemar_p_value(self, b: int, c: int) -> float:
        """
        Calculates exact McNemar p-value for H1: c > b using Binomial(b+c, 0.5)
        p = P(X >= c)
        """
        n = b + c
        if n == 0:
            return 1.0  # No discordants (b+c=0), cannot reject H0
        p_val = 0.0
        for k in range(c, n + 1):
            p_val += math.comb(n, k) * (0.5 ** n)
        return p_val

    def calculate(self, task_results: List[TaskResult]) -> BenchmarkFalsificationMetrics:
        if not task_results:
            raise ValueError("Task results list is empty.")
            
        branches = ["BASE", "EXTRA_COMPUTE", "NULL_ADAPTIVE_CONTROL", "STRUCTURED_CTM", "CTM_TOOL", "PERMUTED_CTM", "SOL_BASELINE"]
        
        success_counts = {b: 0 for b in branches}
        budget_counts = {b: 0 for b in branches}
        
        base_passed_count = 0
        ctm_regressed_count = 0
        
        # McNemar discordants
        discordant_C_vs_D = {"b_C_wins": 0, "c_D_wins": 0}
        discordant_F_vs_D = {"b_F_wins": 0, "c_D_wins": 0}
        
        valid_tasks_count = 0

        for tr in task_results:
            for b in branches:
                budget_counts[b] += tr.branch_budget.get(b, 0)
                
            # Exclude weak oracles from the primary rigorous claim
            if tr.domain in self.weak_oracles:
                continue
                
            valid_tasks_count += 1
            
            for b in branches:
                if tr.branch_passed.get(b, False):
                    success_counts[b] += 1
                    
            if tr.branch_passed.get("BASE", False):
                base_passed_count += 1
                if not tr.branch_passed.get("STRUCTURED_CTM", False):
                    ctm_regressed_count += 1
                    
            # McNemar Pairs (C vs D)
            pass_c = tr.branch_passed.get("NULL_ADAPTIVE_CONTROL", False)
            pass_d = tr.branch_passed.get("STRUCTURED_CTM", False)
            if pass_c and not pass_d:
                discordant_C_vs_D["b_C_wins"] += 1
            elif pass_d and not pass_c:
                discordant_C_vs_D["c_D_wins"] += 1
                
            # McNemar Pairs (F vs D)
            pass_f = tr.branch_passed.get("PERMUTED_CTM", False)
            if pass_f and not pass_d:
                discordant_F_vs_D["b_F_wins"] += 1
            elif pass_d and not pass_f:
                discordant_F_vs_D["c_D_wins"] += 1

        if valid_tasks_count == 0:
            raise ValueError("No valid tasks remain after excluding weak oracles.")

        cov = {b: success_counts[b] / valid_tasks_count for b in branches}
        efficiency = {b: (success_counts[b] / budget_counts[b] if budget_counts[b] > 0 else 0) for b in branches}
        regression = ctm_regressed_count / base_passed_count if base_passed_count > 0 else 0.0
        
        b_c = discordant_C_vs_D["b_C_wins"]
        c_c = discordant_C_vs_D["c_D_wins"]
        b_f = discordant_F_vs_D["b_F_wins"]
        c_f = discordant_F_vs_D["c_D_wins"]

        discordant_C_vs_D["total_discordant_b_plus_c"] = b_c + c_c
        discordant_F_vs_D["total_discordant_b_plus_c"] = b_f + c_f

        # McNemar Significance Tests
        p_val_c = self.exact_mcnemar_p_value(b=b_c, c=c_c)
        p_val_f = self.exact_mcnemar_p_value(b=b_f, c=c_f)
        
        h_ctm_vs_placebo = p_val_c <= self.alpha
        h_ctm_vs_permuted = p_val_f <= self.alpha
        
        # Capability vs Sol
        observed_gap_closed = None
        capability_ce = None
        if "SOL_BASELINE" in cov and cov["SOL_BASELINE"] > 0:
            sol_cov = cov["SOL_BASELINE"]
            luna_single_cov = cov["BASE"]
            luna_ctm_cov = cov["STRUCTURED_CTM"]
            if sol_cov > luna_single_cov:
                observed_gap_closed = (luna_ctm_cov - luna_single_cov) / (sol_cov - luna_single_cov)
            capability_ce = luna_ctm_cov / sol_cov

        falsified = False
        reasons = []
        
        # Kill Conditions based on the McNemar Exact Tests
        if not h_ctm_vs_placebo:
            falsified = True
            reasons.append(f"FAILED H_CTM: STRUCTURED_CTM not significantly better than NULL_ADAPTIVE_CONTROL (p={p_val_c:.3f} > {self.alpha}, discordance b+c={b_c+c_c}).")
            
        if not h_ctm_vs_permuted:
            falsified = True
            reasons.append(f"FAILED H_CTM_PERMUTED: STRUCTURED_CTM not significantly better than PERMUTED_CTM (p={p_val_f:.3f} > {self.alpha}, discordance b+c={b_f+c_f}). Topology adds no value.")

        # Regression Tolerance
        if regression > self.max_regression_rate:
            falsified = True
            reasons.append(f"CATASTROPHIC_REGRESSION: {regression*100:.1f}% successes destroyed, exceeding tolerance of {self.max_regression_rate*100:.1f}%.")
            
        # Compute Control
        if cov["STRUCTURED_CTM"] <= cov["EXTRA_COMPUTE"] and efficiency["STRUCTURED_CTM"] <= efficiency["EXTRA_COMPUTE"]:
            falsified = True
            reasons.append("FAILED EFFICIENCY: STRUCTURED_CTM failed to beat EXTRA_COMPUTE in both Coverage and Efficiency.")

        return BenchmarkFalsificationMetrics(
            coverage=cov,
            regression_rate=regression,
            observed_gap_closed=observed_gap_closed,
            capability_relative_score_ce=capability_ce,
            efficiency=efficiency,
            primary_hypothesis_ctm_vs_placebo=h_ctm_vs_placebo,
            primary_hypothesis_ctm_vs_permuted=h_ctm_vs_permuted,
            total_budget_consumed=budget_counts,
            weak_oracle_excluded_domains=self.weak_oracles,
            discordance_c_vs_d=discordant_C_vs_D,
            discordance_f_vs_d=discordant_F_vs_D,
            p_value_c_vs_d=p_val_c,
            p_value_f_vs_d=p_val_f,
            falsified=falsified,
            falsification_reason=" | ".join(reasons) if falsified else "SURVIVED: Structured Topology proven significantly valuable."
        )
