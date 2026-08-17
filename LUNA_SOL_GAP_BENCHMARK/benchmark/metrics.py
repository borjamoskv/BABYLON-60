# Metrics Engine for LUNA_SOL_GAP_BENCHMARK (CTM³⁰ Falsification)
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

@dataclass
class TaskResult:
    task_id: str
    domain: str
    branch_passed: Dict[str, bool]    # {"BASE": True, "BASE-N": False, "CTM": True}
    branch_scores: Dict[str, float]
    branch_budget: Dict[str, int]     # tokens or iterations consumed

@dataclass
class BenchmarkFalsificationMetrics:
    coverage: Dict[str, float]
    recovery: float
    regression: float
    g_strategy: float
    domain_breakdown: Dict[str, Dict[str, float]]
    total_budget_consumed: Dict[str, int]
    falsified: bool
    falsification_reason: str

class MetricsCalculator:
    def calculate(self, task_results: List[TaskResult]) -> BenchmarkFalsificationMetrics:
        if not task_results:
            raise ValueError("Task results list is empty.")
            
        count = len(task_results)
        branches = ["BASE", "BASE-N", "CTM"]
        
        # Coverage counters
        success_counts = {b: 0 for b in branches}
        budget_counts = {b: 0 for b in branches}
        
        # Recovery & Regression counters
        base_failed_count = 0
        ctm_recovered_count = 0
        
        base_passed_count = 0
        ctm_regressed_count = 0
        
        domain_success = {}
        domain_counts = {}

        for tr in task_results:
            dom = tr.domain
            if dom not in domain_success:
                domain_success[dom] = {b: 0 for b in branches}
                domain_counts[dom] = 0
            domain_counts[dom] += 1
            
            for b in branches:
                if tr.branch_passed.get(b, False):
                    success_counts[b] += 1
                    domain_success[dom][b] += 1
                budget_counts[b] += tr.branch_budget.get(b, 0)
                
            # Recovery: BASE failed, CTM passed
            if not tr.branch_passed.get("BASE", False):
                base_failed_count += 1
                if tr.branch_passed.get("CTM", False):
                    ctm_recovered_count += 1
                    
            # Regression: BASE passed, CTM failed
            if tr.branch_passed.get("BASE", False):
                base_passed_count += 1
                if not tr.branch_passed.get("CTM", False):
                    ctm_regressed_count += 1

        coverage = {b: success_counts[b] / count for b in branches}
        
        recovery = ctm_recovered_count / base_failed_count if base_failed_count > 0 else 0.0
        regression = ctm_regressed_count / base_passed_count if base_passed_count > 0 else 0.0
        
        # G_strategy measures CTM conditional gain over independent random retry under SAME budget B=N
        g_strategy = coverage.get("CTM", 0.0) - coverage.get("BASE-N", 0.0)
        
        # Falsification Checks
        falsified = False
        reasons = []
        
        if regression > 0.0:
            falsified = True
            reasons.append(f"REGRESSION_DETECTED: {regression*100:.1f}%. CTM destroyed a valid baseline certificate.")
            
        if g_strategy <= 0.0:
            falsified = True
            reasons.append(f"NO_STRATEGY_GAIN: CTM Coverage ({coverage.get('CTM',0.0):.2f}) <= BASE-N ({coverage.get('BASE-N',0.0):.2f}). Gain is purely due to compute budget.")
            
        if coverage.get("CTM", 0.0) <= coverage.get("BASE", 0.0):
            falsified = True
            reasons.append("H0_NOT_REJECTED: CTM did not improve absolute coverage over BASE.")
            
        domain_breakdown = {}
        for dom, counts in domain_success.items():
            domain_breakdown[dom] = {b: counts[b] / domain_counts[dom] for b in branches}

        return BenchmarkFalsificationMetrics(
            coverage=coverage,
            recovery=recovery,
            regression=regression,
            g_strategy=g_strategy,
            domain_breakdown=domain_breakdown,
            total_budget_consumed=budget_counts,
            falsified=falsified,
            falsification_reason=" | ".join(reasons) if reasons else "SURVIVED"
        )
