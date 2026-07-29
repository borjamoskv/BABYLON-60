#!/usr/bin/env python3
# tests/test_causal_isomorphism.py — C5-REAL Verification Suite
# Author: Borja Moskv (borjamoskv)
"""
Verification suite for the Causal Isomorphism Transpiler.

Tests the full pipeline: F# parse → IR → regime validation → {Solidity, Rust} emit.
Uses the actual IRPAutomata.fs from domain_kernel/ as ground truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

from causal_isomorphism.ir import (
    IR_FLOAT,
    IR_STRING,
    FunctionClassification,
    IRDiscriminatedUnion,
    IRModule,
    IRType,
    IRTypeKind,
    IRUnionCase,
    RegimeLayer,
)
from causal_isomorphism.parser_fsharp import FSharpParser, resolve_fsharp_type
from causal_isomorphism.emitter_solidity import SolidityEmitter, ir_type_to_solidity
from causal_isomorphism.emitter_rust import RustEmitter, ir_type_to_rust
from causal_isomorphism.regime_validator import RegimeValidator, ViolationSeverity
from causal_isomorphism.transpiler import CausalIsomorphismTranspiler

# Raíz del repo para localizar fixtures (domain_kernel/) y artefactos generados.
# El paquete causal_isomorphism es importable vía `pythonpath = ["."]`
# en pyproject [tool.pytest.ini_options] — no hace falta manipular sys.path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# UNIT TESTS: TYPE RESOLUTION
# ============================================================
def test_fsharp_type_resolution() -> None:
    """Verify F# type strings resolve to correct IR types."""
    assert resolve_fsharp_type("float").kind == IRTypeKind.FLOAT
    assert resolve_fsharp_type("string").kind == IRTypeKind.STRING
    assert resolve_fsharp_type("int").kind == IRTypeKind.INT
    assert resolve_fsharp_type("bool").kind == IRTypeKind.BOOL
    assert resolve_fsharp_type("unit").kind == IRTypeKind.UNIT
    assert resolve_fsharp_type("MembraneState").kind == IRTypeKind.CUSTOM
    assert resolve_fsharp_type("MembraneState").custom_name == "MembraneState"
    print("  ✅ F# type resolution")


def test_solidity_type_mapping() -> None:
    """Verify IR → Solidity type mapping."""
    assert ir_type_to_solidity(IR_FLOAT) == "uint256"
    assert ir_type_to_solidity(IR_STRING) == "string"
    assert ir_type_to_solidity(IRType(IRTypeKind.BOOL)) == "bool"
    assert ir_type_to_solidity(IRType(IRTypeKind.CUSTOM, custom_name="Gravity")) == "Gravity"
    print("  ✅ Solidity type mapping")


def test_rust_type_mapping() -> None:
    """Verify IR → Rust type mapping."""
    assert ir_type_to_rust(IR_FLOAT) == "f64"
    assert ir_type_to_rust(IR_STRING) == "String"
    assert ir_type_to_rust(IRType(IRTypeKind.BOOL)) == "bool"
    assert ir_type_to_rust(IRType(IRTypeKind.CUSTOM, custom_name="Gravity")) == "Gravity"
    print("  ✅ Rust type mapping")


# ============================================================
# UNIT TESTS: F# PARSER
# ============================================================
def test_parse_simple_union() -> None:
    """Parse a simple discriminated union (no payloads)."""
    source = """
module TestModule =
    type Gravity =
        | C5_ColapsoOntologico
        | C4_DegradacionGeometrica
        | C3_FluctuacionTermica
        | C2_FriccionComputacional
"""
    parser = FSharpParser()
    ir = parser.parse_source(source, "Test")

    assert len(ir.submodules) == 1, f"Expected 1 submodule, got {len(ir.submodules)}"
    sub = ir.submodules[0]
    assert sub.name == "TestModule"
    assert len(sub.unions) == 1
    union = sub.unions[0]
    assert union.name == "Gravity"
    assert len(union.cases) == 4
    assert union.is_simple_enum
    assert union.cases[0].name == "C5_ColapsoOntologico"
    assert union.cases[3].name == "C2_FriccionComputacional"
    print("  ✅ Simple union parsing")


def test_parse_tagged_union() -> None:
    """Parse a tagged discriminated union (with payloads)."""
    source = """
module TestModule =
    type MembraneState =
        | Stable of entropyLevel: float
        | Smoothing of variance: float
        | Rollback of targetHash: string
        | Apoptosis of taintLog: string
"""
    parser = FSharpParser()
    ir = parser.parse_source(source, "Test")

    sub = ir.submodules[0]
    assert len(sub.unions) == 1
    union = sub.unions[0]
    assert union.name == "MembraneState"
    assert not union.is_simple_enum
    assert union.has_numeric_payload
    assert union.has_string_payload
    assert len(union.cases) == 4
    assert union.cases[0].name == "Stable"
    assert len(union.cases[0].payload_fields) == 1
    assert union.cases[0].payload_fields[0][0] == "entropyLevel"
    assert union.cases[0].payload_fields[0][1].kind == IRTypeKind.FLOAT
    print("  ✅ Tagged union parsing")


def test_parse_record_type() -> None:
    """Parse an F# record type."""
    source = """
module TestModule =
    type StateNode = {
        NodeId: string
        ParentId: string
        ClaimSummary: string
        PayloadHash: string
    }
"""
    parser = FSharpParser()
    ir = parser.parse_source(source, "Test")

    sub = ir.submodules[0]
    assert len(sub.records) == 1
    record = sub.records[0]
    assert record.name == "StateNode"
    assert len(record.fields) == 4
    assert record.fields[0].name == "NodeId"
    assert record.fields[0].ir_type.kind == IRTypeKind.STRING
    print("  ✅ Record type parsing")


def test_parse_function_with_match() -> None:
    """Parse a function with pattern matching."""
    source = """
module TestModule =
    type Gravity =
        | C5_ColapsoOntologico
        | C2_FriccionComputacional

    type MembraneState =
        | Stable of entropyLevel: float
        | Apoptosis of taintLog: string

    let applyThermalStress (currentState: MembraneState) (gravity: Gravity) : MembraneState =
        match gravity with
        | C2_FriccionComputacional ->
            Stable 0.01
        | C5_ColapsoOntologico ->
            Apoptosis "TAINT:C5_REAL_TRUNCATED"
"""
    parser = FSharpParser()
    ir = parser.parse_source(source, "Test")

    sub = ir.submodules[0]
    assert len(sub.functions) >= 1
    func = sub.functions[0]
    assert func.name == "applyThermalStress"
    assert func.classification == FunctionClassification.STATE_TRANSITION
    assert len(func.params) == 2
    print("  ✅ Function with pattern matching")


# ============================================================
# UNIT TESTS: REGIME VALIDATOR
# ============================================================
def test_regime_blocks_physics_in_solidity() -> None:
    """Verify that STATE_TRANSITION functions are blocked for Solidity."""
    from causal_isomorphism.ir import IRFunction, IRParam, ir_custom

    func = IRFunction(
        name="applyThermalStress",
        params=[
            IRParam(name="state", ir_type=ir_custom("MembraneState")),
            IRParam(name="gravity", ir_type=ir_custom("Gravity")),
        ],
        return_type=ir_custom("MembraneState"),
        classification=FunctionClassification.STATE_TRANSITION,
    )

    module = IRModule(
        name="Test",
        source_layer=RegimeLayer.ONTOLOGY,
        functions=[func],
    )

    validator = RegimeValidator()
    report = validator.validate(module, RegimeLayer.CONSENSUS)

    assert "applyThermalStress" in report.blocked_functions
    assert len(report.violations) >= 1
    assert report.violations[0].severity == ViolationSeverity.ERROR
    assert "Physics" in report.violations[0].message or "physics" in report.violations[0].message.lower()
    print("  ✅ Regime blocks physics in Solidity")


def test_regime_permits_commit_in_solidity() -> None:
    """Verify that COMMIT_BOUNDARY functions are permitted for Solidity."""
    from causal_isomorphism.ir import IRFunction, IRParam, ir_custom

    func = IRFunction(
        name="commitBoundary",
        params=[IRParam(name="state", ir_type=ir_custom("MembraneState"))],
        return_type=IR_STRING,
        classification=FunctionClassification.COMMIT_BOUNDARY,
    )

    module = IRModule(
        name="Test",
        source_layer=RegimeLayer.ONTOLOGY,
        functions=[func],
    )

    validator = RegimeValidator()
    report = validator.validate(module, RegimeLayer.CONSENSUS)

    assert "commitBoundary" in report.permitted_functions
    print("  ✅ Regime permits commit in Solidity")


def test_regime_blocks_hash_in_solidity() -> None:
    """Verify HASH_COMPUTATION functions are blocked for Solidity."""
    from causal_isomorphism.ir import IRFunction

    func = IRFunction(
        name="computeTaint",
        classification=FunctionClassification.HASH_COMPUTATION,
    )

    module = IRModule(name="Test", functions=[func])
    validator = RegimeValidator()
    report = validator.validate(module, RegimeLayer.CONSENSUS)

    assert "computeTaint" in report.blocked_functions
    print("  ✅ Regime blocks hash computation in Solidity")


def test_regime_permits_hash_in_rust() -> None:
    """Verify HASH_COMPUTATION is permitted for Rust."""
    from causal_isomorphism.ir import IRFunction

    func = IRFunction(
        name="computeTaint",
        classification=FunctionClassification.HASH_COMPUTATION,
    )

    module = IRModule(name="Test", functions=[func])
    validator = RegimeValidator()
    report = validator.validate(module, RegimeLayer.THERMODYNAMICS)

    assert "computeTaint" in report.permitted_functions
    print("  ✅ Regime permits hash computation in Rust")


# ============================================================
# UNIT TESTS: EMITTERS
# ============================================================
def test_solidity_emitter_simple_enum() -> None:
    """Emit a simple enum to Solidity."""
    union = IRDiscriminatedUnion(
        name="Gravity",
        cases=[
            IRUnionCase(name="C5_ColapsoOntologico"),
            IRUnionCase(name="C4_DegradacionGeometrica"),
            IRUnionCase(name="C3_FluctuacionTermica"),
            IRUnionCase(name="C2_FriccionComputacional"),
        ],
    )
    module = IRModule(name="Test", unions=[union])
    emitter = SolidityEmitter()
    output = emitter.emit_module(module)

    assert "enum Gravity" in output
    assert "C5_ColapsoOntologico" in output
    assert "C2_FriccionComputacional" in output
    assert "pragma solidity ^0.8.19" in output
    print("  ✅ Solidity simple enum emission")


def test_solidity_emitter_tagged_union() -> None:
    """Emit a tagged union to Solidity."""
    union = IRDiscriminatedUnion(
        name="MembraneState",
        cases=[
            IRUnionCase(name="Stable", payload_fields=[("entropyLevel", IR_FLOAT)]),
            IRUnionCase(name="Smoothing", payload_fields=[("variance", IR_FLOAT)]),
            IRUnionCase(name="Rollback", payload_fields=[("targetHash", IR_STRING)]),
            IRUnionCase(name="Apoptosis", payload_fields=[("taintLog", IR_STRING)]),
        ],
    )
    module = IRModule(name="Test", unions=[union])
    emitter = SolidityEmitter()
    output = emitter.emit_module(module)

    assert "enum MembraneStateTag" in output
    assert "struct MembraneState" in output
    assert "uint256 numericPayload" in output
    assert "string stringPayload" in output
    print("  ✅ Solidity tagged union emission")


def test_rust_emitter_enum() -> None:
    """Emit a discriminated union to Rust."""
    union = IRDiscriminatedUnion(
        name="Gravity",
        cases=[
            IRUnionCase(name="C5_ColapsoOntologico"),
            IRUnionCase(name="C2_FriccionComputacional"),
        ],
    )
    module = IRModule(name="Test", unions=[union])
    emitter = RustEmitter()
    output = emitter.emit_module(module)

    assert "pub enum Gravity" in output
    assert "C5_ColapsoOntologico" in output
    assert "#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]" in output
    assert "use blake3::Hasher;" in output
    print("  ✅ Rust enum emission")


def test_rust_emitter_taint_trait() -> None:
    """Verify CortexTaint trait is generated for tagged unions."""
    union = IRDiscriminatedUnion(
        name="MembraneState",
        cases=[
            IRUnionCase(name="Stable", payload_fields=[("entropyLevel", IR_FLOAT)]),
            IRUnionCase(name="Apoptosis", payload_fields=[("taintLog", IR_STRING)]),
        ],
    )
    module = IRModule(name="Test", unions=[union])
    emitter = RustEmitter()
    output = emitter.emit_module(module)

    assert "pub trait CortexTaint" in output
    assert "impl CortexTaint for MembraneState" in output
    assert "fn compute_taint(&self) -> String" in output
    assert "TAINT:C5_REAL_RUST" in output
    print("  ✅ Rust CortexTaint trait generation")


# ============================================================
# INTEGRATION TEST: FULL PIPELINE ON ACTUAL IRPAUTOMATA.FS
# ============================================================
def test_full_pipeline_irpautomata() -> None:
    """Run the full transpilation pipeline on the actual IRPAutomata.fs."""
    source_path = PROJECT_ROOT / "domain_kernel" / "IRPAutomata.fs"
    if not source_path.exists():
        print(f"  ⚠️  Skipping: {source_path} not found")
        return

    output_dir = PROJECT_ROOT / "causal_isomorphism" / "generated"

    transpiler = CausalIsomorphismTranspiler()
    result = transpiler.transpile_file(source_path, output_dir)

    # Verify IR extraction
    assert result.ir_module.name in ("Domain", "IRPAutomata")
    all_unions = result.ir_module.all_types()
    union_names = [u.name for u in all_unions if isinstance(u, IRDiscriminatedUnion)]
    assert "Gravity" in union_names, f"Gravity not found in {union_names}"
    assert "MembraneState" in union_names, f"MembraneState not found in {union_names}"

    # Verify Solidity output
    assert "pragma solidity" in result.solidity_output
    assert "enum Gravity" in result.solidity_output
    assert "C5_ColapsoOntologico" in result.solidity_output

    # Verify regime: physics blocked in Solidity
    assert "applyThermalStress" in result.solidity_report.blocked_functions

    # Verify Rust output
    assert "pub enum Gravity" in result.rust_output
    assert "blake3" in result.rust_output

    # Verify files written
    assert Path(result.solidity_path).exists()
    assert Path(result.rust_path).exists()
    assert Path(result.report_path).exists()

    # Print report
    print(result.full_report())
    print("  ✅ Full pipeline on IRPAutomata.fs")


def test_linear_type_checker() -> None:
    """Verify linear and affine type checker rules."""
    from causal_isomorphism.ir import (
        IRFunction,
        IRParam,
        IRType,
        IRTypeKind,
        IRExpr,
        IRExprKind,
        IRMatchArm,
        IRPattern,
    )
    from causal_isomorphism.linear_checker import LinearTypeChecker

    # 1. Valid Linear: consumed exactly once
    p1 = IRParam(
        name="x",
        ir_type=IRType(IRTypeKind.INT, is_linear=True),
    )
    # Body: just return x (variable access)
    body1 = IRExpr(kind=IRExprKind.VARIABLE, variable_name="x")
    f1 = IRFunction(name="f1", params=[p1], body=body1)

    checker = LinearTypeChecker()
    violations = checker.check_function(f1)
    assert not violations, f"Expected no violations, got: {violations}"

    # 2. Invalid Linear: consumed zero times
    body2 = IRExpr(kind=IRExprKind.LITERAL, literal_value="42", literal_type=IR_FLOAT)
    f2 = IRFunction(name="f2", params=[p1], body=body2)
    violations = checker.check_function(f2)
    assert len(violations) == 1
    assert "must be consumed exactly once" in violations[0].message
    assert "Found 0" in violations[0].message

    # 3. Invalid Linear: consumed twice
    body3 = IRExpr(
        kind=IRExprKind.BINARY_OP,
        op="+",
        left=IRExpr(kind=IRExprKind.VARIABLE, variable_name="x"),
        right=IRExpr(kind=IRExprKind.VARIABLE, variable_name="x"),
    )
    f3 = IRFunction(name="f3", params=[p1], body=body3)
    violations = checker.check_function(f3)
    assert len(violations) == 1
    assert "Found 2" in violations[0].message

    # 4. Valid Affine: consumed once
    p2 = IRParam(
        name="y",
        ir_type=IRType(IRTypeKind.INT, is_affine=True),
    )
    f4 = IRFunction(name="f4", params=[p2], body=body1)  # body1 consumes x, but we need y
    body4 = IRExpr(kind=IRExprKind.VARIABLE, variable_name="y")
    f4 = IRFunction(name="f4", params=[p2], body=body4)
    violations = checker.check_function(f4)
    assert not violations

    # 5. Valid Affine: consumed zero times (affine allows 0 or 1)
    f5 = IRFunction(name="f5", params=[p2], body=body2)
    violations = checker.check_function(f5)
    assert not violations

    # 6. Invalid Affine: consumed twice
    body6 = IRExpr(
        kind=IRExprKind.BINARY_OP,
        op="+",
        left=IRExpr(kind=IRExprKind.VARIABLE, variable_name="y"),
        right=IRExpr(kind=IRExprKind.VARIABLE, variable_name="y"),
    )
    f6 = IRFunction(name="f6", params=[p2], body=body6)
    violations = checker.check_function(f6)
    assert len(violations) == 1

    # 7. Non-uniform consumption in Match arms: x consumed in one branch but not another
    arm1 = IRMatchArm(
        pattern=IRPattern(case_name="A"),
        body=IRExpr(kind=IRExprKind.VARIABLE, variable_name="x"),
    )
    arm2 = IRMatchArm(
        pattern=IRPattern(case_name="B"),
        body=body2,  # literal 42
    )
    body7 = IRExpr(
        kind=IRExprKind.MATCH,
        match_expr=IRExpr(kind=IRExprKind.VARIABLE, variable_name="state"),
        match_arms=[arm1, arm2],
    )
    f7 = IRFunction(name="f7", params=[p1], body=body7)
    violations = checker.check_function(f7)
    assert len(violations) == 1

    print("  ✅ Linear type checker logic")


# ============================================================
# RUNNER
# ============================================================
def main() -> int:
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  CAUSAL ISOMORPHISM TRANSPILER — VERIFICATION SUITE    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    test_groups: list[tuple[str, list[object]]] = [
        (
            "Type Resolution",
            [
                test_fsharp_type_resolution,
                test_solidity_type_mapping,
                test_rust_type_mapping,
            ],
        ),
        (
            "F# Parser",
            [
                test_parse_simple_union,
                test_parse_tagged_union,
                test_parse_record_type,
                test_parse_function_with_match,
            ],
        ),
        (
            "Regime Validator",
            [
                test_regime_blocks_physics_in_solidity,
                test_regime_permits_commit_in_solidity,
                test_regime_blocks_hash_in_solidity,
                test_regime_permits_hash_in_rust,
            ],
        ),
        (
            "Emitters",
            [
                test_solidity_emitter_simple_enum,
                test_solidity_emitter_tagged_union,
                test_rust_emitter_enum,
                test_rust_emitter_taint_trait,
            ],
        ),
        (
            "Linear Type Checker",
            [
                test_linear_type_checker,
            ],
        ),
        (
            "Integration",
            [
                test_full_pipeline_irpautomata,
            ],
        ),
    ]

    total = 0
    passed = 0
    failed = 0

    for group_name, tests in test_groups:
        print(f"\n── {group_name} ──")
        for test_fn in tests:
            total += 1
            try:
                test_fn()  # type: ignore[operator]
                passed += 1
            except Exception as e:
                failed += 1
                name = getattr(test_fn, "__name__", str(test_fn))
                print(f"  ❌ {name}: {e}")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")

    if failed == 0:
        print("✅ ALL TESTS PASSED — C5-REAL VERIFIED")
    else:
        print("❌ FAILURES DETECTED")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
