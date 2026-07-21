# Project: KIAS Summer School poster

Goal: produce the poster for the KIAS Summer School on Extragalactic Astronomy
and Cosmology, styled after `posterkit/assets/2024-Poster.png` — a **white
background** with black title text, a sky-image banner near the top, and
left-aligned logistics and lecture-topic blocks below.

## Layout
- `posterkit/` is the reusable, year-agnostic engine. `years/<year>/` holds one
  year's data. To make a new year, copy an existing `years/<year>/` directory
  and edit its `poster.yml`.
- `posterkit/render.py` — reads `years/<year>/poster.yml`, builds the SVG, and
  renders `<basename>.{svg,png,pdf}` into `years/<year>/drafts/`. Edit
  `poster.yml`, not the engine.
- `posterkit/imageprep/` — image-preparation scripts (`cut_oval.py`,
  `merge_oval.py`, `fetch_images.py`).
- `posterkit/assets/` — year-invariant assets: `KIAS-banner.png` (tracked) and
  `2024-Poster.png` (style reference, gitignored — large).
- `years/<year>/images/` — that year's imagery. The raw SPHEREx sources (two
  JPGs + the spacecraft PNG) are tracked, so the poster survives if the download
  URLs disappear; the derived cutouts (`*_cut.png`) are gitignored and rebuilt
  from the raw sources by `cut_oval`/`merge_oval`. `years/<year>/drafts/` —
  generated output (gitignored).
- `years/<year>/CREDITS.md` — full image credits and acknowledgments for that
  year (only short forms appear on the poster).

## Pipeline
- Standalone repo. `pyproject.toml` is the dependency source; `env.yml` is for
  conda. Install: conda+pip, conda+uv, or uv-only (see README). All install the
  `posterkit` package editable (`pip install -e .`).
- Run everything from the repo root:
  - `python -m posterkit.imageprep.fetch_images --dir years/2026/images` — the
    derived cutouts are gitignored, so rebuild them after cloning. This
    re-downloads the raw sources and rebuilds the cutouts; the tracked raw
    sources are the fallback if the download URLs die.
  - `python -m posterkit --year years/2026` — renders the poster (also available
    as the `kias-poster` console script).

## poster.yml
- Two sections. `content` — words/people, edited every year (title, subtitle,
  section label, topics + 발제 강연자, logistics rows, 조직위원, 문의사항, footer,
  qr_url, image credit, SPHEREx note). `render` — layout/assets, edited only when
  the design changes (blend, center_image, craft_box/flip/rotate, show_qr,
  kias_logo, output_basename).
- Image paths starting with `assets/` resolve under `posterkit/assets/`; all
  other paths resolve under the year directory.

## Imagery
- Banner is a SPHEREx all-sky map (a 2:1 Mollweide ellipse on black).
  `cut_oval.py` removes the black with an elliptical alpha mask, applied to both
  `SPHEREx_StarsRGB.jpg` and `SPHEREx_LinesRB.jpg`.
- `merge_oval.py` blends two oval cutouts into one banner (left half / right
  half with a smooth meridian cross-fade) → `SPHEREx_Merged_cut.png`. The 2026
  `center_image` is that merge: LinesRB (left) into StarsRGB (right).
- The spacecraft `SPHEREx_March2022-Satellite.png` is already a transparent PNG;
  the engine trims it to content at render time (blend `craft`), so there is no
  separate satellite-cutout step.
- QR (bottom-right, with the KIAS logo) encodes the year's `qr_url` (trailing
  slash required for 2026).

## Chosen design (2026)
- The "craft" version: `blend: craft`, `center_image:
  images/SPHEREx_Merged_cut.png`, cut-out spacecraft top-right (flipped to face
  the galaxy). These are the values in `years/2026/poster.yml`.
- Likely print size: B3 (353x500 mm, ISO 1:√2). Canvas 680x960 ≈ 0.708 fits it
  with negligible trim. Print from the vector PDF. If committing to B3, set the
  canvas to exact B3 and bump export resolution / asset sizes (canvas is a
  constant in `render.py`; `BANNER` too).

## Decided content (2026)
- Venue: 양평 수향더한옥 펜션.
- Discussion topics, 발제 강연자, 조직위원, 문의사항 are set in
  `years/2026/poster.yml`.

## Notes
- Verify the SPHEREx image credit before printing (currently NASA/JPL-Caltech).
- Regression check when touching `render.py`: the rendered SVG must stay
  byte-identical for unchanged `poster.yml` (compare `shasum` of the output SVG).
