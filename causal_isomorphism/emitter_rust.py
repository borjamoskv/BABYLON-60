# causal_isomorphism/emitter_rust.py — IR → Rust Emitter
# C5-REAL: Regime-filtered Rust code generation
# Author: Borja Moskv (borjamoskv)
"""
Emits Rust source from IR modules for the strike_rs poset layer.

REGIME ENFORCEMENT:
  - TYPE_DEFINITION: ✅ Emits enums and structs
  - POSET_OPERATION: ✅ Emits DAG/hash computation stubs
  - VALIDATION_GUARD: ✅ Emits Result<T,E> return types
  - PURE_QUERY: ✅ Emits read-only functions
  - PHYSICS_COMPUTATION: ❌ BLOCKED — transitions stay in F#
  - STATE_STORAGE: ❌ N/A — not a Rust concern
  - EVENT_EMISSION: ❌ N/A — not a Rust concern
  - COMMIT_ANCHOR: ❌ N/A — not a Rust concern

The emitter generates type-safe Rust structs and enums that mirror
the F# ontological types, plus trait implementations for BLAKE3 hashing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from causal_isomorphism.ir import (
    FunctionClassification,
    IRDiscriminatedUnion,
    IRFunction,
    IRModule,
    IRParam,
    IRRecordType,
    IRType,
    IRTypeKind,
)


# ============================================================
# TYPE MAPPING: IR → Rust
# ============================================================
def ir_type_to_rust(ir_type: IRType) -> str:
    """Map an IR type to its Rust equivalent."""
    match ir_type.kind:
        case IRTypeKind.FLOAT:
            return "f64"
        case IRTypeKind.INT:
            return "i64"
        case IRTypeKind.STRING:
            return "String"
        case IRTypeKind.BOOL:
            return "bool"
        case IRTypeKind.UNIT:
            return "()"
        case IRTypeKind.BYTES:
            return "Vec<u8>"
        case IRTypeKind.CUSTOM:
            return ir_type.custom_name
        case IRTypeKind.RESULT:
            if len(ir_type.type_params) == 2:
                ok = ir_type_to_rust(ir_type.type_params[0])
                err = ir_type_to_rust(ir_type.type_params[1])
                return f"Result<{ok}, {err}>"
            return "Result<(), String>"
        case IRTypeKind.MAP:
            if len(ir_type.type_params) == 2:
                k = ir_type_to_rust(ir_type.type_params[0])
                v = ir_type_to_rust(ir_type.type_params[1])
                return f"std::collections::HashMap<{k}, {v}>"
            return "std::collections::HashMap<String, String>"
        case IRTypeKind.LIST:
            if ir_type.type_params:
                inner = ir_type_to_rust(ir_type.type_params[0])
                return f"Vec<{inner}>"
            return "Vec<String>"
        case IRTypeKind.OPTION:
            if ir_type.type_params:
                inner = ir_type_to_rust(ir_type.type_params[0])
                return f"Option<{inner}>"
            return "Option<String>"
        case _:
            return "Vec<u8>"


# ============================================================
# RUST CODE GENERATION
# ============================================================
@dataclass
class RustEmitter:
    """
    Emits Rust source from IR modules for the strike_rs layer.

    Enforces the Trilingual Regime by blocking physics computation
    and emitting only type definitions and poset operation stubs.
    """
    indent: int = 0
    lines: list[str] = field(default_factory=list)

    def emit_module(self, module: IRModule) -> str:
        """Emit a Rust module from an IR module."""
        self.lines = []
        self.indent = 0

        # Header
        self._line("//! Auto-generated from F# Domain Kernel via Causal Isomorphism Transpiler")
        self._line("//! Trilingual Regime: Type definitions and poset stubs for strike_rs")
        self._line("//! Author: borjamoskv")
        self._line("//!")
        self._line("//! REGIME: Physics computation stays in F# Domain Kernel.")
        self._line("//! REGIME: Only type definitions and DAG/hash operations emitted here.")
        self._line("")
        self._line("use blake3::Hasher;")
        self._line("use serde::{Deserialize, Serialize};")
        self._line("")

        # Emit all type definitions
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

        # Emit BLAKE3 trait implementation
        self._emit_taint_trait(module)

        # Emit regime-filtered functions
        for func in module.all_functions():
            self._emit_function(func)

        return "\n".join(self.lines)

    def _emit_union(self, union: IRDiscriminatedUnion) -> None:
        """Emit a discriminated union as a Rust enum."""
        self._line(f"/// F# Discriminated Union: {union.name}")
        self._line("#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]")
        self._line(f"pub enum {union.name} {{")
        self.indent += 1

        for case in union.cases:
            if not case.payload_fields:
                self._line(f"{case.name},")
            elif len(case.payload_fields) == 1:
                fname, ftype = case.payload_fields[0]
                rust_type = ir_type_to_rust(ftype)
                self._line(f"{case.name} {{ {fname}: {rust_type} }},")
            else:
                self._line(f"{case.name} {{")
                self.indent += 1
                for fname, ftype in case.payload_fields:
                    rust_type = ir_type_to_rust(ftype)
                    self._line(f"{fname}: {rust_type},")
                self.indent -= 1
                self._line("},")

        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_record(self, record: IRRecordType) -> None:
        """Emit a record type as a Rust struct."""
        self._line(f"/// F# Record Type: {record.name}")
        self._line("#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]")
        self._line(f"pub struct {record.name} {{")
        self.indent += 1

        for fld in record.fields:
            rust_type = ir_type_to_rust(fld.ir_type)
            # Convert PascalCase field names to snake_case
            snake_name = self._to_snake_case(fld.name)
            self._line(f"pub {snake_name}: {rust_type},")

        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_taint_trait(self, module: IRModule) -> None:
        """Emit a BLAKE3 taint computation trait for the module types."""
        self._line("/// CORTEX-TAINT computation trait for BFT anchoring")
        self._line("pub trait CortexTaint {")
        self.indent += 1
        self._line("fn compute_taint(&self) -> String;")
        self.indent -= 1
        self._line("}")
        self._line("")

        # Implement for each tagged union
        for union in module.unions:
            if not union.is_simple_enum:
                self._emit_taint_impl(union)

        for sub in module.submodules:
            for union in sub.unions:
                if not union.is_simple_enum:
                    self._emit_taint_impl(union)

        # Implement for each record
        for record in module.records:
            self._emit_record_taint_impl(record)

        for sub in module.submodules:
            for record in sub.records:
                self._emit_record_taint_impl(record)

    def _emit_taint_impl(self, union: IRDiscriminatedUnion) -> None:
        """Emit CortexTaint implementation for a union type."""
        self._line(f"impl CortexTaint for {union.name} {{")
        self.indent += 1
        self._line("fn compute_taint(&self) -> String {")
        self.indent += 1
        self._line("let mut hasher = Hasher::new();")
        self._line("match self {")
        self.indent += 1

        for case in union.cases:
            if not case.payload_fields:
                self._line(f'{union.name}::{case.name} => {{')
                self.indent += 1
                self._line(f'hasher.update(b"{case.name}");')
                self.indent -= 1
                self._line("}")
            else:
                bindings = ", ".join(
                    self._to_snake_case(fname) for fname, _ in case.payload_fields
                )
                self._line(f'{union.name}::{case.name} {{ {bindings} }} => {{')
                self.indent += 1
                self._line(f'hasher.update(b"{case.name}");')
                for fname, ftype in case.payload_fields:
                    snake = self._to_snake_case(fname)
                    if ftype.kind == IRTypeKind.STRING:
                        self._line(f"hasher.update({snake}.as_bytes());")
                    elif ftype.kind == IRTypeKind.FLOAT:
                        self._line(f"hasher.update(&{snake}.to_be_bytes());")
                    else:
                        self._line(f'hasher.update(format!("{{:?}}", {snake}).as_bytes());')
                self.indent -= 1
                self._line("}")

        self.indent -= 1
        self._line("}")
        self._line('format!("TAINT:C5_REAL_RUST:{}", hasher.finalize().to_hex())')
        self.indent -= 1
        self._line("}")
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_record_taint_impl(self, record: IRRecordType) -> None:
        """Emit CortexTaint implementation for a record type."""
        self._line(f"impl CortexTaint for {record.name} {{")
        self.indent += 1
        self._line("fn compute_taint(&self) -> String {")
        self.indent += 1
        self._line("let mut hasher = Hasher::new();")

        for fld in record.fields:
            snake = self._to_snake_case(fld.name)
            if fld.ir_type.kind == IRTypeKind.STRING:
                self._line(f"hasher.update(self.{snake}.as_bytes());")
            elif fld.ir_type.kind == IRTypeKind.FLOAT:
                self._line(f"hasher.update(&self.{snake}.to_be_bytes());")
            elif fld.ir_type.kind == IRTypeKind.INT:
                self._line(f"hasher.update(&self.{snake}.to_be_bytes());")
            else:
                self._line(f'hasher.update(format!("{{:?}}", self.{snake}).as_bytes());')

        self._line('format!("TAINT:C5_REAL_RUST:{}", hasher.finalize().to_hex())')
        self.indent -= 1
        self._line("}")
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_function(self, func: IRFunction) -> None:
        """Emit a function, respecting regime boundaries."""
        # REGIME FILTER: Block physics computation
        if func.classification == FunctionClassification.STATE_TRANSITION:
            self._line(f"// @regime-blocked: {func.name}")
            self._line("// Classification: STATE_TRANSITION — physics stays in F# Domain Kernel.")
            self._line("// Rust receives the computed result via IPC/FFI boundary.")
            self._line("")
            return

        # Block consensus anchoring (belongs to Solidity)
        if func.classification == FunctionClassification.COMMIT_BOUNDARY:
            self._line(f"// @regime-blocked: {func.name}")
            self._line("// Classification: COMMIT_BOUNDARY — anchoring belongs to Solidity/Anvil.")
            self._line("")
            return

        if func.classification == FunctionClassification.EVENT_EMITTER:
            self._line(f"// @regime-blocked: {func.name}")
            self._line("// Classification: EVENT_EMITTER — event emission belongs to Solidity/Anvil.")
            self._line("")
            return

        # HASH_COMPUTATION → emit full implementation
        if func.classification == FunctionClassification.HASH_COMPUTATION:
            self._emit_hash_function(func)
            return

        # VALIDATION and PURE_QUERY → emit as Rust functions
        self._emit_generic_function(func)

    def _emit_hash_function(self, func: IRFunction) -> None:
        """Emit a BLAKE3 hash computation function."""
        params_rust = self._format_params(func.params)
        ret_type = ir_type_to_rust(func.return_type)

        self._line(f"/// {func.name} — BLAKE3 hash computation (Rust poset layer)")
        self._line(f"pub fn {self._to_snake_case(func.name)}({params_rust}) -> {ret_type} {{")
        self.indent += 1
        self._line("let mut hasher = Hasher::new();")
        for p in func.params:
            if p.ir_type.kind == IRTypeKind.STRING:
                self._line(f"hasher.update({p.name}.as_bytes());")
            else:
                self._line(f'hasher.update(format!("{{:?}}", {p.name}).as_bytes());')
        self._line('format!("TAINT:C5_REAL_RUST:{}", hasher.finalize().to_hex())')
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_generic_function(self, func: IRFunction) -> None:
        """Emit a generic Rust function stub."""
        params_rust = self._format_params(func.params)
        ret_type = ir_type_to_rust(func.return_type)

        self._line(f"/// {func.name} — Pure query / validation")
        self._line(f"pub fn {self._to_snake_case(func.name)}({params_rust}) -> {ret_type} {{")
        self.indent += 1
        self._line("todo!(\"Implement from F# Domain Kernel logic\")")
        self.indent -= 1
        self._line("}")
        self._line("")

    def _format_params(self, params: list[IRParam]) -> str:
        """Format function parameters for Rust."""
        parts: list[str] = []
        for p in params:
            rust_type = ir_type_to_rust(p.ir_type)
            name = self._to_snake_case(p.name)
            if p.ir_type.kind == IRTypeKind.STRING:
                parts.append(f"{name}: &str")
            elif p.ir_type.kind == IRTypeKind.CUSTOM:
                parts.append(f"{name}: &{rust_type}")
            else:
                parts.append(f"{name}: {rust_type}")
        return ", ".join(parts)

    def _line(self, text: str) -> None:
        """Add an indented line."""
        prefix = "    " * self.indent
        self.lines.append(f"{prefix}{text}")

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert PascalCase/camelCase to snake_case."""
        import re
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
