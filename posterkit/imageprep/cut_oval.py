#!/usr/bin/env python3
"""Cut the black background off an oval (Mollweide / Hammer) all-sky image.

The SPHEREx all-sky map is a 2:1 ellipse sitting on a black rectangle. A plain
black-to-transparent threshold would eat into the dark sky near the ellipse rim
and leave ragged holes, so instead we fit an ellipse to the lit region and use
that as the alpha mask. The result is a transparent PNG cropped tight to the
oval, ready to drop onto any background.

    pip install pillow numpy
    python cut_oval.py images/SPHEREx_StarsRGB.jpg images/SPHEREx_StarsRGB_cut.png
"""
import sys

import numpy as np
from PIL import Image


def cut_oval(src_path, dst_path, lum_threshold=18, feather=0.006, pad=2.0):
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    arr = np.asarray(im)

    # Find the lit region (brightest channel above threshold) and fit an
    # axis-aligned ellipse to its bounding box.
    lit = arr.max(axis=2) > lum_threshold
    ys, xs = np.where(lit)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    ax = (xs.max() - xs.min()) / 2 + pad
    ay = (ys.max() - ys.min()) / 2 + pad

    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - cx) / ax) ** 2 + ((yy - cy) / ay) ** 2)
    alpha = np.clip((1.0 - r) / feather, 0.0, 1.0)  # 1 inside, feathered rim

    rgba = np.dstack([arr, (alpha * 255).astype(np.uint8)])

    # Crop tight to the ellipse bounding box so the PNG is itself ~2:1.
    box = (int(cx - ax), int(cy - ay), int(cx + ax) + 1, int(cy + ay) + 1)
    out = Image.fromarray(rgba, "RGBA").crop(box)
    out.save(dst_path)
    print(f"wrote {dst_path} {out.size}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "images/SPHEREx_StarsRGB.jpg"
    dst = sys.argv[2] if len(sys.argv) > 2 else "images/SPHEREx_StarsRGB_cut.png"
    cut_oval(src, dst)
