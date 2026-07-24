# C5-REAL: Regime-filtered Solidity code generation
"""
Emits Solidity 0.8.19+ contracts from IR modules.

REGIME ENFORCEMENT:
  - TYPE_DEFINITION: ✅ Emits enums and structs
  - STATE_STORAGE: ✅ Emits contract storage variables
  - EVENT_EMISSION: ✅ Emits events for state transitions
  - COMMIT_ANCHOR: ✅ Emits commitState/logApoptosis functions
  - VALIDATION_GUARD: ✅ Emits require() from Result<T,E> validators
  - PURE_QUERY: ✅ Emits view/pure query functions
  - PHYSICS_COMPUTATION: ❌ BLOCKED — transitions stay in F#
  - POSET_OPERATION: ❌ BLOCKED — DAG/hash stays in Rust

The emitter generates contracts that anchor ontological state on-chain
without computing the physics of state transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from causal_isomorphism.ir import (
    EmitPermission,
    FunctionClassification,
    IRDiscriminatedUnion,
    IRExprKind,
    IRFunction,
    IRModule,
    IRParam,
    IRRecordType,
    IRType,
    IRTypeKind,
    REGIME_PERMISSIONS,
    RegimeLayer,
)


def ir_type_to_solidity(ir_type: IRType) -> str:
    """Map an IR type to its Solidity equivalent."""
    match ir_type.kind:
        case IRTypeKind.FLOAT:
            return "uint256"  # Fixed-point scaled (1e18)
        case IRTypeKind.INT:
            return "uint256"
        case IRTypeKind.STRING:
            return "string"
        case IRTypeKind.BOOL:
            return "bool"
        case IRTypeKind.UNIT:
            return ""  # void
        case IRTypeKind.BYTES:
            return "bytes32"
        case IRTypeKind.CUSTOM:
            return ir_type.custom_name
        case IRTypeKind.MAP:
            if len(ir_type.type_params) == 2:
                k = ir_type_to_solidity(ir_type.type_params[0])
                v = ir_type_to_solidity(ir_type.type_params[1])
                return f"mapping({k} => {v})"
            return "mapping(bytes32 => bytes32)"
        case _:
            return "bytes32"


@dataclass
class SolidityEmitter:
    """
    Emits Solidity contracts from IR modules.

    Enforces the Trilingual Regime by filtering out functions
    classified as PHYSICS_COMPUTATION or POSET_OPERATION.
    """

    indent: int = 0
    lines: list[str] = field(default_factory=list)
    _emitted_enums: set[str] = field(default_factory=set)
    _emitted_structs: set[str] = field(default_factory=set)

    _permissions: frozenset[EmitPermission] = REGIME_PERMISSIONS[RegimeLayer.CONSENSUS]

    def emit_module(self, module: IRModule) -> str:
        """Emit a complete Solidity contract from an IR module."""
        self.lines = []
        self._emitted_enums = set()
        self._emitted_structs = set()
        self.indent = 0

        self._line("// SPDX-License-Identifier: MIT")
        self._line("pragma solidity ^0.8.19;")
        self._line("")
        self._line(f"/// @title {module.name} (Auto-generated from F# Domain Kernel)")
        self._line("/// @dev Causal Isomorphism Transpiler — Trilingual Regime")
        self._line("/// @notice TYPE DEFINITIONS and CONSENSUS ANCHORING only.")
        self._line("/// @notice Physics computation stays in F# Domain Kernel.")
        self._line("/// @author borjamoskv")

        contract_name = self._sanitize_name(module.name) + "Anchor"
        self._line(f"contract {contract_name} {{")
        self.indent += 1

        for union in module.unions:
            self._emit_union(union)

        for sub in module.submodules:
            for union in sub.unions:
                self._emit_union(union)

        for record in module.records:
            self._emit_record(record)

        for sub in module.submodules:
            for record in sub.records:
                self._emit_record(record)

        self._emit_state_storage(module)

        self._emit_events(module)

        for func in module.all_functions():
            self._emit_function(func)

        self.indent -= 1
        self._line("}")

        return "\n".join(self.lines)

    def _emit_union(self, union: IRDiscriminatedUnion) -> None:
        """Emit a discriminated union as Solidity enum + optional struct."""
        if union.name in self._emitted_enums:
            return
        self._emitted_enums.add(union.name)

        self._line("")

        if union.is_simple_enum:
            self._line(f"enum {union.name} {{")
            self.indent += 1
            for i, case in enumerate(union.cases):
                comma = "," if i < len(union.cases) - 1 else ""
                self._line(f"{case.name}{comma}")
            self.indent -= 1
            self._line("}")
        else:
            tag_name = f"{union.name}Tag"
            self._line(f"enum {tag_name} {{")
            self.indent += 1
            for i, case in enumerate(union.cases):
                comma = "," if i < len(union.cases) - 1 else ""
                self._line(f"{case.name}{comma}")
            self.indent -= 1
            self._line("}")
            self._line("")

            self._line(f"struct {union.name} {{")
            self.indent += 1
            self._line(f"{tag_name} tag;")

            if union.has_numeric_payload:
                self._line("uint256 numericPayload;  // Scaled 1e18 for float precision")
            if union.has_string_payload:
                self._line("string stringPayload;")

            self.indent -= 1
            self._line("}")

    def _emit_record(self, record: IRRecordType) -> None:
        """Emit a record type as a Solidity struct."""
        if record.name in self._emitted_structs:
            return
        self._emitted_structs.add(record.name)

        self._line("")
        self._line(f"struct {record.name} {{")
        self.indent += 1
        for fld in record.fields:
            sol_type = ir_type_to_solidity(fld.ir_type)
            self._line(f"{sol_type} {fld.name};")
        self.indent -= 1
        self._line("}")

    def _emit_state_storage(self, module: IRModule) -> None:
        """Emit contract storage variables for stateful unions."""
        self._line("")
        self._line("// ---- State Storage ----")

        for union in module.unions:
            if not union.is_simple_enum:
                var_name = self._camel_case(union.name)
                self._line(f"{union.name} public {var_name};")

        self._line("string public currentHead;")
        self._line("uint256 public latentSteps;")
        self._line("address public owner;")

    def _emit_events(self, module: IRModule) -> None:
        """Emit events for state transitions and anchoring."""
        self._line("")
        self._line("// ---- Events ----")

        for union in module.unions:
            if not union.is_simple_enum:
                self._line(
                    f"event {union.name}Committed("
                    f"{union.name}Tag indexed prevTag, "
                    f"{union.name}Tag indexed newTag, "
                    f"uint256 latentSteps);"
                )

        self._line("event StateAnchored(string prevHead, string newHead, uint256 steps);")
        self._line("event ApoptosisLogged(string taint, string reason);")

        self._line("")
        self._line("// ---- Constructor ----")
        self._line("constructor(string memory genesisHash) {")
        self.indent += 1
        self._line("currentHead = genesisHash;")
        self._line("latentSteps = 0;")
        self._line("owner = msg.sender;")
        self.indent -= 1
        self._line("}")

    def _emit_function(self, func: IRFunction) -> None:
        """Emit a function, respecting regime boundaries."""
        if func.classification == FunctionClassification.STATE_TRANSITION:
            self._line("")
            self._line(f"// @regime-blocked: {func.name}")
            self._line("// Classification: STATE_TRANSITION — physics computation stays in F# Domain Kernel.")
            self._line("// The off-chain F# kernel computes the transition and calls commitState() with the result.")
            return

        if func.classification == FunctionClassification.HASH_COMPUTATION:
            self._line("")
            self._line(f"// @regime-blocked: {func.name}")
            self._line("// Classification: HASH_COMPUTATION — BLAKE3/DAG operations stay in Rust strike_rs.")
            return

        if func.classification == FunctionClassification.COMMIT_BOUNDARY:
            self._emit_commit_function(func)
            return

        if func.classification == FunctionClassification.VALIDATION:
            self._emit_validation_function(func)
            return

        if func.classification == FunctionClassification.PURE_QUERY:
            self._emit_query_function(func)
            return

    def _emit_commit_function(self, func: IRFunction) -> None:
        """Emit a commit/anchor function for the EVM layer."""
        self._line("")
        self._line(f"/// @notice {func.name} — Anchors computed state from F# Domain Kernel")
        self._line("/// @dev Off-chain F# computes transition; this function anchors the result on-chain")

        params_sol = self._format_params(func.params)
        self._line(f"function {func.name}({params_sol}) external {{")
        self.indent += 1

        if func.body is not None and func.body.kind == IRExprKind.MATCH:
            self._emit_commit_match_body(func)
        else:
            self._line("// Commit boundary — anchor the computed state")
            self._line("string memory prev = currentHead;")
            self._line("// State mutation anchored here")
            self._line("emit StateAnchored(prev, currentHead, latentSteps);")

        self.indent -= 1
        self._line("}")

    def _emit_commit_match_body(self, func: IRFunction) -> None:
        """Emit commit boundary with match-based serialization."""
        self._line("// State serialization from F# commitBoundary")
        if func.body is None:
            return

        for arm in func.body.match_arms:
            tag = arm.pattern.case_name
            if arm.body is not None and arm.body.kind == IRExprKind.STRING_FORMAT:
                fmt = arm.body.format_string
                self._line(f'// {tag}: "{fmt}"')

        self._line("string memory prev = currentHead;")
        self._line("latentSteps += 1;")
        self._line("emit StateAnchored(prev, currentHead, latentSteps);")

    def _emit_validation_function(self, func: IRFunction) -> None:
        """Emit a validation function with require() guards."""
        self._line("")
        self._line(f"/// @notice {func.name} — Validation guard (from F# Result<T,E>)")

        params_sol = self._format_params(func.params)
        ret_type = ir_type_to_solidity(func.return_type) if func.return_type.kind != IRTypeKind.UNIT else ""
        returns = f" returns ({ret_type})" if ret_type else ""

        self._line(f"function {func.name}({params_sol}) internal pure{returns} {{")
        self.indent += 1

        if func.body is not None and func.body.kind == IRExprKind.MATCH:
            for arm in func.body.match_arms:
                if arm.body is not None and arm.body.kind == IRExprKind.RETURN_ERROR:
                    error_name = arm.pattern.case_name
                    self._line(f'require(false, "{error_name}");')

        self._line("// Validation passed")
        self.indent -= 1
        self._line("}")

    def _emit_query_function(self, func: IRFunction) -> None:
        """Emit a read-only query function."""
        self._line("")
        self._line(f"/// @notice {func.name} — Pure query function")

        params_sol = self._format_params(func.params)
        ret_type = ir_type_to_solidity(func.return_type)
        if not ret_type:
            ret_type = "string memory"

        self._line(f"function {func.name}({params_sol}) public view returns ({ret_type}) {{")
        self.indent += 1
        self._line("return currentHead;")
        self.indent -= 1
        self._line("}")

    def _format_params(self, params: list[IRParam]) -> str:
        """Format function parameters for Solidity."""
        parts: list[str] = []
        for p in params:
            sol_type = ir_type_to_solidity(p.ir_type)
            if sol_type == "string":
                parts.append(f"string calldata {p.name}")
            elif sol_type.startswith("mapping"):
                continue  # Mappings can't be function params
            else:
                parts.append(f"{sol_type} {p.name}")
        return ", ".join(parts)

    def _line(self, text: str) -> None:
        """Add an indented line."""
        prefix = "    " * self.indent
        self.lines.append(f"{prefix}{text}")

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize an F# module name for Solidity."""
        return name.replace(".", "_").replace("-", "_")

    @staticmethod
    def _camel_case(name: str) -> str:
        """Convert PascalCase to camelCase."""
        if not name:
            return name
        return name[0].lower() + name[1:]
