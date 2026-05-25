# 2026 KIAS Summer School poster

Generates the poster for the 2026 KIAS Summer School on Extragalactic Astronomy
and Cosmology — a white layout with a SPHEREx all-sky banner and a SPHEREx
spacecraft, rendered to SVG, PNG, and a print-ready vector PDF.

The generator scripts and images live in `poster/`; the commands below assume
you `cd poster` first (paths like `images/` and `drafts/` are relative to it).

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
- macOS: `brew install cairo` (cairosvg needs it). Korean text uses the system
  font "Apple SD Gothic Neo".
- Linux: install a CJK font, e.g. `apt install fonts-noto-cjk`; the scripts fall
  back to "Noto Sans CJK KR" automatically.

## Build

```bash
cd poster
python fetch_images.py       # downloads SPHEREx source images + builds cutouts
python make_poster.py        # renders the poster into drafts/
```

`fetch_images.py` is needed once after cloning: the SPHEREx all-sky maps and
spacecraft are downloaded (not committed) and the derived cutouts are rebuilt.
`KIAS-banner.png` and the artist scene are stored in the repo.

Outputs land in `drafts/` as `*.svg`, `*.png` (2040x2880), and `*.pdf` (vector;
use this for printing — sized for B3 / the ISO 1:√2 family).

## Editing

Edit the CONTENT block at the top of `make_poster.py` (title, topics, lecturers,
logistics, committee, contact). Key knobs:

- `BLEND` — how the spacecraft appears: `None`, `"watermark"`, `"lower"`,
  `"banner"`, `"craft"` (cut-out over the oval), `"background"` (full-page).
- `CENTER_IMAGE` — the oval banner image; set to `None` to drop it.
- `CRAFT_BOX`, `CRAFT_FLIP`, `CRAFT_ROTATE` — placement of the cut-out spacecraft.
- `BG_TRANSFORM`, `BG_TELE_FRAC`, `BG_ZOOM` — framing of the background spacecraft.
- `TEXT_STROKE`, `CREDIT_COLOR` — legibility tweaks for busy backgrounds.

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
