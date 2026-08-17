# Unit Test Suite for LUNA_SOL_GAP_BENCHMARK v0.1
import pytest
from benchmark.evaluators.coding_evaluator import CodingEvaluator
from benchmark.evaluators.math_evaluator import MathEvaluator
from benchmark.evaluators.logic_evaluator import LogicEvaluator
from benchmark.evaluators.architecture_evaluator import ArchitectureEvaluator
from benchmark.ctm import CTM
from benchmark.runners.mock_runner import MockRunner
from benchmark.metrics import MetricsCalculator, TaskResult
from benchmark.statistics import StatisticsEngine


def test_coding_evaluator_pass():
    evaluator = CodingEvaluator()
    task = {
        "ground_truth": {
            "test_code": "assert add(2, 3) == 5"
        }
    }
    candidate = "```python\ndef add(a, b):\n    return a + b\n```"
    res = evaluator.evaluate(candidate, task)
    assert res.passed is True
    assert res.score == 1.0


def test_coding_evaluator_fail():
    evaluator = CodingEvaluator()
    task = {
        "ground_truth": {
            "test_code": "assert add(2, 3) == 5"
        }
    }
    candidate = "```python\ndef add(a, b):\n    return a * b\n```"
    res = evaluator.evaluate(candidate, task)
    assert res.passed is False
    assert res.score == 0.0
    assert "AssertionError" in str(res.failure_set)


def test_math_evaluator():
    evaluator = MathEvaluator()
    task = {"ground_truth": {"value": 1.75}}
    res = evaluator.evaluate("The answer is 7/4 = 1.75.", task)
    assert res.passed is True
    assert res.score == 1.0


def test_logic_evaluator():
    evaluator = LogicEvaluator()
    task = {"id": "logic_02"}
    res = evaluator.evaluate("Person A is a Knight, Person B is a Knight.", task)
    assert res.passed is True
    assert res.score == 1.0


def test_architecture_evaluator():
    evaluator = ArchitectureEvaluator()
    task = {
        "ground_truth": {
            "required_components": ["compensating_transaction", "idempotency_key"],
            "failure_modes": ["payment_failed"]
        }
    }
    candidate = "Design with compensating_transaction, idempotency_key, and payment_failed recovery."
    res = evaluator.evaluate(candidate, task)
    assert res.passed is True
    assert res.score == 1.0


def test_ctm_stagnation_detection():
    runner = MockRunner(branch="A", model_name="luna")
    evaluator = CodingEvaluator()
    task = {
        "prompt": "Write bad code",
        "ground_truth": {"test_code": "assert False"}
    }
    ctm = CTM(runner=runner, evaluator=evaluator, max_iterations=2, epsilon_semantic_delta=0.9)
    res = ctm.run(task, use_think=False)
    assert res.passed is False
    assert res.aborted_stagnation is True or res.aborted_max_iterations is True


def test_metrics_calculator():
    calc = MetricsCalculator(epsilon_baseline_gap=0.05)
    tr = TaskResult(
        task_id="t1",
        domain="coding",
        branch_scores={"A": 0.5, "B": 0.8, "C": 1.0, "D": 1.0, "E": 0.9},
        branch_tokens={"A": 100, "B": 200, "C": 300, "D": 200, "E": 250},
        ctm_initial_passed=False,
        ctm_final_passed=True,
        ctm_iterations=1,
        ctm_aborted_stagnation=False
    )
    metrics = calc.calculate([tr])
    assert metrics.mean_scores["A"] == 0.5
    assert metrics.absolute_gain_g_ctm == 0.5
    assert metrics.recovery_ratio_re == 1.0
    assert metrics.verification_value_vv == 1.0
