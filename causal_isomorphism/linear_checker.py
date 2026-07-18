# causal_isomorphism/linear_checker.py — Linear and Affine Type Checker
# C5-REAL: Static analysis pass for linear/affine/region constraints
# Author: Borja Moskv (borjamoskv)
"""
Verifies linear and affine type constraints on the Intermediate Representation (IR).

Linear rules:
  - If a parameter's type is linear (is_linear=True) or the parameter is marked
    as consumed (is_consumed=True), it must be consumed EXACTLY ONCE in the
    execution flow of the function.

Affine rules:
  - If a parameter's type is affine (is_affine=True), it must be consumed AT MOST
    ONCE in the execution flow.

Consuming operations:
  - Passing as an argument to a function call or constructor.
  - Pattern matching on it.
  - Returning it.
  - Using it in binary operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from causal_isomorphism.ir import (
    IRModule,
    IRFunction,
    IRExpr,
    IRExprKind,
    IRMatchArm,
)


@dataclass
class LinearViolation:
    function_name: str
    parameter_name: str
    message: str


class LinearTypeChecker:
    """
    Statically analyzes function bodies to ensure linear and affine parameters
    are consumed according to their constraints.
    """

    def check_module(self, module: IRModule) -> list[LinearViolation]:
        violations: list[LinearViolation] = []
        for func in module.all_functions():
            violations.extend(self.check_function(func))
        return violations

    def check_function(self, func: IRFunction) -> list[LinearViolation]:
        if func.body is None:
            return []

        violations: list[LinearViolation] = []

        # Identify parameters with linear/affine constraints
        for param in func.params:
            is_linear = param.is_consumed or param.ir_type.is_linear
            is_affine = param.ir_type.is_affine

            if not (is_linear or is_affine):
                continue

            # Count usages in the body
            usage_count = self._count_usages(param.name, func.body)

            if is_linear and usage_count != 1:
                violations.append(
                    LinearViolation(
                        function_name=func.name,
                        parameter_name=param.name,
                        message=(
                            f"Linear parameter '{param.name}' must be consumed exactly once. "
                            f"Found {usage_count} usage(s)."
                        ),
                    )
                )
            elif is_affine and usage_count > 1:
                violations.append(
                    LinearViolation(
                        function_name=func.name,
                        parameter_name=param.name,
                        message=(
                            f"Affine parameter '{param.name}' must be consumed at most once. "
                            f"Found {usage_count} usage(s)."
                        ),
                    )
                )

        return violations

    def _count_usages(self, param_name: str, expr: IRExpr) -> int:
        """Walk the IRExpr tree and count occurrences of param_name as a consumed variable."""
        count = 0

        match expr.kind:
            case IRExprKind.VARIABLE:
                if expr.variable_name == param_name:
                    count += 1

            case IRExprKind.FIELD_ACCESS:
                if expr.object_expr is not None:
                    count += self._count_usages(param_name, expr.object_expr)

            case IRExprKind.CONSTRUCTOR:
                for arg in expr.constructor_args:
                    count += self._count_usages(param_name, arg)

            case IRExprKind.FUNCTION_CALL:
                for arg in expr.call_args:
                    count += self._count_usages(param_name, arg)

            case IRExprKind.BINARY_OP:
                if expr.left is not None:
                    count += self._count_usages(param_name, expr.left)
                if expr.right is not None:
                    count += self._count_usages(param_name, expr.right)

            case IRExprKind.STRING_FORMAT:
                for arg in expr.format_args:
                    count += self._count_usages(param_name, arg)

            case IRExprKind.MATCH:
                # Count in match expression itself
                if expr.match_expr is not None:
                    count += self._count_usages(param_name, expr.match_expr)

                # For match arms, we branch. Under strict linear logic, a variable
                # must be consumed in ALL branches of a match.
                # So we sum usages across arms, but wait:
                # In standard linear logic, if it is consumed in one arm, it must
                # be consumed in all. If it's consumed in any arm, we count the max
                # or enforce consistency.
                # Let's count usage per arm and check for consistency, or just return
                # the maximum usage in any branch.
                arm_counts = []
                for arm in expr.match_arms:
                    # If param_name is bound in the pattern, it is shadowed inside this arm,
                    # so usages inside this arm don't count towards the original parameter.
                    if param_name in arm.pattern.bindings:
                        arm_counts.append(0)
                    else:
                        arm_counts.append(self._count_usages(param_name, arm.body))

                if arm_counts:
                    # Enforce that usage is uniform across all branches (INV_MIR_02/03 related consistency)
                    first = arm_counts[0]
                    if any(c != first for c in arm_counts):
                        # Non-uniform consumption is a violation. Let's return a special number to trigger error.
                        return -99  # Special marker for non-uniform branch consumption
                    count += first

            case IRExprKind.BLOCK:
                for stmt in expr.statements:
                    count += self._count_usages(param_name, stmt)

            case _:
                pass

        return count
