#!/usr/bin/env python3
"""Merge two oval all-sky cutouts into one banner: left image on the left half,
right image on the right half, with a smooth blend across the central meridian.

Both inputs must be the same size (the transparent oval cutouts from
cut_oval.py share the 4012x2012 ellipse).

    python merge_oval.py images/SPHEREx_LinesRB_cut.png \\
                         images/SPHEREx_StarsRGB_cut.png \\
                         images/SPHEREx_Merged_cut.png
"""
import sys

import numpy as np
from PIL import Image

# Fraction of the width over which the two images cross-fade, centered.
BLEND_WIDTH = 0.16


def merge(left_path, right_path, dst_path, blend=BLEND_WIDTH):
    left = Image.open(left_path).convert("RGBA")
    right = Image.open(right_path).convert("RGBA")
    if left.size != right.size:
        right = right.resize(left.size)
    w, h = left.size

    L = np.asarray(left).astype(np.float32)
    R = np.asarray(right).astype(np.float32)

    # weight for the right image: 0 on the left, 1 on the right, smoothstep
    # across a band of width `blend` centered at x = w/2.
    x = np.arange(w, dtype=np.float32)
    t = np.clip((x - w / 2) / (blend * w) + 0.5, 0.0, 1.0)
    wr = (t * t * (3 - 2 * t))[None, :, None]   # smoothstep, shape (1,w,1)

    rgb = L[..., :3] * (1 - wr) + R[..., :3] * wr
    # both cutouts share the same ellipse alpha; blend it too for safety
    a = L[..., 3:] * (1 - wr) + R[..., 3:] * wr
    out = np.concatenate([rgb, a], axis=2).clip(0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(dst_path)
    print(f"wrote {dst_path} {(w, h)}")


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "images/SPHEREx_LinesRB_cut.png"
    b = sys.argv[2] if len(sys.argv) > 2 else "images/SPHEREx_StarsRGB_cut.png"
    c = sys.argv[3] if len(sys.argv) > 3 else "images/SPHEREx_Merged_cut.png"
    merge(a, b, c)
