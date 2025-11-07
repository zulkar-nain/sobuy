"""
Generate optimized favicon images (PNG and ICO) from the source PNG at app/static/images/favicon.png

Usage:
    python scripts/generate_favicons.py

This will write files into app/static/images/:
 - favicon-16.png
 - favicon-32.png
 - apple-touch-icon-180x180.png
 - favicon.ico
 - site.webmanifest

Requires Pillow: pip install Pillow
"""
import os
from PIL import Image


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STATIC_IMAGES = os.path.join(ROOT, 'app', 'static', 'images')
SOURCE = os.path.join(STATIC_IMAGES, 'favicon.png')


def ensure_dirs():
    os.makedirs(STATIC_IMAGES, exist_ok=True)


def generate():
    if not os.path.exists(SOURCE):
        print('Source favicon not found at', SOURCE)
        return 1

    sizes_png = [(16, 'favicon-16.png'), (32, 'favicon-32.png'), (180, 'apple-touch-icon-180x180.png'), (48, 'favicon-48.png')]
    sizes_ico = [16, 32, 48, 64]

    im = Image.open(SOURCE).convert('RGBA')

    # Create PNG sizes
    for size, name in sizes_png:
        outpath = os.path.join(STATIC_IMAGES, name)
        res = im.resize((size, size), Image.LANCZOS)
        res.save(outpath, optimize=True)
        print('Wrote', outpath)

    # Create multi-size ICO
    ico_path = os.path.join(STATIC_IMAGES, 'favicon.ico')
    icons = [im.resize((s, s), Image.LANCZOS) for s in sizes_ico]
    icons[0].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes_ico])
    print('Wrote', ico_path)

    # Create a simple webmanifest
    manifest = {
        "name": "SoBuy",
        "short_name": "SoBuy",
        "icons": [
            {"src": "/static/images/apple-touch-icon-180x180.png", "sizes": "180x180", "type": "image/png"},
            {"src": "/static/images/favicon-32.png", "sizes": "32x32", "type": "image/png"},
            {"src": "/static/images/favicon-16.png", "sizes": "16x16", "type": "image/png"}
        ],
        "theme_color": "#ffffff",
        "background_color": "#ffffff",
        "display": "standalone"
    }
    import json
    manifest_path = os.path.join(STATIC_IMAGES, '..', 'site.webmanifest')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print('Wrote', manifest_path)

    return 0


if __name__ == '__main__':
    ensure_dirs()
    raise SystemExit(generate())
