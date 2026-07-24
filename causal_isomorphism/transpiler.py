# C5-REAL: F# → {Solidity, Rust} controlled AST transmutation
"""
Main orchestrator for the Causal Isomorphism Transpiler.

Pipeline:
  1. Parse F# source → IR (Intermediate Representation)
  2. Validate IR against Trilingual Regime boundaries
  3. Emit Solidity contract (regime-filtered)
  4. Emit Rust module (regime-filtered)
  5. Generate validation report

This module ties together parser, validator, and emitters into a single
deterministic pipeline invocation.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from causal_isomorphism.emitter_rust import RustEmitter
from causal_isomorphism.emitter_solidity import SolidityEmitter
from causal_isomorphism.ir import IRModule, RegimeLayer
from causal_isomorphism.parser_fsharp import FSharpParser
from causal_isomorphism.regime_validator import (
    RegimeValidator,
    ValidationReport,
)


@dataclass
class TranspilationResult:
    """Complete result of a transpilation run."""
    source_file: str
    ir_module: IRModule
    solidity_output: str
    rust_output: str
    solidity_report: ValidationReport
    rust_report: ValidationReport
    timestamp: str = ""
    source_hash: str = ""

    solidity_path: str = ""
    rust_path: str = ""
    report_path: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def is_valid(self) -> bool:
        return self.solidity_report.is_valid and self.rust_report.is_valid

    def full_report(self) -> str:
        """Generate the complete transpilation report."""
        lines: list[str] = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║     CAUSAL ISOMORPHISM TRANSPILER — BABYLON-60             ║",
            "║     Trilingual Regime: F# → {Solidity, Rust}              ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            f"Source:    {self.source_file}",
            f"Hash:      {self.source_hash}",
            f"Timestamp: {self.timestamp}",
            f"Status:    {'✅ VALID' if self.is_valid else '❌ REGIME VIOLATIONS DETECTED'}",
            "",
            "── IR Module ──",
            f"  Name:       {self.ir_module.name}",
            f"  Unions:     {len(self.ir_module.unions)}",
            f"  Records:    {len(self.ir_module.records)}",
            f"  Functions:  {len(self.ir_module.functions)}",
            f"  Submodules: {len(self.ir_module.submodules)}",
            "",
            "── Solidity Target ──",
            self.solidity_report.summary(),
            "",
            "── Rust Target ──",
            self.rust_report.summary(),
        ]

        if self.solidity_path:
            lines.extend(["", f"Solidity output: {self.solidity_path}"])
        if self.rust_path:
            lines.extend([f"Rust output:     {self.rust_path}"])

        return "\n".join(lines)


@dataclass
class CausalIsomorphismTranspiler:
    """
    Orchestrates the full F# → {Solidity, Rust} transpilation pipeline.

    Usage:
        transpiler = CausalIsomorphismTranspiler()
        result = transpiler.transpile_file(
            source=Path("domain_kernel/IRPAutomata.fs"),
            output_dir=Path("causal_isomorphism/generated/"),
        )
    """
    parser: FSharpParser = field(default_factory=FSharpParser)
    validator: RegimeValidator = field(default_factory=RegimeValidator)
    sol_emitter: SolidityEmitter = field(default_factory=SolidityEmitter)
    rust_emitter: RustEmitter = field(default_factory=RustEmitter)

    def transpile_file(
        self,
        source: Path,
        output_dir: Path | None = None,
    ) -> TranspilationResult:
        """
        Execute the full transpilation pipeline on an F# source file.

        Args:
            source: Path to the F# source file
            output_dir: Directory for generated output (None = dry run)

        Returns:
            TranspilationResult with all outputs and validation reports
        """
        source_text = source.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()

        ir_module = self.parser.parse_file(source)

        sol_report = self.validator.validate(ir_module, RegimeLayer.CONSENSUS)
        rust_report = self.validator.validate(ir_module, RegimeLayer.THERMODYNAMICS)

        self.sol_emitter = SolidityEmitter()  # Reset state
        solidity_output = self.sol_emitter.emit_module(ir_module)

        self.rust_emitter = RustEmitter()  # Reset state
        rust_output = self.rust_emitter.emit_module(ir_module)

        try:
            rel_source = str(source.resolve().relative_to(Path.cwd()))
        except ValueError:
            rel_source = str(source)

        result = TranspilationResult(
            source_file=rel_source,
            ir_module=ir_module,
            solidity_output=solidity_output,
            rust_output=rust_output,
            solidity_report=sol_report,
            rust_report=rust_report,
            source_hash=source_hash,
        )

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            self._write_outputs(result, output_dir)

        return result

    def transpile_source(self, source: str, module_name: str = "Anonymous") -> TranspilationResult:
        """
        Execute transpilation on an F# source string (for testing/REPL).

        Args:
            source: F# source code string
            module_name: Name for the IR module

        Returns:
            TranspilationResult
        """
        source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()

        ir_module = self.parser.parse_source(source, module_name)

        sol_report = self.validator.validate(ir_module, RegimeLayer.CONSENSUS)
        rust_report = self.validator.validate(ir_module, RegimeLayer.THERMODYNAMICS)

        self.sol_emitter = SolidityEmitter()
        solidity_output = self.sol_emitter.emit_module(ir_module)

        self.rust_emitter = RustEmitter()
        rust_output = self.rust_emitter.emit_module(ir_module)

        return TranspilationResult(
            source_file="<string>",
            ir_module=ir_module,
            solidity_output=solidity_output,
            rust_output=rust_output,
            solidity_report=sol_report,
            rust_report=rust_report,
            source_hash=source_hash,
        )

    def _write_outputs(self, result: TranspilationResult, output_dir: Path) -> None:
        """Write generated code and reports to disk."""
        module_name = result.ir_module.name

        sol_path = output_dir / f"{module_name}Anchor.sol"
        sol_path.write_text(result.solidity_output, encoding="utf-8")
        try:
            result.solidity_path = str(sol_path.resolve().relative_to(Path.cwd()))
        except ValueError:
            result.solidity_path = str(sol_path)

        rust_path = output_dir / f"{self._to_snake(module_name)}.rs"
        rust_path.write_text(result.rust_output, encoding="utf-8")
        try:
            result.rust_path = str(rust_path.resolve().relative_to(Path.cwd()))
        except ValueError:
            result.rust_path = str(rust_path)

        report_path = output_dir / f"{module_name}_regime_report.txt"
        report_path.write_text(result.full_report(), encoding="utf-8")
        try:
            result.report_path = str(report_path.resolve().relative_to(Path.cwd()))
        except ValueError:
            result.report_path = str(report_path)

    @staticmethod
    def _to_snake(name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
