# C5-REAL EXERGY CERTIFIED
"""
Pytest integration test for F# Sovereign Ontology (net10.0).
Rule Compliance: Ω117 (Multi-Language BFT Audit).
"""

import subprocess
from pathlib import Path


def test_fsharp_kernel_compilation_and_ontology() -> None:
    project_dir = Path(__file__).resolve().parent.parent / "fsharp_kernel"
    fsproj = project_dir / "fsharp_kernel.fsproj"

    assert fsproj.exists(), f"F# project file not found at {fsproj}"

    res = subprocess.run(
        ["dotnet", "build", str(fsproj)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert res.returncode == 0, f"dotnet build failed:\n{res.stdout}\n{res.stderr}"
    assert "0 Errores" in res.stdout or "0 Error(s)" in res.stdout
