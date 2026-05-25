#!/usr/bin/env python3
"""Download the SPHEREx source images and rebuild the derived cutouts.

These images are freely available, so the repo fetches them rather than storing
them. Run once after cloning (and again to refresh):

    python fetch_images.py

Kept in the repo instead (no public URL): KIAS-banner.png. The optional
background/watermark/lower BLEND modes additionally need an artist scene at
images/SPHEREx_March2022.jpg; it is neither downloaded nor committed, so supply
it yourself to use those modes (the default "craft" poster does not need it).
"""
import os
import urllib.request

from cut_oval import cut_oval
from merge_oval import merge

IMAGES = "images"

SOURCES = {
    "SPHEREx_LinesRB.jpg":
        "https://www.astropix.org/archive/spherex/spherex20251218c/spherex_spherex20251218c_3000.jpg",
    "SPHEREx_StarsRGB.jpg":
        "https://www.astropix.org/archive/spherex/spherex20251218b/spherex_spherex20251218b_3000.jpg",
    "SPHEREx_March2022-Satellite.png":   # already a transparent cutout
        "https://spherex.caltech.edu/download/MediaFile/17/binary/large",
}


def download(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r, open(dst, "wb") as f:
        f.write(r.read())
    print("downloaded", dst)


def main():
    os.makedirs(IMAGES, exist_ok=True)
    for name, url in SOURCES.items():
        download(url, os.path.join(IMAGES, name))

    # Rebuild the derived cutouts used by the poster.
    cut_oval(f"{IMAGES}/SPHEREx_StarsRGB.jpg", f"{IMAGES}/SPHEREx_StarsRGB_cut.png")
    cut_oval(f"{IMAGES}/SPHEREx_LinesRB.jpg",  f"{IMAGES}/SPHEREx_LinesRB_cut.png")
    merge(f"{IMAGES}/SPHEREx_LinesRB_cut.png",
          f"{IMAGES}/SPHEREx_StarsRGB_cut.png",
          f"{IMAGES}/SPHEREx_Merged_cut.png")
    # The spacecraft (SPHEREx_March2022-Satellite.png) is already transparent;
    # make_poster.py trims it at render time, so no cutout step is needed here.


if __name__ == "__main__":
    main()
