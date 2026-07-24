# C5-REAL: Static analysis pass for linear/affine/region constraints
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

from dataclasses import dataclass

from causal_isomorphism.ir import (
    IRExpr,
    IRExprKind,
    IRFunction,
    IRModule,
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

        for param in func.params:
            is_linear = param.is_consumed or param.ir_type.is_linear
            is_affine = param.ir_type.is_affine

            if not (is_linear or is_affine):
                continue

            usages = self._get_usage_paths(param.name, func.body)

            if is_linear:
                if usages != {1}:
                    if len(usages) == 1:
                        found_str = f"{next(iter(usages))}"
                    else:
                        found_str = f"{sorted(list(usages))} across paths"
                    violations.append(
                        LinearViolation(
                            function_name=func.name,
                            parameter_name=param.name,
                            message=(
                                f"Linear parameter '{param.name}' must be consumed exactly once. "
                                f"Found {found_str} usage(s)."
                            ),
                        )
                    )
            elif is_affine:
                if any(u > 1 for u in usages):
                    if len(usages) == 1:
                        found_str = f"{next(iter(usages))}"
                    else:
                        found_str = f"{sorted(list(usages))} across paths"
                    violations.append(
                        LinearViolation(
                            function_name=func.name,
                            parameter_name=param.name,
                            message=(
                                f"Affine parameter '{param.name}' must be consumed at most once. "
                                f"Found {found_str} usage(s)."
                            ),
                        )
                    )

        return violations

    def _add_sets(self, s1: set[int], s2: set[int]) -> set[int]:
        return {x + y for x in s1 for y in s2}

    def _get_usage_paths(self, param_name: str, expr: IRExpr) -> set[int]:
        """Walk the IRExpr tree and return a set of possible consumption counts across all execution paths."""
        match expr.kind:
            case IRExprKind.VARIABLE:
                if expr.variable_name == param_name:
                    return {1}
                return {0}

            case IRExprKind.FIELD_ACCESS:
                if expr.object_expr is not None:
                    return self._get_usage_paths(param_name, expr.object_expr)
                return {0}

            case IRExprKind.CONSTRUCTOR:
                current = {0}
                for arg in expr.constructor_args:
                    current = self._add_sets(current, self._get_usage_paths(param_name, arg))
                return current

            case IRExprKind.FUNCTION_CALL:
                current = {0}
                for arg in expr.call_args:
                    current = self._add_sets(current, self._get_usage_paths(param_name, arg))
                return current

            case IRExprKind.BINARY_OP:
                left_usages = self._get_usage_paths(param_name, expr.left) if expr.left is not None else {0}
                right_usages = self._get_usage_paths(param_name, expr.right) if expr.right is not None else {0}
                return self._add_sets(left_usages, right_usages)

            case IRExprKind.STRING_FORMAT:
                current = {0}
                for arg in expr.format_args:
                    current = self._add_sets(current, self._get_usage_paths(param_name, arg))
                return current

            case IRExprKind.MATCH:
                match_expr_usages = (
                    self._get_usage_paths(param_name, expr.match_expr) if expr.match_expr is not None else {0}
                )

                arm_usages: set[int] = set()
                for arm in expr.match_arms:
                    if param_name in arm.pattern.bindings:
                        arm_usages.add(0)
                    else:
                        arm_usages.update(self._get_usage_paths(param_name, arm.body))

                if not arm_usages:
                    arm_usages = {0}

                return self._add_sets(match_expr_usages, arm_usages)

            case IRExprKind.BLOCK:
                current = {0}
                for stmt in expr.statements:
                    current = self._add_sets(current, self._get_usage_paths(param_name, stmt))
                return current

            case _:
                return {0}
