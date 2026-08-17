# Cognitive Transition Machine (CTM) Orchestrator Engine for LUNA_SOL_GAP_BENCHMARK
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from benchmark.evaluators.base_evaluator import BaseEvaluator, EvaluationResult


@dataclass
class CTMTraceStep:
    iteration: int
    phase: str
    prompt: str
    output: str
    verification: Optional[EvaluationResult] = None
    delta_score: float = 0.0


@dataclass
class CTMResult:
    final_candidate: str
    passed: bool
    final_score: float
    initial_passed: bool
    initial_score: float
    iterations: int
    aborted_stagnation: bool
    aborted_max_iterations: bool
    trace: List[CTMTraceStep] = field(default_factory=list)
    tokens_used: int = 0
    feedback: str = ""


class CTM:
    def __init__(
        self,
        runner: Any,
        evaluator: BaseEvaluator,
        max_iterations: int = 3,
        epsilon_semantic_delta: float = 0.05,
        epsilon_score_delta: float = 0.01
    ):
        self.runner = runner
        self.evaluator = evaluator
        self.max_iterations = max_iterations
        self.epsilon_semantic_delta = epsilon_semantic_delta
        self.epsilon_score_delta = epsilon_score_delta

    def _calculate_semantic_delta(self, candidate_a: str, candidate_b: str) -> float:
        # Simple Jaccard distance over word 3-grams to measure semantic delta
        words_a = set(candidate_a.lower().split())
        words_b = set(candidate_b.lower().split())
        if not words_a and not words_b:
            return 0.0
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        similarity = len(intersection) / len(union) if union else 1.0
        return 1.0 - similarity

    def run(self, task: Dict[str, Any], use_think: bool = True) -> CTMResult:
        trace: List[CTMTraceStep] = []
        total_tokens = 0

        # Phase 0: Specify & Phase 1: Decompose
        specify_prompt = f"""Task Specification & Decomposition:
Objective: {task.get('prompt')}
Identify constraints, failure modes, and isolate independent subproblems.
Output a structured problem formalization.
"""
        spec_out, tok0 = self.runner.generate(specify_prompt, use_think=use_think)
        total_tokens += tok0
        trace.append(CTMTraceStep(iteration=0, phase="specify_decompose", prompt=specify_prompt, output=spec_out))

        # Phase 2: Generation (Solve)
        solve_prompt = f"""Problem Formalization:
{spec_out}

Task: {task.get('prompt')}

Produce a complete candidate solution. State assumptions explicitly.
"""
        candidate, tok1 = self.runner.generate(solve_prompt, use_think=use_think)
        total_tokens += tok1
        trace.append(CTMTraceStep(iteration=0, phase="solve", prompt=solve_prompt, output=candidate))

        # Initial evaluation
        initial_verification = self.evaluator.evaluate(candidate, task)
        initial_passed = initial_verification.passed
        initial_score = initial_verification.score

        if initial_passed:
            # Immediate success without requiring repair loop
            synth_prompt = f"Synthesize final clean solution:\n{candidate}"
            synth_out, tok_s = self.runner.generate(synth_prompt, use_think=False)
            total_tokens += tok_s
            return CTMResult(
                final_candidate=candidate,
                passed=True,
                final_score=initial_score,
                initial_passed=initial_passed,
                initial_score=initial_score,
                iterations=0,
                aborted_stagnation=False,
                aborted_max_iterations=False,
                trace=trace,
                tokens_used=total_tokens,
                feedback=initial_verification.feedback
            )

        # Iterative Verification, Attack, and Repair Loop
        history_scores = [initial_score]
        history_candidates = [candidate]

        for iteration in range(1, self.max_iterations + 1):
            # Phase 3: Adversarial Attack
            attack_prompt = f"""Candidate Solution:
{candidate}

Task Constraints: {task.get('prompt')}
Evaluation Feedback: {initial_verification.feedback}

Find edge-case failures, counterexamples, or missing structural components in this candidate solution.
"""
            attack_out, tok_a = self.runner.generate(attack_prompt, use_think=use_think)
            total_tokens += tok_a

            # Phase 4 & 5: Repair
            repair_prompt = f"""Original Task: {task.get('prompt')}
Current Candidate Solution:
{candidate}

Adversarial Analysis of Vulnerabilities:
{attack_out}

Verification Errors:
{initial_verification.feedback}
Failure Set: {initial_verification.failure_set}

Produce a REVISED, FULLY CORRECTIONS-APPLIED candidate solution.
"""
            repaired_candidate, tok_r = self.runner.generate(repair_prompt, use_think=use_think)
            total_tokens += tok_r

            # External Verification
            verification = self.evaluator.evaluate(repaired_candidate, task)
            score_delta = verification.score - history_scores[-1]
            semantic_delta = self._calculate_semantic_delta(candidate, repaired_candidate)

            trace.append(CTMTraceStep(
                iteration=iteration,
                phase="attack_repair_verify",
                prompt=repair_prompt,
                output=repaired_candidate,
                verification=verification,
                delta_score=score_delta
            ))

            if verification.passed:
                return CTMResult(
                    final_candidate=repaired_candidate,
                    passed=True,
                    final_score=verification.score,
                    initial_passed=initial_passed,
                    initial_score=initial_score,
                    iterations=iteration,
                    aborted_stagnation=False,
                    aborted_max_iterations=False,
                    trace=trace,
                    tokens_used=total_tokens,
                    feedback=verification.feedback
                )

            # Stagnation Check
            if semantic_delta < self.epsilon_semantic_delta and abs(score_delta) < self.epsilon_score_delta:
                return CTMResult(
                    final_candidate=repaired_candidate,
                    passed=False,
                    final_score=verification.score,
                    initial_passed=initial_passed,
                    initial_score=initial_score,
                    iterations=iteration,
                    aborted_stagnation=True,
                    aborted_max_iterations=False,
                    trace=trace,
                    tokens_used=total_tokens,
                    feedback=f"ABORT_STAGNATION: Semantic delta {semantic_delta:.4f} < {self.epsilon_semantic_delta}"
                )

            candidate = repaired_candidate
            history_scores.append(verification.score)
            history_candidates.append(repaired_candidate)
            initial_verification = verification

        return CTMResult(
            final_candidate=candidate,
            passed=False,
            final_score=history_scores[-1],
            initial_passed=initial_passed,
            initial_score=history_scores[0],
            iterations=self.max_iterations,
            aborted_stagnation=False,
            aborted_max_iterations=True,
            trace=trace,
            tokens_used=total_tokens,
            feedback=f"ABORT_MAX_ITERATIONS: Reached limit {self.max_iterations}"
        )
