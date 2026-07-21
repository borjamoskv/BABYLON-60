"""
CORTEX-OS Epistemic Cognitive Scheduler.
Schedules process tasks based on Priority * InfoGain * RiskReduction / TokenCost.
"""

from dataclasses import dataclass, field
import heapq
import time


@dataclass(order=True)
class ProcessTask:
    priority_score: float  # Inverted for min-heap (lower value = higher priority)
    pid: int = field(compare=False)
    name: str = field(compare=False)
    weight: float = field(compare=False, default=1.0)
    info_gain: float = field(compare=False, default=1.0)
    risk_reduction: float = field(compare=False, default=1.0)
    token_cost: float = field(compare=False, default=1.0)
    created_at: float = field(compare=False, default_factory=time.time)

    @classmethod
    def calculate_priority(
        cls,
        pid: int,
        name: str,
        weight: float,
        info_gain: float,
        risk_reduction: float,
        token_cost: float,
    ) -> "ProcessTask":
        # Score = (weight * info_gain * risk_reduction) / (token_cost + 1)
        raw_score = (weight * info_gain * risk_reduction) / (token_cost + 1.0)
        # Invert score for min-heap
        return cls(
            priority_score=-raw_score,
            pid=pid,
            name=name,
            weight=weight,
            info_gain=info_gain,
            risk_reduction=risk_reduction,
            token_cost=token_cost,
        )


class CognitiveScheduler:
    def __init__(self) -> None:
        self.ready_queue: list[ProcessTask] = []

    def schedule_task(self, task: ProcessTask) -> None:
        heapq.heappush(self.ready_queue, task)

    def next_task(self) -> ProcessTask | None:
        if self.ready_queue:
            return heapq.heappop(self.ready_queue)
        return None

    def queue_size(self) -> int:
        return len(self.ready_queue)
