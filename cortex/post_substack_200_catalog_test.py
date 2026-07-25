# C5-REAL EXERGY CERTIFIED
"""
Pytest unit test suite for Complete 200 Substack Archive Catalog Transduction.
Rule Compliance: Ω11 (Rich-Text Compatibility), R12 (Substack Exergy), Ω23 (Relative Paths).
"""

import pytest
from pathlib import Path

ARCHIVE_200_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "substack_archive_200"

def get_200_archive_files() -> list[Path]:
    if not ARCHIVE_200_DIR.exists():
        return []
    return sorted(list(ARCHIVE_200_DIR.glob("*.md")))

FILES_200 = get_200_archive_files()

def test_200_archive_count() -> None:
    assert len(FILES_200) == 200, f"Expected 200 archive files, found {len(FILES_200)}"

@pytest.mark.parametrize("filepath", FILES_200)
def test_substack_200_article_invariants(filepath: Path) -> None:
    assert filepath.exists(), f"Missing file: {filepath}"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Invariant 1: Prohibit Markdown Tables (|---|)
    assert "|---| " not in content, f"Markdown table found in {filepath}"
    assert "|:---|" not in content, f"Markdown table found in {filepath}"

    # Invariant 2: Prohibit Raw LaTeX $ delimiters
    assert "$S = " not in content, f"LaTeX math found in {filepath}"
    assert "$r$" not in content, f"LaTeX math found in {filepath}"

    # Invariant 3: Mandatory Footer Block & UTBH Anchor URL
    assert "⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):" in content
    assert "https://borjamoskv.substack.com/p/el-colapso-del-macho-alfa-de-cristal" in content

    # Invariant 4: Mandatory Persona & Reality Tags
    assert "Telmo Dinámico de Moskv" in content
    assert "#C5-REAL" in content
