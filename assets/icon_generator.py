"""
Simple script to generate app icon
"""
from PIL import Image, ImageDraw, ImageFont

# Create a 512x512 icon
size = 512
img = Image.new('RGB', (size, size), color='#2196F3')
draw = ImageDraw.Draw(img)

# Draw a simple AI/image icon representation
# Draw a frame
frame_margin = 50
draw.rectangle(
    [frame_margin, frame_margin, size-frame_margin, size-frame_margin],
    outline='white',
    width=15
)

# Draw "AI" text in the center
try:
    # Try to use a nice font if available
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
except:
    font = ImageFont.load_default()

text = "AI"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (size - text_width) // 2
y = (size - text_height) // 2 - 20
draw.text((x, y), text, fill='white', font=font)

# Save icon
img.save('icon.png')
print("Icon created: icon.png")

# Create presplash (same image but landscape)
presplash = Image.new('RGB', (1280, 720), color='#2196F3')
draw = ImageDraw.Draw(presplash)

# Center the icon in presplash
icon_small = img.resize((256, 256), Image.Resampling.LANCZOS)
x = (1280 - 256) // 2
y = (720 - 256) // 2
presplash.paste(icon_small, (x, y))

# Add app name
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
except:
    font = ImageFont.load_default()

text = "DALL-E Image Generator"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
x = (1280 - text_width) // 2
y = y + 256 + 40
draw.text((x, y), text, fill='white', font=font)

presplash.save('presplash.png')
print("Presplash created: presplash.png")