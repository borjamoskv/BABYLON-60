# C5-REAL EXERGY CERTIFIED
"""
Pytest unit tests for Substack Publisher & Formatting Transducer Tool.
Rule Compliance: Ω11 (Rich-Text Compatibility), R12 (Substack Exergy).
"""

from cortex.substack_publisher_tool import (
    format_signature_block,
    purge_latex_math,
    convert_tables_to_lists,
    process_markdown_for_substack,
)


def test_format_signature_block() -> None:
    sig = format_signature_block(count=3)
    assert "⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):" in sig
    assert "https://borjamoskv.substack.com/p/el-colapso-del-macho-alfa-de-cristal" in sig
    # Should contain 4 links total (1 mandatory + 3 random)
    assert sig.count("https://borjamoskv.substack.com/p/") >= 4


def test_purge_latex_math() -> None:
    raw = "The entropy is $S = -\\sum p_i \\ln p_i$ and growth rate $r$"
    purged = purge_latex_math(raw)
    assert "$S = " not in purged
    assert "$r$" not in purged
    assert "S = -∑ p_i ln(p_i)" in purged


def test_convert_tables_to_lists() -> None:
    table_md = "| Header1 | Header2 |\n|---|---|\n| Val1 | Val2 |"
    converted = convert_tables_to_lists(table_md)
    assert "|---| " not in converted
    assert "* **Val1:**" in converted


def test_full_process() -> None:
    raw = "# Test Post\n\nSome text with $r$ rate.\n"
    res = process_markdown_for_substack(raw)
    assert "$r$" not in res
    assert "⚡ [CORTEX C5-REAL]" in res
