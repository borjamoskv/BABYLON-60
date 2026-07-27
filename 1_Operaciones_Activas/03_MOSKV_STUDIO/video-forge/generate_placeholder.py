# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import argparse
from PIL import Image, ImageDraw, ImageFont

def draw_placeholder(output_path, text, width, height):
    # Create image
    img = Image.new("RGBA", (width, height), "#0A0A0A")
    draw = ImageDraw.Draw(img)

    # Draw gradient background to dark blue-gray
    for y in range(height):
        r = int(10 + (y / height) * 8)
        g = int(10 + (y / height) * 12)
        b = int(10 + (y / height) * 28)
        for x in range(width):
            img.putpixel((x, y), (r, g, b, 255))

    # Re-get draw context for drawing shapes
    draw = ImageDraw.Draw(img)

    # Draw grid lines
    grid_spacing = 60
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill=(43, 59, 229, 12))  # #2B3BE5 with low opacity
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill=(43, 59, 229, 12))

    # Draw technical corner accents
    pad = 40
    corner_len = 30
    color_accent = (43, 59, 229, 128)  # Electric blue (#2B3BE5)

    # Top-left
    draw.line([(pad, pad), (pad + corner_len, pad)], fill=color_accent, width=2)
    draw.line([(pad, pad), (pad, pad + corner_len)], fill=color_accent, width=2)

    # Top-right
    draw.line([(width - pad, pad), (width - pad - corner_len, pad)], fill=color_accent, width=2)
    draw.line([(width - pad, pad), (width - pad, pad + corner_len)], fill=color_accent, width=2)

    # Bottom-left
    draw.line([(pad, height - pad), (pad + corner_len, height - pad)], fill=color_accent, width=2)
    draw.line([(pad, height - pad), (pad, height - pad - corner_len)], fill=color_accent, width=2)

    # Bottom-right
    draw.line([(width - pad, height - pad), (width - pad - corner_len, height - pad)], fill=color_accent, width=2)
    draw.line([(width - pad, height - pad), (width - pad, height - pad - corner_len)], fill=color_accent, width=2)

    # Load fonts
    font = None
    status_font = None
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(width / 22))
    except Exception:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New.ttf", int(width / 24))
        except Exception:
            font = ImageFont.load_default()

    try:
        status_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New.ttf", 16)
    except Exception:
        status_font = ImageFont.load_default()

    # Measure text size
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = draw.textsize(text, font=font)

    text_x = (width - text_w) // 2
    text_y = (height - text_h) // 2

    # Draw drop shadow for main text
    shadow_offset = 3
    draw.text((text_x + shadow_offset, text_y + shadow_offset), text, fill=(0, 0, 0, 180), font=font)

    # Draw main text
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 240), font=font)

    # Draw status bar
    draw.text((pad + 10, pad + 10), "SYS // C4-SIMULATION", fill=(255, 184, 0, 180), font=status_font)
    draw.text((width - pad - 220, pad + 10), "EXERGY: OMEGA-SIGNAL", fill=(43, 59, 229, 200), font=status_font)

    # Save image
    img.convert("RGB").save(output_path, "PNG")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()
    draw_placeholder(args.output, args.text, args.width, args.height)
