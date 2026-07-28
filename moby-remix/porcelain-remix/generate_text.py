# C5-REAL EXERGY CERTIFIED
import os
from PIL import Image, ImageDraw, ImageFont

# Create a transparent image the size of the video (1280x720)
width, height = 1280, 720
img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Try to load a nice font, fallback to default
try:
    font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
    font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

text1 = "PORCELAIN"
text2 = "MICROTONAL COSMIC DOWNTEMPO"

# We use textbbox to get dimensions
bbox1 = draw.textbbox((0, 0), text1, font=font_large)
w1 = bbox1[2] - bbox1[0]
h1 = bbox1[3] - bbox1[1]

bbox2 = draw.textbbox((0, 0), text2, font=font_small)
w2 = bbox2[2] - bbox2[0]
h2 = bbox2[3] - bbox2[1]

# Draw with shadow
x1, y1 = (width - w1) // 2, (height - h1) // 2 - 40
# Shadow
draw.text((x1+2, y1+2), text1, font=font_large, fill=(0, 0, 0, 128))
# Text
draw.text((x1, y1), text1, font=font_large, fill=(255, 255, 255, 204))

x2, y2 = (width - w2) // 2, (height - h2) // 2 + 60
# Shadow
draw.text((x2+2, y2+2), text2, font=font_small, fill=(0, 0, 0, 128))
# Text
draw.text((x2, y2), text2, font=font_small, fill=(255, 255, 255, 153))

img.save("public/text_layer.png")
