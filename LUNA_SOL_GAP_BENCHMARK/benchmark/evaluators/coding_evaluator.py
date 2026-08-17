# Coding Evaluator for LUNA_SOL_GAP_BENCHMARK
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict
from benchmark.evaluators.base_evaluator import BaseEvaluator, EvaluationResult


class CodingEvaluator(BaseEvaluator):
    def _extract_code(self, candidate_solution: str) -> str:
        # Look for markdown python code blocks
        blocks = re.findall(r"```(?:python)?\s*\n(.*?)\n```", candidate_solution, re.DOTALL | re.IGNORECASE)
        if blocks:
            return "\n\n".join(blocks)
        # If no code block tags, use full raw text
        return candidate_solution

    def evaluate(self, candidate_solution: str, task: Dict[str, Any]) -> EvaluationResult:
        extracted_code = self._extract_code(candidate_solution)
        test_code = task.get("ground_truth", {}).get("test_code", "")

        full_script = f"""
import sys
import time
import threading

# Candidate Solution
{extracted_code}

# Verification Test Suite
{test_code}

print("ALL_TESTS_PASSED")
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(full_script)
            temp_path = f.name

        try:
            res = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=5.0
            )

            if res.returncode == 0 and "ALL_TESTS_PASSED" in res.stdout:
                return EvaluationResult(
                    passed=True,
                    score=1.0,
                    feedback="All test assertions passed successfully.",
                    failure_set=[],
                    details={"stdout": res.stdout}
                )
            else:
                error_msg = res.stderr.strip() or res.stdout.strip()
                # Parse specific line error or failure set
                failures = [line for line in error_msg.splitlines() if "AssertionError" in line or "Error" in line]
                if not failures:
                    failures = [f"Execution failed with return code {res.returncode}"]

                return EvaluationResult(
                    passed=False,
                    score=0.0,
                    feedback=f"Execution error:\n{error_msg[-400:]}",
                    failure_set=failures,
                    details={"stdout": res.stdout, "stderr": res.stderr}
                )

        except subprocess.TimeoutExpired:
            return EvaluationResult(
                passed=False,
                score=0.0,
                feedback="Execution timed out after 5.0 seconds.",
                failure_set=["TimeoutExpired"],
                details={"timeout": 5.0}
            )
        except Exception as e:
            return EvaluationResult(
                passed=False,
                score=0.0,
                feedback=f"System evaluator exception: {str(e)}",
                failure_set=[type(e).__name__],
                details={"error": str(e)}
            )
