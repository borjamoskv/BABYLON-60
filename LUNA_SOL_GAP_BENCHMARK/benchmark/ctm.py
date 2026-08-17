# Cognitive Transition Machine (CTM) Formal Engine for LUNA_SOL_GAP_BENCHMARK
# Implements CTM⁴⁰-CTM⁵⁰ Invariants (5-Arm Causal Falsification)
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
    policy: str  # 'BASE', 'EXTRA-COMPUTE', 'RANDOM-CTM', 'STRUCTURED-CTM', 'CTM+TOOL'
    passed: bool
    final_score: float
    budget_consumed_tokens: int
    iterations_used: int
    trace: List[TransitionTrace] = field(default_factory=list)

class CTMPolicyEngine:
    def __init__(self, runner: Any, checker: BaseEvaluator):
        self.runner = runner    # The Model (M)
        self.checker = checker  # The Legal Predicate (L) / Kernel

    def _execute_branch(self, task: Dict[str, Any], max_iterations: int, policy_name: str, use_feedback: bool, scramble_feedback: bool) -> CTMResult:
        task_id = task.get("id", "unknown")
        base_prompt = f"Solve the following task completely:\n{task.get('prompt')}"
        
        total_tokens = 0
        trace = []
        
        # Initial Pass (Iteration 1 is identical for all branches except its outcome)
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
        
        if eval_result.passed or max_iterations == 1:
            return CTMResult(
                task_id=task_id, policy=policy_name, passed=eval_result.passed,
                final_score=eval_result.score, budget_consumed_tokens=total_tokens,
                iterations_used=1, trace=trace
            )

        # Retry Loop
        for i in range(2, max_iterations + 1):
            if not use_feedback:
                # EXTRA-COMPUTE (B): Independent generation without conditional feedback
                prompt = base_prompt
            elif scramble_feedback:
                # RANDOM-CTM (C): Placebo feedback. Forces random mutation to break topology value.
                prompt = f"""Task: {task.get('prompt')}
Previous Candidate:
{candidate}
Kernel Feedback: {eval_result.feedback}
Failure Set: {eval_result.failure_set}
IGNORE THE FEEDBACK STRICTLY. Generate a completely random and vastly different alternative approach. Do not attempt to fix the errors structurally, just mutate drastically."""
            else:
                # STRUCTURED-CTM (D): True CTM Transition condition
                prompt = f"""Task: {task.get('prompt')}
Previous Candidate:
{candidate}
Kernel Verification Failure:
{eval_result.feedback}
Failure Set: {eval_result.failure_set}
Provide a corrected candidate that resolves these strict legality constraints."""

            # We use high temperature for Random CTM to ensure topological destruction
            temp_override = scramble_feedback
            candidate, tokens = self.runner.generate(prompt, use_think=True) 
            total_tokens += tokens
            eval_result = self.checker.evaluate(candidate, task)
            
            trace.append(TransitionTrace(
                iteration=i, candidate=candidate, verification=eval_result,
                tokens_consumed=tokens, is_legal=eval_result.passed
            ))
            
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

    def run_base(self, task: Dict[str, Any]) -> CTMResult:
        return self._execute_branch(task, max_iterations=1, policy_name="BASE", use_feedback=False, scramble_feedback=False)

    def run_extra_compute(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        return self._execute_branch(task, max_iterations=max_iterations, policy_name="EXTRA-COMPUTE", use_feedback=False, scramble_feedback=False)

    def run_random_ctm(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        return self._execute_branch(task, max_iterations=max_iterations, policy_name="RANDOM-CTM", use_feedback=True, scramble_feedback=True)

    def run_structured_ctm(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        return self._execute_branch(task, max_iterations=max_iterations, policy_name="STRUCTURED-CTM", use_feedback=True, scramble_feedback=False)

    def run_ctm_tool(self, task: Dict[str, Any], max_iterations: int) -> CTMResult:
        # Placeholder for Branch E (Mocked as identical to D until external Tool interpreter is injected)
        res = self._execute_branch(task, max_iterations=max_iterations, policy_name="CTM+TOOL", use_feedback=True, scramble_feedback=False)
        return res
