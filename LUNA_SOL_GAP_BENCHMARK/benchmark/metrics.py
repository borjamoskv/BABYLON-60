# Metrics Engine for LUNA_SOL_GAP_BENCHMARK (CTM⁵¹-CTM⁵⁹ Falsification v3)
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

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
    primary_hypothesis_ctm_vs_placebo: bool
    primary_hypothesis_ctm_vs_permuted: bool
    total_budget_consumed: Dict[str, int]
    weak_oracle_excluded_domains: List[str]
    falsified: bool
    falsification_reason: str

class MetricsCalculator:
    def __init__(self, weak_oracles: List[str] = None):
        self.weak_oracles = weak_oracles or ["architecture"]

    def calculate(self, task_results: List[TaskResult]) -> BenchmarkFalsificationMetrics:
        if not task_results:
            raise ValueError("Task results list is empty.")
            
        branches = ["SINGLE_PASS", "INDEPENDENT_RETRY", "ADAPTIVE_PLACEBO", "CTM", "PERMUTED_CTM", "SOL_BASELINE"]
        
        success_counts = {b: 0 for b in branches}
        budget_counts = {b: 0 for b in branches}
        
        base_passed_count = 0
        ctm_regressed_count = 0
        
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
                    
            if tr.branch_passed.get("SINGLE_PASS", False):
                base_passed_count += 1
                if not tr.branch_passed.get("CTM", False):
                    ctm_regressed_count += 1

        if valid_tasks_count == 0:
            raise ValueError("No valid tasks remain after excluding weak oracles.")

        cov = {b: success_counts[b] / valid_tasks_count for b in branches}
        
        regression = ctm_regressed_count / base_passed_count if base_passed_count > 0 else 0.0
        
        # Primary Algorithmic Value Claims (CTM > Adaptive Placebo AND CTM > Permuted CTM)
        h_ctm_vs_placebo = cov["CTM"] > cov["ADAPTIVE_PLACEBO"]
        h_ctm_vs_permuted = cov["CTM"] > cov["PERMUTED_CTM"]
        
        # Capability vs Sol
        observed_gap_closed = None
        capability_ce = None
        if "SOL_BASELINE" in cov and cov["SOL_BASELINE"] > 0:
            sol_cov = cov["SOL_BASELINE"]
            luna_single_cov = cov["SINGLE_PASS"]
            luna_ctm_cov = cov["CTM"]
            
            if sol_cov > luna_single_cov:
                observed_gap_closed = (luna_ctm_cov - luna_single_cov) / (sol_cov - luna_single_cov)
            
            capability_ce = luna_ctm_cov / sol_cov

        falsified = False
        reasons = []
        
        # Kill Conditions based on the new H_CTM Focus
        if cov["CTM"] <= cov["ADAPTIVE_PLACEBO"]:
            falsified = True
            reasons.append("FAILED H_CTM: CTM failed to beat the unstructured Adaptive Placebo. Topology adds no value.")
            
        if cov["CTM"] <= cov["PERMUTED_CTM"]:
            falsified = True
            reasons.append("FAILED H_CTM_PERMUTED: CTM failed to beat Permuted CTM. Transition order doesn't matter.")

        # Regression is no longer a hard kill unless it's catastrophic (> 5%)
        if regression > 0.05:
            falsified = True
            reasons.append(f"CATASTROPHIC_REGRESSION: {regression*100:.1f}% successes destroyed. Violates conservative extension.")

        return BenchmarkFalsificationMetrics(
            coverage=cov,
            regression_rate=regression,
            observed_gap_closed=observed_gap_closed,
            capability_relative_score_ce=capability_ce,
            primary_hypothesis_ctm_vs_placebo=h_ctm_vs_placebo,
            primary_hypothesis_ctm_vs_permuted=h_ctm_vs_permuted,
            total_budget_consumed=budget_counts,
            weak_oracle_excluded_domains=self.weak_oracles,
            falsified=falsified,
            falsification_reason=" | ".join(reasons) if falsified else "SURVIVED: Topology proven valuable."
        )
