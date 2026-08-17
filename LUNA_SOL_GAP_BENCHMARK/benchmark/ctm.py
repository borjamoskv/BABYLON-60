# Cognitive Transition Machine (CTM) Formal Engine for LUNA_SOL_GAP_BENCHMARK
# Implements CTM³⁰ Invariants (Task, Model, TransitionSystem, Checker, Budget)
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from benchmark.evaluators.base_evaluator import BaseEvaluator, EvaluationResult

@dataclass
class TransitionTrace:
    iteration: int
    candidate: str
    verification: EvaluationResult
    tokens_consumed: int
    is_legal: bool

@dataclass
class CTMResult:
    task_id: str
    policy: str  # 'BASE', 'BASE-N', 'CTM'
    passed: bool
    final_score: float
    budget_consumed_tokens: int
    iterations_used: int
    trace: List[TransitionTrace] = field(default_factory=list)

class CTMPolicyEngine:
    def __init__(self, runner: Any, checker: BaseEvaluator):
        self.runner = runner    # The Model (M)
        self.checker = checker  # The Legal Predicate (L) / Kernel

    def run_base(self, task: Dict[str, Any], use_think: bool = True) -> CTMResult:
        """
        Policy A: BASE (Single Pass)
        Model generates 1 candidate. Kernel checks. Run ends.
        """
        task_id = task.get("id", "unknown")
        prompt = f"Solve the following task completely:\n{task.get('prompt')}"
        
        candidate, tokens = self.runner.generate(prompt, use_think=use_think)
        eval_result = self.checker.evaluate(candidate, task)
        
        trace = [TransitionTrace(
            iteration=1,
            candidate=candidate,
            verification=eval_result,
            tokens_consumed=tokens,
            is_legal=eval_result.passed
        )]
        
        return CTMResult(
            task_id=task_id,
            policy="BASE",
            passed=eval_result.passed,
            final_score=eval_result.score,
            budget_consumed_tokens=tokens,
            iterations_used=1,
            trace=trace
        )

    def run_random_retry(self, task: Dict[str, Any], max_iterations: int, use_think: bool = True) -> CTMResult:
        """
        Policy B: BASE-N (Random Retry)
        Model generates N independent candidates until Kernel accepts.
        Used to measure baseline Coverage(B) under Budget B=N without conditional transitioning.
        """
        task_id = task.get("id", "unknown")
        prompt = f"Solve the following task completely:\n{task.get('prompt')}"
        
        total_tokens = 0
        trace = []
        
        for i in range(1, max_iterations + 1):
            # Independent generation (no feedback injected)
            candidate, tokens = self.runner.generate(prompt, use_think=use_think)
            total_tokens += tokens
            eval_result = self.checker.evaluate(candidate, task)
            
            trace.append(TransitionTrace(
                iteration=i,
                candidate=candidate,
                verification=eval_result,
                tokens_consumed=tokens,
                is_legal=eval_result.passed
            ))
            
            if eval_result.passed:
                return CTMResult(
                    task_id=task_id,
                    policy="BASE-N",
                    passed=True,
                    final_score=eval_result.score,
                    budget_consumed_tokens=total_tokens,
                    iterations_used=i,
                    trace=trace
                )
                
        # Exhausted budget
        return CTMResult(
            task_id=task_id,
            policy="BASE-N",
            passed=False,
            final_score=trace[-1].verification.score,
            budget_consumed_tokens=total_tokens,
            iterations_used=max_iterations,
            trace=trace
        )

    def run_ctm(self, task: Dict[str, Any], max_iterations: int, use_think: bool = True) -> CTMResult:
        """
        Policy C: CTM (Conditional Transition)
        Model generates -> Kernel filters -> Kernel feedback conditionally restricts next generation.
        Measures structural Reachability improvement over Random Retry.
        """
        task_id = task.get("id", "unknown")
        prompt = f"Solve the following task completely:\n{task.get('prompt')}"
        
        total_tokens = 0
        trace = []
        
        candidate, tokens = self.runner.generate(prompt, use_think=use_think)
        total_tokens += tokens
        eval_result = self.checker.evaluate(candidate, task)
        
        trace.append(TransitionTrace(
            iteration=1,
            candidate=candidate,
            verification=eval_result,
            tokens_consumed=tokens,
            is_legal=eval_result.passed
        ))
        
        if eval_result.passed:
            return CTMResult(
                task_id=task_id,
                policy="CTM",
                passed=True,
                final_score=eval_result.score,
                budget_consumed_tokens=total_tokens,
                iterations_used=1,
                trace=trace
            )
            
        for i in range(2, max_iterations + 1):
            # CTM applies Legal restriction feedback to condition the next state
            transition_prompt = f"""Task: {task.get('prompt')}
Previous Candidate:
{candidate}

Kernel Verification Failure:
{eval_result.feedback}
Failure Set: {eval_result.failure_set}

Provide a corrected candidate that resolves these strict legality constraints.
"""
            candidate, tokens = self.runner.generate(transition_prompt, use_think=use_think)
            total_tokens += tokens
            eval_result = self.checker.evaluate(candidate, task)
            
            trace.append(TransitionTrace(
                iteration=i,
                candidate=candidate,
                verification=eval_result,
                tokens_consumed=tokens,
                is_legal=eval_result.passed
            ))
            
            if eval_result.passed:
                return CTMResult(
                    task_id=task_id,
                    policy="CTM",
                    passed=True,
                    final_score=eval_result.score,
                    budget_consumed_tokens=total_tokens,
                    iterations_used=i,
                    trace=trace
                )
                
        # Exhausted budget
        return CTMResult(
            task_id=task_id,
            policy="CTM",
            passed=False,
            final_score=trace[-1].verification.score,
            budget_consumed_tokens=total_tokens,
            iterations_used=max_iterations,
            trace=trace
        )
