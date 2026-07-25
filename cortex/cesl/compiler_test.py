# C5-REAL EXERGY CERTIFIED
"""
Unit tests for C5-REAL CESL 1.0 Compiler.
"""

from pathlib import Path
from cortex.cesl.compiler import CESLCompiler

def test_cesl_compiler_end_to_end() -> None:
    spec_path = Path(__file__).parent / "kernel_v1.cesl"
    assert spec_path.exists()

    source = spec_path.read_text(encoding="utf-8")
    compiler = CESLCompiler(source)
    ast = compiler.compile()

    assert ast.module_name == "C5RealKernel"
    assert len(ast.types) == 3
    assert ast.types[0].name == "Evidence"
    assert ast.types[0].fields[0].name == "id"
    assert len(ast.relations) == 4
    assert ast.relations[0].name == "verifies"
    assert ast.relations[0].domain == "Evidence"
    assert ast.relations[0].codomain == "Claim"

    assert len(ast.invariants) == 1
    assert ast.invariants[0].name == "EveryClaimHasEvidence"

    assert len(ast.transitions) == 1
    assert ast.transitions[0].name == "VerifyClaim"
    assert "Claim" in ast.transitions[0].inputs
    assert "VerifiedClaim" in ast.transitions[0].outputs

    assert len(ast.capabilities) == 5
    assert ast.capabilities[0].name == "ReadArtifact"

    # Validate Mermaid generation
    mermaid_out = compiler.generate_mermaid(ast)
    assert "Evidence -->|verifies| Claim" in mermaid_out
    assert "Claim -->|input to VerifyClaim| VerifyClaim_Step" in mermaid_out

    # Validate Markdown generation
    md_out = compiler.generate_markdown(ast)
    assert "# Module: C5RealKernel" in md_out
    assert "### `type Evidence`" in md_out
    assert "capability ReadArtifact" in md_out
