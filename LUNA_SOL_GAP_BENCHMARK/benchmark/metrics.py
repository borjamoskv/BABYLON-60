# Metrics Engine for LUNA_SOL_GAP_BENCHMARK (CTM⁴⁰-CTM⁵⁰ Falsification)
from dataclasses import dataclass, asdict
from typing import Dict, List, Any

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
    recovery: float
    regression: float
    g_structure: float
    g_compute: float
    g_topology: float
    g_tools: float
    total_budget_consumed: Dict[str, int]
    falsified: bool
    kill_conditions_triggered: List[str]
    falsification_reason: str

class MetricsCalculator:
    def calculate(self, task_results: List[TaskResult]) -> BenchmarkFalsificationMetrics:
        if not task_results:
            raise ValueError("Task results list is empty.")
            
        count = len(task_results)
        branches = ["BASE", "EXTRA-COMPUTE", "RANDOM-CTM", "STRUCTURED-CTM", "CTM+TOOL"]
        
        success_counts = {b: 0 for b in branches}
        budget_counts = {b: 0 for b in branches}
        
        base_failed_count = 0
        ctm_recovered_count = 0
        base_passed_count = 0
        ctm_regressed_count = 0
        
        for tr in task_results:
            for b in branches:
                if tr.branch_passed.get(b, False):
                    success_counts[b] += 1
                budget_counts[b] += tr.branch_budget.get(b, 0)
                
            # Recovery & Regression against Structured CTM (Branch D)
            if not tr.branch_passed.get("BASE", False):
                base_failed_count += 1
                if tr.branch_passed.get("STRUCTURED-CTM", False):
                    ctm_recovered_count += 1
                    
            if tr.branch_passed.get("BASE", False):
                base_passed_count += 1
                if not tr.branch_passed.get("STRUCTURED-CTM", False):
                    ctm_regressed_count += 1

        cov = {b: success_counts[b] / count for b in branches}
        
        recovery = ctm_recovered_count / base_failed_count if base_failed_count > 0 else 0.0
        regression = ctm_regressed_count / base_passed_count if base_passed_count > 0 else 0.0
        
        # CTM⁴⁶ Causal Isolations
        # D-B: Value of Structure over just more compute
        g_structure = cov["STRUCTURED-CTM"] - cov["EXTRA-COMPUTE"]
        # C-B: Value of random feedback/compute without structure
        g_compute = cov["RANDOM-CTM"] - cov["EXTRA-COMPUTE"]
        # D-C: Value of the CTM Policy Topology vs Random Topology
        g_topology = cov["STRUCTURED-CTM"] - cov["RANDOM-CTM"]
        # E-D: Value of External Tools
        g_tools = cov["CTM+TOOL"] - cov["STRUCTURED-CTM"]
        
        # CTM⁴⁹ Kill Conditions
        kill_conditions = []
        
        # 1. Placebo Beats CTM
        if cov["RANDOM-CTM"] >= cov["STRUCTURED-CTM"] and cov["STRUCTURED-CTM"] > 0:
            kill_conditions.append("PLACEBO_BEATS_CTM: RANDOM-CTM achieved >= coverage than STRUCTURED-CTM.")
            
        # 2. Regression Rate > Limit (Limit = 0.0 for conservative formal limit)
        if regression > 0.0:
            kill_conditions.append(f"REGRESSION_DETECTED: {regression*100:.1f}% successes were destroyed.")
            
        # 3. Gain explained by Extra Compute
        if cov["STRUCTURED-CTM"] <= cov["EXTRA-COMPUTE"]:
            kill_conditions.append("GAIN_EXPLAINED_BY_COMPUTE: STRUCTURED-CTM coverage <= EXTRA-COMPUTE. No architectural advantage.")

        # 4. No Baseline Gain
        if cov["STRUCTURED-CTM"] <= cov["BASE"]:
            kill_conditions.append("H0_NOT_REJECTED: STRUCTURED-CTM did not improve over BASE.")

        falsified = len(kill_conditions) > 0

        return BenchmarkFalsificationMetrics(
            coverage=cov,
            recovery=recovery,
            regression=regression,
            g_structure=g_structure,
            g_compute=g_compute,
            g_topology=g_topology,
            g_tools=g_tools,
            total_budget_consumed=budget_counts,
            falsified=falsified,
            kill_conditions_triggered=kill_conditions,
            falsification_reason=" | ".join(kill_conditions) if falsified else "SURVIVED"
        )
