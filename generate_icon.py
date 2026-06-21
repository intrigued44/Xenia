from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    os.makedirs('ui/assets', exist_ok=True)
    
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
        
    # Background circle (Xenia Iris color)
    margin = size // 8
    draw.ellipse(
        [margin, margin, 
         size-margin, size-margin],
        fill=(90, 94, 219, 255) # #5a5edb
    )
    
    # Letter X
    font_size = size // 2
    try:
        font = ImageFont.truetype(
            "arial.ttf", font_size
        )
    except Exception:
        font = ImageFont.load_default()
    
    text = "X"
    bbox = draw.textbbox((0,0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - margin//2
    draw.text((x, y), text, 
              fill=(255,255,255,255),
              font=font)
    
    # Save as PNG
    img.save('ui/assets/icon.png', format='PNG')
    print("Icon created: ui/assets/icon.png")

if __name__ == '__main__':
    create_icon()
