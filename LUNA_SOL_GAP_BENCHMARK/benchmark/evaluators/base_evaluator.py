# Base Evaluator Interface for LUNA_SOL_GAP_BENCHMARK
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvaluationResult:
    passed: bool
    score: float  # 0.0 to 1.0
    feedback: str
    failure_set: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(self, candidate_solution: str, task: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate candidate solution against task ground truth.
        Must return EvaluationResult with passed boolean and numeric score [0.0, 1.0].
        """
        pass
