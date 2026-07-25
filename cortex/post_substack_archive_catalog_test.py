# C5-REAL EXERGY CERTIFIED
"""
Pytest unit test suite for Full Substack Archive Catalog Transduction (23 Articles).
Rule Compliance: Ω11 (Rich-Text Compatibility), R12 (Substack Exergy), Ω23 (Relative Paths).
"""

import pytest
from pathlib import Path

ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "substack_archive"


def get_archive_files() -> list[Path]:
    if not ARCHIVE_DIR.exists():
        return []
    return sorted(list(ARCHIVE_DIR.glob("*.md")))


ARCHIVE_FILES = get_archive_files()


def test_archive_count() -> None:
    assert len(ARCHIVE_FILES) == 23, f"Expected 23 archive files, found {len(ARCHIVE_FILES)}"


@pytest.mark.parametrize("filepath", ARCHIVE_FILES)
def test_substack_archive_article_invariants(filepath: Path) -> None:
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
