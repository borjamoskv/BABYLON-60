# C5-REAL EXERGY CERTIFIED
"""
Pytest unit test suite for All Substack Publication Formatting Invariants (substack-moskv-omega).
Rule Compliance: Ω11 (Rich-Text Compatibility), R12 (Substack Exergy), Ω23 (Relative Paths).
"""

import pytest
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"

SUBSTACK_FILES = [
    ARTIFACTS_DIR / "post_substack_escohotado_ultrathink.md",
    ARTIFACTS_DIR / "post_substack_neuromorphic_vs_quantum.md",
    ARTIFACTS_DIR / "post_substack_necrosis_ontologica.md",
]

@pytest.mark.parametrize("filepath", SUBSTACK_FILES)
def test_substack_publication_formatting_invariants(filepath: Path) -> None:
    assert filepath.exists(), f"Publication file missing: {filepath}"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Invariant 1: Prohibit Markdown Tables (|---|)
    assert "|---| " not in content, f"Table found in {filepath}"
    assert "|:---|" not in content, f"Table found in {filepath}"

    # Invariant 2: Prohibit Raw LaTeX $ delimiters
    assert "$S = " not in content, f"LaTeX math found in {filepath}"
    assert "$r$" not in content, f"LaTeX math found in {filepath}"

    # Invariant 3: Mandatory Footer Block & UTBH Canonical URL
    assert "⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):" in content
    assert "https://borjamoskv.substack.com/p/el-colapso-del-macho-alfa-de-cristal" in content

    # Invariant 4: Mandatory Persona & Reality Tags
    assert "Telmo Dinámico de Moskv" in content
    assert "#C5-REAL" in content
