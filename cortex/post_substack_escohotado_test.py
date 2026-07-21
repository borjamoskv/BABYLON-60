"""
Pytest unit test for Substack Post Formatting Invariants (substack-moskv-omega).
Rule Compliance: Ω11 (Rich-Text Compatibility), R12 (Substack Exergy).
"""

import os
from pathlib import Path

SUBSTACK_POST_PATH = str(
    Path(__file__).resolve().parent.parent
    / "artifacts"
    / "post_substack_escohotado_ultrathink.md"
)


def test_substack_post_formatting_invariants() -> None:
    assert os.path.exists(SUBSTACK_POST_PATH)
    with open(SUBSTACK_POST_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Invariant 1: Prohibit Markdown Tables (|---|)
    assert "|---| " not in content
    assert "|:---|" not in content

    # Invariant 2: Prohibit Raw LaTeX $ delimiters
    assert "$S = " not in content
    assert "$r$" not in content
    assert "$c$" not in content

    # Invariant 3: Mandatory Footer Block
    assert "⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):" in content
    assert (
        "https://borjamoskv.substack.com/p/el-colapso-del-macho-alfa-de-cristal"
        in content
    )

    # Invariant 4: Mandatory Persona & Reality Tags
    assert "Telmo Dinámico de Moskv" in content
    assert "#C5-REAL" in content
    assert "#C4-SIM" in content
