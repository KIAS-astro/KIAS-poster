# KIAS Summer School poster

Generates the poster for the KIAS Summer School on Extragalactic Astronomy and
Cosmology — a white layout with a SPHEREx all-sky banner and a SPHEREx
spacecraft, rendered to SVG, PNG, and a print-ready vector PDF.

The engine (`posterkit/`) is year-agnostic. Each year lives under
`years/<year>/` and holds one `poster.yml` (all content and layout settings)
plus its images. To make a new year, copy an existing `years/<year>/` directory
and edit its `poster.yml`.

```
posterkit/          reusable engine
  render.py           builds the SVG and renders SVG/PNG/PDF from poster.yml
  imageprep/          banner + spacecraft image preparation scripts
  assets/             year-invariant assets (KIAS logo, style reference)
years/2026/
  poster.yml          content + layout for the 2026 poster
  images/             SPHEREx sources + cutouts (downloaded, not committed)
  drafts/             generated output (not committed)
```

## Setup

Run these from the repository root (where `pyproject.toml` lives). Use `-e`
(editable) so edits to `posterkit/` take effect without reinstalling.

**Option 1 — conda + pip**
```bash
conda env create -f env.yml       # also runs `pip install -e . --no-deps`
conda activate kias-poster
```

**Option 2 — conda + [uv](https://docs.astral.sh/uv/)**

Same as Option 1, but uv resolves the editable install faster. uv uses the
active conda environment (add `--python "$(which python)"` if it does not detect
it).
```bash
conda env create -f env.yml
conda activate kias-poster
uv pip install -e . --no-deps     # conda already installed the dependencies
```

**Option 3 — uv only (no conda)**

uv installs every dependency from PyPI, so conda is not required. The
dependencies are declared in `pyproject.toml`.
```bash
uv venv --python 3.12
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install -e .
```

Sanity check any option with:
```bash
python -c "import posterkit; print(posterkit.__file__)"
```

Notes:
- `cairosvg` needs the native cairo library. Conda (Options 1 and 2) provides
  it. For the uv-only path on macOS, run `brew install cairo`; on Debian/Ubuntu,
  `apt install libcairo2`.
- Korean text uses the system font "Apple SD Gothic Neo" on macOS. On Linux,
  install a CJK font, e.g. `apt install fonts-noto-cjk`; rendering falls back to
  "Noto Sans CJK KR" automatically.

## Build

```bash
# once after cloning: download SPHEREx source images + rebuild the cutouts
python -m posterkit.imageprep.fetch_images --dir years/2026/images

# render the poster into years/2026/drafts/
python -m posterkit --year years/2026
```

`fetch_images` is needed once after cloning: the SPHEREx all-sky maps and
spacecraft are downloaded (not committed) and the oval cutouts are rebuilt. The
KIAS logo (`posterkit/assets/KIAS-banner.png`) is the only image stored in the
repo.

Outputs land in `years/2026/drafts/` as `*.svg`, `*.png` (2040x2880), and
`*.pdf` (vector; use this for printing — sized for B3 / the ISO 1:√2 family).

## Editing a year

Edit `years/<year>/poster.yml`. It has two sections:

- **`content`** — the words and people, edited every year: title, English
  subtitle, section label, the topics + lecturers, logistics rows (dates, venue,
  audience), organizing committee, contact, footer, and the QR URL.
- **`render`** — layout and assets, edited only when the design changes:
  - `blend` — `craft` (cut-out spacecraft over the oval banner) or `null` (banner only).
  - `center_image` — the oval banner image; set to `null` to drop it.
  - `craft_box`, `craft_flip`, `craft_rotate` — size / position / orientation of the spacecraft.
  - `show_qr`, `qr_url`, `kias_logo` — the bottom-right QR code and logo.

Image paths in `poster.yml` that start with `assets/` resolve under
`posterkit/assets/`; all other paths resolve under the year directory.

## Starting a new year

```bash
cp -r years/2026 years/2027
# edit years/2027/poster.yml, swap in years/2027/images/ as needed
python -m posterkit --year years/2027
```

## Image assets (regenerating)

`fetch_images` downloads the sources and rebuilds everything. The individual
steps, if you want to run them by hand (from the repo root):

```bash
python -m posterkit.imageprep.cut_oval  years/2026/images/SPHEREx_StarsRGB.jpg years/2026/images/SPHEREx_StarsRGB_cut.png
python -m posterkit.imageprep.cut_oval  years/2026/images/SPHEREx_LinesRB.jpg  years/2026/images/SPHEREx_LinesRB_cut.png
python -m posterkit.imageprep.merge_oval years/2026/images/SPHEREx_LinesRB_cut.png years/2026/images/SPHEREx_StarsRGB_cut.png years/2026/images/SPHEREx_Merged_cut.png
```

- `cut_oval` — elliptical alpha mask to drop the black around an all-sky oval.
- `merge_oval` — blends two oval cutouts (left half / right half).

The spacecraft PNG is already transparent; the engine trims it to content at
render time, so there is no separate satellite-cutout step.
