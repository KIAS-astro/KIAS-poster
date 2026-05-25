# 2026 KIAS Summer School poster

Generates the poster for the 2026 KIAS Summer School on Extragalactic Astronomy
and Cosmology — a white layout with a SPHEREx all-sky banner and a SPHEREx
spacecraft, rendered to SVG, PNG, and a print-ready vector PDF.

Run the **Setup** commands from the repo root (where `env.yml` lives); then
`cd poster` to **build**. The generator scripts live in `poster/` and use paths
like `images/` and `drafts/` relative to it.

## Setup

With conda (recommended):

```bash
conda env create -f env.yml
conda activate kias-poster
```

Or with pip in a virtualenv:

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Notes:
- The conda env includes cairo. For the pip path on macOS, also run
  `brew install cairo` (cairosvg needs it). Korean text uses the system font
  "Apple SD Gothic Neo".
- Linux: install a CJK font, e.g. `apt install fonts-noto-cjk`; the scripts fall
  back to "Noto Sans CJK KR" automatically.

## Build

```bash
cd poster
python fetch_images.py       # downloads SPHEREx source images + builds cutouts
python make_poster.py        # renders the poster into drafts/
```

`fetch_images.py` is needed once after cloning: the SPHEREx all-sky maps and
spacecraft are downloaded (not committed) and the oval cutouts are rebuilt.
`KIAS-banner.png` is the only image stored in the repo.

Outputs land in `drafts/` as `*.svg`, `*.png` (2040x2880), and `*.pdf` (vector;
use this for printing — sized for B3 / the ISO 1:√2 family).

## Editing

Edit the CONTENT block at the top of `make_poster.py`: title, English subtitle,
section label, the three topics + lecturers, the logistics rows (dates, venue,
audience), organizing committee, contact, footer, and the QR URL. Layout knobs:

- `BLEND` — `"craft"` (cut-out spacecraft over the oval banner) or `None` (banner only).
- `CENTER_IMAGE` — the oval banner image; set to `None` to drop it.
- `CRAFT_BOX`, `CRAFT_FLIP`, `CRAFT_ROTATE` — size / position / orientation of the spacecraft.
- `SHOW_QR`, `QR_URL`, `KIAS_LOGO` — the bottom-right QR code and logo.

## Image assets (regenerating)

`fetch_images.py` downloads the sources and rebuilds everything. The individual
steps, if you want to run them by hand:

```bash
python cut_oval.py images/SPHEREx_StarsRGB.jpg images/SPHEREx_StarsRGB_cut.png
python cut_oval.py images/SPHEREx_LinesRB.jpg  images/SPHEREx_LinesRB_cut.png
python merge_oval.py                 # left/right merge -> SPHEREx_Merged_cut.png
```

- `cut_oval.py` — elliptical alpha mask to drop the black around an all-sky oval.
- `merge_oval.py` — blends two oval cutouts (left half / right half).

The spacecraft PNG is already transparent; `make_poster.py` trims it to content
at render time, so there is no separate satellite-cutout step.
