# C5-REAL EXERGY CERTIFIED
"""
Pytest unit tests for CORTEX Substack Preview Server & Renderer Engine.
Rule Compliance: Ω11 (Rich-Text Compatibility), Ω23 (Relative Paths).
"""

from cortex.substack.substack_preview_server import render_post_html, HTML_TEMPLATE

def test_render_post_html_valid_file() -> None:
    html = render_post_html("01_la-matriz-cuatripartita-de-enfant.md")
    assert "<!DOCTYPE html>" in html
    assert "CORTEX C5-REAL PREVIEW" in html
    assert "La Matriz Cuatripartita de Enfant Sauvage" in html

def test_render_post_html_missing_file() -> None:
    html = render_post_html("non_existent_file_999.md")
    assert "Error 404" in html
    assert "Post file not found" in html

def test_template_rendering() -> None:
    rendered = HTML_TEMPLATE.format(body_content="<p>Test Body</p>")
    assert "<p>Test Body</p>" in rendered
    assert "INDUSTRIAL NOIR 2026" in rendered
