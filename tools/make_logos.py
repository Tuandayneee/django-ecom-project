# tools/make_logos.py
# Usage: python tools/make_logos.py [path/to/source-image]
from PIL import Image
import os
import sys

# Source file path (default). You can override by passing a path as the first arg.
SRC = "source/logo-source.png"
if len(sys.argv) > 1:
    SRC = sys.argv[1]

OUT_DIR = "public/static/images"

os.makedirs(OUT_DIR, exist_ok=True)

sizes = {
    "logo.png": (512, 512),
    "logo-256.png": (256, 256),
    "logo-180.png": (180, 180),
    "logo-64.png": (64, 64),
    "logo-32.png": (32, 32),
}

if not os.path.exists(SRC):
    print(f"Source file not found: {SRC}\nPlace your source image at '{SRC}' or pass the source path as the first argument:\n    python tools/make_logos.py path/to/your-image.png")
    raise SystemExit(1)

img = Image.open(SRC).convert("RGBA")

for name, size in sizes.items():
    out_path = os.path.join(OUT_DIR, name)
    # create a thumbnail preserving aspect ratio
    resized = img.copy()
    resized.thumbnail(size, Image.LANCZOS)
    # center the image on a transparent background of exact size
    background = Image.new("RGBA", size, (255, 255, 255, 0))
    x = (size[0] - resized.width) // 2
    y = (size[1] - resized.height) // 2
    background.paste(resized, (x, y), resized)
    background.save(out_path, format="PNG")
    print(f"Saved {out_path}")

# create favicon.ico (16,32,48)
ico_sizes = [(16, 16), (32, 32), (48, 48)]
icons = []
for s in ico_sizes:
    im = img.copy()
    im.thumbnail(s, Image.LANCZOS)
    # ensure RGBA -> RGB for ICO
    bg = Image.new("RGBA", s, (255, 255, 255, 0))
    x = (s[0] - im.width) // 2
    y = (s[1] - im.height) // 2
    bg.paste(im, (x, y), im)
    icons.append(bg.convert("RGBA"))

ico_path = os.path.join(OUT_DIR, "favicon.ico")
# Pillow can save multiple sizes in one ICO by passing sizes argument when saving an RGB image
icons[0].save(ico_path, format="ICO", sizes=[(16,16),(32,32),(48,48)])
print(f"Saved {ico_path}")
