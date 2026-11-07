#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 Sovereign Hardened
# █ BRUTALIST CAROUSEL BUILDER (ISHTAR-60) | DOMAIN: creatives | STATE: C5-REAL
# ============================================================================
"""
Brutalist 1080x1350 (4:5) Instagram Carousel Builder.
Generates pixel-perfect, high-exergy multi-slide graphics using PIL.
Applies the C5-REAL Sovereign aesthetic: Obsidian, Sovereign Gold, and Bone White.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


# Canonical Dimensions & Colors
CANONICAL_WIDTH = 1080
CANONICAL_HEIGHT = 1350

COLOR_BG = (10, 10, 10)            # #0A0A0A Obsidian
COLOR_CARD_BG = (18, 20, 24)       # #121418 Dark slate
COLOR_GOLD = (212, 175, 55)        # #D4AF37 Sovereign Gold
COLOR_TEXT_MAIN = (240, 240, 240)  # #F0F0F0 Bone White
COLOR_TEXT_MUTED = (140, 145, 155) # #8C919B Muted Silver
COLOR_BORDER = (40, 44, 52)        # #282C34 Graphite Border


@dataclass
class CarouselSlide:
    """Represents the data content of a single carousel slide."""
    header: str
    body_paragraphs: List[str]
    code_snippet: Optional[str] = None
    footer_note: Optional[str] = None


class CarouselBuilder:
    """Generates 1080x1350 vertical PNG carousels for @babylon60.ai."""

    def __init__(self, font_name: Optional[str] = None):
        self.width = CANONICAL_WIDTH
        self.height = CANONICAL_HEIGHT
        self.fonts = self._load_fonts(font_name)

    def _load_fonts(self, font_name: Optional[str] = None) -> dict:
        """Loads available system fonts or falls back safely to PIL default."""
        font_candidates = [
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/SFProDisplay-Regular.otf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
        if font_name and Path(font_name).exists():
            font_candidates.insert(0, font_name)

        loaded_font_path = None
        for path in font_candidates:
            if Path(path).exists():
                loaded_font_path = path
                break

        try:
            if loaded_font_path:
                return {
                    "title": ImageFont.truetype(loaded_font_path, 54),
                    "subtitle": ImageFont.truetype(loaded_font_path, 34),
                    "body": ImageFont.truetype(loaded_font_path, 36),
                    "code": ImageFont.truetype(loaded_font_path, 28),
                    "meta": ImageFont.truetype(loaded_font_path, 24),
                }
        except Exception:
            pass

        default = ImageFont.load_default()
        return {
            "title": default,
            "subtitle": default,
            "body": default,
            "code": default,
            "meta": default,
        }

    def _draw_chrome(
        self,
        draw: ImageDraw.ImageDraw,
        slide_idx: int,
        total_slides: int,
        category: str = "BABYLON-60 · SOVEREIGN SYSTEMS",
    ):
        """Draws top status bar, category badge, slide index, and bottom footer."""
        # Top Header line
        draw.line([(60, 80), (self.width - 60, 80)], fill=COLOR_BORDER, width=2)
        
        # Category Tag
        draw.text((60, 48), category.upper(), fill=COLOR_GOLD, font=self.fonts["meta"])
        
        # Slide Index Indicator [k/N]
        indicator = f"[{slide_idx:02d} / {total_slides:02d}]"
        draw.text((self.width - 160, 48), indicator, fill=COLOR_TEXT_MUTED, font=self.fonts["meta"])

        # Bottom Footer Line
        draw.line([(60, self.height - 90), (self.width - 60, self.height - 90)], fill=COLOR_BORDER, width=2)
        
        # Brand & Author Attribution
        draw.text((60, self.height - 68), "@babylon60.ai", fill=COLOR_GOLD, font=self.fonts["meta"])
        author_text = "BORJA FERNÁNDEZ ANGULO · C5-REAL"
        draw.text((self.width - 430, self.height - 68), author_text, fill=COLOR_TEXT_MUTED, font=self.fonts["meta"])

    def _wrap_text(self, text: str, max_chars: int = 42) -> List[str]:
        """Simple deterministic word-wrap for slide typography."""
        words = text.split()
        lines = []
        current_line = []
        current_len = 0
        for word in words:
            if current_len + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_len += len(word) + 1
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    def render_cover_slide(
        self,
        title: str,
        subtitle: str,
        slide_idx: int,
        total_slides: int,
        tag: str = "ARQUITECTURA DE SISTEMAS",
    ) -> Image.Image:
        """Renders the opening cover slide with brutalist typography."""
        img = Image.new("RGB", (self.width, self.height), color=COLOR_BG)
        draw = ImageDraw.Draw(img)
        self._draw_chrome(draw, slide_idx, total_slides, tag)

        # Decorative Corner Crosses
        cross_size = 12
        for (cx, cy) in [(60, 110), (self.width - 60, 110), (60, self.height - 120), (self.width - 60, self.height - 120)]:
            draw.line([(cx - cross_size, cy), (cx + cross_size, cy)], fill=COLOR_GOLD, width=2)
            draw.line([(cx, cy - cross_size), (cx, cy + cross_size)], fill=COLOR_GOLD, width=2)

        # Title Block
        y = 380
        title_lines = self._wrap_text(title, max_chars=32)
        for line in title_lines:
            draw.text((90, y), line, fill=COLOR_TEXT_MAIN, font=self.fonts["title"])
            y += 76

        # Gold Accent Divider
        draw.line([(90, y + 20), (220, y + 20)], fill=COLOR_GOLD, width=4)
        y += 50

        # Subtitle
        sub_lines = self._wrap_text(subtitle, max_chars=44)
        for line in sub_lines:
            draw.text((90, y), line, fill=COLOR_TEXT_MUTED, font=self.fonts["subtitle"])
            y += 48

        # Bottom Call to Action hint
        draw.text((90, self.height - 200), "Desliza para continuar ──►", fill=COLOR_GOLD, font=self.fonts["body"])

        return img

    def render_content_slide(
        self,
        slide: CarouselSlide,
        slide_idx: int,
        total_slides: int,
        tag: str = "INVARIANTES C5-REAL",
    ) -> Image.Image:
        """Renders an intermediate content slide with paragraphs and optional code."""
        img = Image.new("RGB", (self.width, self.height), color=COLOR_BG)
        draw = ImageDraw.Draw(img)
        self._draw_chrome(draw, slide_idx, total_slides, tag)

        y = 150
        # Slide Header
        header_lines = self._wrap_text(slide.header, max_chars=36)
        for line in header_lines:
            draw.text((90, y), line, fill=COLOR_GOLD, font=self.fonts["subtitle"])
            y += 52
        
        # Subtle horizontal separator
        draw.line([(90, y + 10), (self.width - 90, y + 10)], fill=COLOR_BORDER, width=1)
        y += 35

        # Body Paragraphs
        for paragraph in slide.body_paragraphs:
            wrapped = self._wrap_text(paragraph, max_chars=44)
            for line in wrapped:
                draw.text((90, y), line, fill=COLOR_TEXT_MAIN, font=self.fonts["body"])
                y += 50
            y += 24

        # Code or Quotation Box
        if slide.code_snippet:
            box_top = y + 10
            code_lines = slide.code_snippet.strip().split("\n")
            box_height = len(code_lines) * 38 + 40
            draw.rectangle(
                [(90, box_top), (self.width - 90, box_top + box_height)],
                fill=COLOR_CARD_BG,
                outline=COLOR_BORDER,
                width=2,
            )
            # Left gold accent bar
            draw.line([(90, box_top), (90, box_top + box_height)], fill=COLOR_GOLD, width=4)

            cy = box_top + 20
            for cline in code_lines:
                draw.text((120, cy), cline, fill=COLOR_TEXT_MAIN, font=self.fonts["code"])
                cy += 38

        return img

    def build_carousel(
        self,
        title: str,
        subtitle: str,
        slides_data: List[CarouselSlide],
        output_dir: Path,
        prefix: str = "slide",
    ) -> List[Path]:
        """
        Builds and saves the complete set of carousel PNG files.
        Returns the ordered list of absolute paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        total_slides = len(slides_data) + 1
        output_paths: List[Path] = []

        # 1. Cover Slide
        cover_img = self.render_cover_slide(title, subtitle, 1, total_slides)
        cover_path = output_dir / f"{prefix}_01_cover.png"
        cover_img.save(cover_path, format="PNG")
        output_paths.append(cover_path)

        # 2. Content Slides
        for i, slide in enumerate(slides_data, start=2):
            slide_img = self.render_content_slide(slide, i, total_slides)
            slide_path = output_dir / f"{prefix}_{i:02d}.png"
            slide_img.save(slide_path, format="PNG")
            output_paths.append(slide_path)

        return output_paths
