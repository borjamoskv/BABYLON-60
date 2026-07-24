# C5-REAL: Validates that emitted code respects the regime
"""
Validates that IR modules and emitted code respect the Trilingual Regime:

  F# (Ontology)     → Types, state machines, physics computation
  Rust (Thermo)     → Causal posets, DAGs, BLAKE3 hashing
  Solidity (Anvil)  → State anchoring, events, BFT consensus

Antipatterns (PROHIBITED):
  - Physics computation in Rust     → F# only
  - Physics computation in Solidity → F# only
  - Ontological type discrimination in Rust → F# only
  - Poset/DAG operations in Solidity → Rust only
  - Consensus anchoring in Rust → Solidity only
  - Direct Rust→Solidity writes bypassing F# → CommitBoundary violation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from causal_isomorphism.ir import (
    EmitPermission,
    FunctionClassification,
    IRModule,
    REGIME_PERMISSIONS,
    RegimeLayer,
)


class ViolationSeverity(Enum):
    ERROR = auto()    # Hard block — must not emit
    WARNING = auto()  # Soft block — emit with annotation


@dataclass
class RegimeViolation:
    """A detected regime boundary violation."""
    severity: ViolationSeverity
    source_layer: RegimeLayer
    target_layer: RegimeLayer
    construct_name: str
    rule: str
    message: str


@dataclass
class ValidationReport:
    """Complete validation report for a transpilation run."""
    violations: list[RegimeViolation] = field(default_factory=list)
    blocked_functions: list[str] = field(default_factory=list)
    permitted_functions: list[str] = field(default_factory=list)
    total_types: int = 0
    total_functions: int = 0

    @property
    def is_valid(self) -> bool:
        return not any(v.severity == ViolationSeverity.ERROR for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.WARNING)

    def summary(self) -> str:
        lines = [
            "=== Regime Validation Report ===",
            f"Types:     {self.total_types}",
            f"Functions: {self.total_functions}",
            f"  Permitted: {len(self.permitted_functions)}",
            f"  Blocked:   {len(self.blocked_functions)}",
            f"Violations: {len(self.violations)} ({self.error_count} errors, {self.warning_count} warnings)",
        ]
        if self.violations:
            lines.append("")
            for v in self.violations:
                prefix = "❌" if v.severity == ViolationSeverity.ERROR else "⚠️"
                lines.append(
                    f"  {prefix} [{v.source_layer.value}→{v.target_layer.value}] "
                    f"{v.construct_name}: {v.message} (Rule: {v.rule})"
                )
        if self.blocked_functions:
            lines.append("")
            lines.append("Blocked functions (regime-filtered):")
            for name in self.blocked_functions:
                lines.append(f"  🚫 {name}")
        if self.permitted_functions:
            lines.append("")
            lines.append("Permitted functions:")
            for name in self.permitted_functions:
                lines.append(f"  ✅ {name}")

        return "\n".join(lines)


CLASSIFICATION_PERMISSIONS: dict[FunctionClassification, EmitPermission] = {
    FunctionClassification.STATE_TRANSITION: EmitPermission.PHYSICS_COMPUTATION,
    FunctionClassification.COMMIT_BOUNDARY: EmitPermission.COMMIT_ANCHOR,
    FunctionClassification.VALIDATION: EmitPermission.VALIDATION_GUARD,
    FunctionClassification.PURE_QUERY: EmitPermission.PURE_QUERY,
    FunctionClassification.HASH_COMPUTATION: EmitPermission.POSET_OPERATION,
    FunctionClassification.EVENT_EMITTER: EmitPermission.EVENT_EMISSION,
}

REGIME_RULES: list[tuple[FunctionClassification, RegimeLayer, str]] = [
    (FunctionClassification.STATE_TRANSITION, RegimeLayer.THERMODYNAMICS,
     "ANTIPATTERN: Physics computation in Rust — must stay in F# Domain Kernel"),
    (FunctionClassification.STATE_TRANSITION, RegimeLayer.CONSENSUS,
     "ANTIPATTERN: Physics computation in Solidity — must stay in F# Domain Kernel"),
    (FunctionClassification.HASH_COMPUTATION, RegimeLayer.CONSENSUS,
     "ANTIPATTERN: BLAKE3/DAG operations in Solidity — must stay in Rust strike_rs"),
    (FunctionClassification.COMMIT_BOUNDARY, RegimeLayer.THERMODYNAMICS,
     "ANTIPATTERN: Consensus anchoring in Rust — must stay in Solidity/Anvil"),
    (FunctionClassification.EVENT_EMITTER, RegimeLayer.THERMODYNAMICS,
     "ANTIPATTERN: Event emission in Rust — must stay in Solidity/Anvil"),
]


class RegimeValidator:
    """
    Validates IR modules against the Trilingual Regime.

    Usage:
        validator = RegimeValidator()
        report = validator.validate(ir_module, target_layer=RegimeLayer.CONSENSUS)
    """

    def validate(self, module: IRModule, target_layer: RegimeLayer) -> ValidationReport:
        """Validate an IR module for emission to the target layer."""
        report = ValidationReport()
        target_permissions = REGIME_PERMISSIONS[target_layer]

        report.total_types = len(module.all_types())
        report.total_functions = len(module.all_functions())

        for func in module.all_functions():
            required_permission = CLASSIFICATION_PERMISSIONS.get(
                func.classification, EmitPermission.PURE_QUERY
            )

            if required_permission in target_permissions:
                report.permitted_functions.append(func.name)
            else:
                report.blocked_functions.append(func.name)

                for rule_class, rule_layer, rule_msg in REGIME_RULES:
                    if func.classification == rule_class and target_layer == rule_layer:
                        report.violations.append(RegimeViolation(
                            severity=ViolationSeverity.ERROR,
                            source_layer=module.source_layer,
                            target_layer=target_layer,
                            construct_name=func.name,
                            rule=f"{rule_class.name}→{rule_layer.value}",
                            message=rule_msg,
                        ))
                        break

        from causal_isomorphism.linear_checker import LinearTypeChecker
        checker = LinearTypeChecker()
        for viol in checker.check_module(module):
            report.violations.append(RegimeViolation(
                severity=ViolationSeverity.ERROR,
                source_layer=module.source_layer,
                target_layer=target_layer,
                construct_name=viol.function_name,
                rule="LinearTypeCheck",
                message=viol.message,
            ))

        return report

    def validate_cross_regime(
        self,
        module: IRModule,
        target_layers: list[RegimeLayer] | None = None,
    ) -> dict[RegimeLayer, ValidationReport]:
        """Validate an IR module against all target layers."""
        if target_layers is None:
            target_layers = [RegimeLayer.CONSENSUS, RegimeLayer.THERMODYNAMICS]

        return {layer: self.validate(module, layer) for layer in target_layers}
