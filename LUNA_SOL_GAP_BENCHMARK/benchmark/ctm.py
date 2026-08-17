# Cognitive Transition Machine (CTM) Formal Engine for LUNA_SOL_GAP_BENCHMARK
# Implements CTM⁵¹-CTM⁵⁹ Invariants (Falsification v3)
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from benchmark.evaluators.base_evaluator import BaseEvaluator, EvaluationResult
import random

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
    policy: str  # 'SINGLE_PASS', 'INDEPENDENT_RETRY', 'ADAPTIVE_PLACEBO', 'CTM', 'PERMUTED_CTM'
    passed: bool
    final_score: float
    budget_consumed_tokens: int
    iterations_used: int
    trace: List[TransitionTrace] = field(default_factory=list)

class CTMPolicyEngine:
    def __init__(self, runner: Any, checker: BaseEvaluator):
        self.runner = runner    # The Model (M)
        self.checker = checker  # The Legal Predicate (L) / Kernel

    def _execute_branch(self, task: Dict[str, Any], max_iterations: int, policy_name: str) -> CTMResult:
        task_id = task.get("id", "unknown")
        base_prompt = f"Solve the following task completely:\n{task.get('prompt')}"
        
        total_tokens = 0
        trace: List[TransitionTrace] = []
        feedback_history = []
        
        # Initial Pass (Identical base state for all branches)
        candidate, tokens = self.runner.generate(base_prompt, use_think=True)
        total_tokens += tokens
        eval_result = self.checker.evaluate(candidate, task)
        
        trace.append(TransitionTrace(
            iteration=1,
            candidate=candidate,
            verification=eval_result,
            tokens_consumed=tokens,
            is_legal=eval_result.passed
        ))
        
        feedback_history.append((eval_result.feedback, eval_result.failure_set))
        
        if eval_result.passed or max_iterations == 1:
            return CTMResult(
                task_id=task_id, policy=policy_name, passed=eval_result.passed,
                final_score=eval_result.score, budget_consumed_tokens=total_tokens,
                iterations_used=1, trace=trace
            )

        # Retry Loop
        for i in range(2, max_iterations + 1):
            if policy_name == "INDEPENDENT_RETRY":
                prompt = base_prompt
                
            elif policy_name == "ADAPTIVE_PLACEBO":
                prompt = f"""Task: {task.get('prompt')}
Previous Candidate:
{candidate}
Kernel Feedback: {eval_result.feedback}
Failure Set: {eval_result.failure_set}
You failed. Do NOT try to fix the specific constraints structurally. Instead, ignore the details of the failure and just guess a completely different and creative alternative solution."""

            elif policy_name == "PERMUTED_CTM":
                # Inject a random past feedback instead of the most recent one to destroy topological order
                random_past = random.choice(feedback_history)
                past_feedback, past_failures = random_past
                prompt = f"""Task: {task.get('prompt')}
Previous Candidate:
{candidate}
Kernel Verification Failure (Scrambled Order):
{past_feedback}
Failure Set: {past_failures}
Provide a corrected candidate that resolves these strict legality constraints."""

            else:
                # CTM (Structured)
                prompt = f"""Task: {task.get('prompt')}
Previous Candidate:
{candidate}
Kernel Verification Failure:
{eval_result.feedback}
Failure Set: {eval_result.failure_set}
Provide a corrected candidate that strictly resolves these legality constraints without breaking existing invariants."""

            # Override temperature for placebo branches to encourage structural break
            use_high_temp = policy_name in ["ADAPTIVE_PLACEBO"]
            candidate, tokens = self.runner.generate(prompt, use_think=not use_high_temp) 
            total_tokens += tokens
            eval_result = self.checker.evaluate(candidate, task)
            
            trace.append(TransitionTrace(
                iteration=i, candidate=candidate, verification=eval_result,
                tokens_consumed=tokens, is_legal=eval_result.passed
            ))
            
            feedback_history.append((eval_result.feedback, eval_result.failure_set))
            
            if eval_result.passed:
                return CTMResult(
                    task_id=task_id, policy=policy_name, passed=True,
                    final_score=eval_result.score, budget_consumed_tokens=total_tokens,
                    iterations_used=i, trace=trace
                )
                
        return CTMResult(
            task_id=task_id, policy=policy_name, passed=False,
            final_score=trace[-1].verification.score, budget_consumed_tokens=total_tokens,
            iterations_used=max_iterations, trace=trace
        )

    def run_single_pass(self, task: Dict[str, Any]) -> CTMResult:
        return self._execute_branch(task, max_iterations=1, policy_name="SINGLE_PASS")

    def run_independent_retry(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        return self._execute_branch(task, max_iterations=max_iterations, policy_name="INDEPENDENT_RETRY")

    def run_adaptive_placebo(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        return self._execute_branch(task, max_iterations=max_iterations, policy_name="ADAPTIVE_PLACEBO")

    def run_ctm(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        return self._execute_branch(task, max_iterations=max_iterations, policy_name="CTM")

    def run_permuted_ctm(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        return self._execute_branch(task, max_iterations=max_iterations, policy_name="PERMUTED_CTM")
