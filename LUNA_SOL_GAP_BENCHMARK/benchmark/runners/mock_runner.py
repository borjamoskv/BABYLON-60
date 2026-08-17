# Mock Runner for Deterministic Offline Benchmark Execution
from typing import Dict, Any, Tuple
from benchmark.runners.base_runner import BaseRunner


class MockRunner(BaseRunner):
    def __init__(self, branch: str, model_name: str):
        self.branch = branch
        self.model_name = model_name
        self.current_task: Dict[str, Any] = {}

    def set_task(self, task: Dict[str, Any]):
        self.current_task = task

    def generate(self, prompt: str, use_think: bool = False) -> Tuple[str, int]:
        task_id = self.current_task.get("id", "")
        domain = self.current_task.get("domain", "")

        tokens = 250 if not use_think else 600

        # Branch D (Sol Baseline) always outputs high-fidelity solutions
        if self.branch == "D":
            return self._solve_perfectly(task_id, domain), tokens

        # CTM Repair / Synthesis Phase (Branch C and Branch E)
        if "REVISED, FULLY CORRECTIONS-APPLIED" in prompt or "Synthesize" in prompt:
            if self.branch == "E" and task_id in ["math_03", "logic_03"]:
                return self._solve_flawed(task_id, domain), tokens
            return self._solve_perfectly(task_id, domain), tokens

        # CTM Structural Phases
        if "Task Specification" in prompt:
            return f"Structured Problem Formalization for {task_id}:\n1. Objective identified.\n2. Constraints listed.", 150
        elif "Find edge-case failures" in prompt:
            return f"Adversarial vulnerability report for {task_id}:\nFound potential edge case failure in error handling.", 200

        # Initial Candidate Generation
        if self.branch == "A":
            # Single pass Luna fails hard multi-step tasks across all domains
            if task_id in ["code_01", "code_04", "arch_01", "arch_03", "math_03", "logic_03"]:
                return self._solve_flawed(task_id, domain), tokens
            return self._solve_perfectly(task_id, domain), tokens

        elif self.branch == "B":
            # Luna Think succeeds in math & logic, but fails complex coding & architecture
            if task_id in ["code_01", "arch_01", "arch_03"]:
                return self._solve_flawed(task_id, domain), tokens
            return self._solve_perfectly(task_id, domain), tokens

        elif self.branch in ["C", "E"]:
            # Initial generation for CTM has flaws on hard tasks, which CTM will repair
            if task_id in ["code_01", "code_04", "arch_01", "arch_03", "math_03", "logic_03"]:
                return self._solve_flawed(task_id, domain), tokens
            return self._solve_perfectly(task_id, domain), tokens

        return self._solve_perfectly(task_id, domain), tokens

    def _solve_perfectly(self, task_id: str, domain: str) -> str:
        # Returns exact passing solution code / math / logic / architecture based on task ground truth
        gt = self.current_task.get("ground_truth", {})

        if domain == "coding":
            if task_id == "code_01":
                return """```python
import time
from collections import OrderedDict

class ExpiringLRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.expiry = {}

    def get(self, key: int) -> int:
        self.evict_expired()
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int, ttl_seconds: int):
        self.evict_expired()
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl_seconds
        if len(self.cache) > self.capacity:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
            if oldest in self.expiry:
                del self.expiry[oldest]

    def evict_expired(self):
        now = time.time()
        expired = [k for k, exp in self.expiry.items() if exp <= now]
        for k in expired:
            if k in self.cache:
                del self.cache[k]
            del self.expiry[k]
```"""
            elif task_id == "code_02":
                return """```python
def longest_valid_parentheses(s: str) -> int:
    stack = [-1]
    max_len = 0
    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        else:
            stack.pop()
            if not stack:
                stack.append(i)
            else:
                max_len = max(max_len, i - stack[-1])
    return max_len
```"""
            elif task_id == "code_03":
                return """```python
def find_sccs(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    index = 0
    indices = [-1] * n
    lowlink = [-1] * n
    on_stack = [False] * n
    stack = []
    sccs = []

    def strongconnect(u):
        nonlocal index
        indices[u] = index
        lowlink[u] = index
        index += 1
        stack.append(u)
        on_stack[u] = True

        for v in adj[u]:
            if indices[v] == -1:
                strongconnect(v)
                lowlink[u] = min(lowlink[u], lowlink[v])
            elif on_stack[v]:
                lowlink[u] = min(lowlink[u], indices[v])

        if lowlink[u] == indices[u]:
            component = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
                if w == u:
                    break
            sccs.append(component)

    for i in range(n):
        if indices[i] == -1:
            strongconnect(i)
    return sorted([sorted(c) for c in sccs])
```"""
            elif task_id == "code_04":
                return """```python
import threading
import time

class BoundedRingBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = []
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)
        self.not_empty = threading.Condition(self.lock)

    def push(self, item, timeout: float) -> bool:
        end_time = time.time() + timeout
        with self.lock:
            while len(self.buffer) >= self.capacity:
                remaining = end_time - time.time()
                if remaining <= 0 or not self.not_full.wait(remaining):
                    return False
            self.buffer.append(item)
            self.not_empty.notify()
            return True

    def pop(self, timeout: float):
        end_time = time.time() + timeout
        with self.lock:
            while len(self.buffer) == 0:
                remaining = end_time - time.time()
                if remaining <= 0 or not self.not_empty.wait(remaining):
                    return None
            item = self.buffer.pop(0)
            self.not_full.notify()
            return item
```"""
            elif task_id == "code_05":
                return """```python
def merge_intervals(intervals: list[tuple[int, int, str]]) -> list[tuple[int, int, list[str]]]:
    if not intervals:
        return []
    sorted_inv = sorted(intervals, key=lambda x: (x[0], x[1]))
    res = []
    curr_start, curr_end, curr_labels = sorted_inv[0][0], sorted_inv[0][1], [sorted_inv[0][2]]

    for start, end, label in sorted_inv[1:]:
        if start <= curr_end:
            curr_end = max(curr_end, end)
            curr_labels.append(label)
        else:
            res.append((curr_start, curr_end, curr_labels))
            curr_start, curr_end, curr_labels = start, end, [label]
    res.append((curr_start, curr_end, curr_labels))
    return res
```"""

        elif domain == "mathematics":
            if task_id == "math_01":
                return "The closed form is T(n) = 2^n + 3^n. Evaluates to 2, 5, 13, 35, 275."
            elif task_id == "math_02":
                return "The trace of A^3 is exactly 91."
            elif task_id == "math_03":
                return "The conditional expectation E[X^2 | X > 1] is 7/4 = 1.75."
            elif task_id == "math_04":
                return "The number of derangements D_6 is 265."
            elif task_id == "math_05":
                return "The minimum distance is sqrt(14) = 3.741657."

        elif domain == "logic":
            if task_id == "logic_01":
                return "TRUE. The formula is a Tautology by truth table analysis."
            elif task_id == "logic_02":
                return "Deduction: Person A is a Knight, Person B is a Knight."
            elif task_id == "logic_03":
                return "SATISFIABLE with assignment A = True, B = False, C = True."
            elif task_id == "logic_04":
                return "The valid sequence of events is E1, E4, E2, E3, E5."
            elif task_id == "logic_05":
                return "Option (a): P is not hyper-exergy."

        elif domain == "architecture":
            reqs = gt.get("required_components", [])
            fms = gt.get("failure_modes", [])
            return f"Architecture design for {task_id}.\nComponents: " + ", ".join(reqs) + "\nFailure Modes: " + ", ".join(fms)

        return "Sample passing response."

    def _solve_flawed(self, task_id: str, domain: str) -> str:
        if domain == "coding":
            return """```python
# Flawed implementation missing edge-case check
class ExpiringLRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
    def get(self, key: int) -> int:
        return self.cache.get(key, -1)
    def put(self, key: int, value: int, ttl_seconds: int):
        self.cache[key] = value
    def evict_expired(self):
        pass
```"""
        elif domain == "architecture":
            return "Basic architectural proposal without compensating_transaction or circuit_breaker."
        elif domain == "mathematics":
            return "Calculated value: 42."
        return "Flawed candidate answer."
