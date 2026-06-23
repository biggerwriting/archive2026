#!/usr/bin/env python3
"""Generate Chrome extension icon set from a source image."""

import sys
import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

ICON_SIZES = [16, 32, 48, 128]


def generate_icons(source_path: str, output_dir: str = None):
    source = Path(source_path)
    if not source.exists():
        print(f"Error: Source file '{source_path}' not found.")
        sys.exit(1)

    if output_dir is None:
        output_dir = source.parent / "icons"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as img:
        # Convert to RGBA to support transparency
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        print(f"Source: {source} ({img.width}x{img.height})")

        # Center-crop to square if not already square
        w, h = img.width, img.height
        if w != h:
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            print(f"Cropped to square: {side}x{side}")

        print(f"Output: {output_dir}/")
        print()

        for size in ICON_SIZES:
            resized = img.resize((size, size), Image.LANCZOS)
            output_path = output_dir / f"icon{size}.png"
            resized.save(output_path, "PNG")
            print(f"  icon{size}.png  ({size}x{size})")

    print("\nDone.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_icons.py <source_image> [output_dir]")
        print("Example: python generate_icons.py logo.png")
        print("         python generate_icons.py logo.png ./my_icons")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    generate_icons(source, output)
