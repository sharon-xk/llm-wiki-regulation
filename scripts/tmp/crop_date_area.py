from PIL import Image
import os

# Crop the bottom 500 pixels of page 3 where the date should be
img_path = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/ocr_尹伟霖/page-3.png"
img = Image.open(img_path)
w, h = img.size
print(f"Image size: {w}x{h}")

# Crop bottom portion (last ~600 pixels)
bottom = img.crop((0, h-600, w, h))
bottom_path = "/Users/sharon/ai-project/llm-wiki-regulation/scripts/tmp/尹伟霖_date_area.png"
bottom.save(bottom_path)
print(f"Cropped to: {bottom_path}, size: {bottom.size}")
