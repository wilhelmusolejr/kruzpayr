from PIL import Image
import os

src_dir = "images"
dst_dir = "png_refs"

os.makedirs(dst_dir, exist_ok=True)

for file in os.listdir(src_dir):
    if file.lower().endswith(".bmp"):
        img = Image.open(os.path.join(src_dir, file))
        out_name = file.replace(".bmp", ".png")
        img.save(os.path.join(dst_dir, out_name), format="PNG")
