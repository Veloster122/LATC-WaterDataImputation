"""
Convert PNG icon to ICO format for Windows executable
"""
from PIL import Image
import sys

def convert_to_ico(png_path, ico_path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]):
    """Convert PNG to multi-resolution ICO"""
    img = Image.open(png_path)
    
    # Remove alpha channel if present and create white background
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])  # Use alpha as mask
        img = background
    
    img.save(ico_path, format='ICO', sizes=sizes)
    print(f"✓ Icon created: {ico_path}")

if __name__ == "__main__":
    source = "C:/Users/Utilizador/.gemini/antigravity/brain/62aa1241-7342-492a-85d9-3ed92319a8de/icon_concept_chart_water_1767986204001.png"
    target = "icon.ico"
    
    convert_to_ico(source, target)
