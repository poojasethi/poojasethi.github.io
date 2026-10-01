#!/usr/bin/env python3
"""Prepare photos for the Photos page.

For each input photo this writes two WebP files to img/photos/:
  <name>.webp        2000px on the long edge, shown when a photo is opened
  <name>-thumb.webp  900px on the long edge, shown in the grid
Rotation from the camera is applied, and all metadata (including GPS
location) is removed. It then prints the lines to paste into _data/photos.yml.

Usage:
  python3 scripts/add_photo.py ~/Pictures/rainier.jpg [more photos...]

Requires Pillow:  python3 -m pip install --user pillow
HEIC files from an iPhone are converted with macOS `sips` first.
"""

import pathlib
import re
import subprocess
import sys
import tempfile

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is not installed. Run: python3 -m pip install --user pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "img" / "photos"
SIZES = {"": 2000, "-thumb": 900}


def slug(path):
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def open_image(path, tmpdir):
    if path.suffix.lower() in (".heic", ".heif"):
        jpg = pathlib.Path(tmpdir) / (path.stem + ".jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", str(path), "--out", str(jpg)],
                       check=True, capture_output=True)
        path = jpg
    image = ImageOps.exif_transpose(Image.open(path))
    return image.convert("RGB")


def main(paths):
    if not paths:
        sys.exit(__doc__)
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for arg in paths:
            path = pathlib.Path(arg).expanduser()
            name = slug(path)
            image = open_image(path, tmpdir)
            for suffix, long_edge in SIZES.items():
                copy = image.copy()
                copy.thumbnail((long_edge, long_edge), Image.LANCZOS)
                # Saving without exif= drops all metadata, including GPS.
                copy.save(OUT / f"{name}{suffix}.webp", "WEBP", quality=82, method=6)
            width, height = copy.size  # thumbnail size, used to reserve space in the grid
            entries.append((name, width, height))
            print(f"Saved img/photos/{name}.webp", file=sys.stderr)

    print("\nAdd to _data/photos.yml (newest first), then fill in the captions:\n")
    for name, width, height in entries:
        print(f"- file: {name}\n  title: \"\"\n  place: \"\"\n  year: \n  width: {width}\n  height: {height}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
