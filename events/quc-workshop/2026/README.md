# QUC Workshop 2026 poster

Poster for the KIAS Quantum Universe Center (QUC) Workshop, 25–27 November
2026, Sono Calm Goyang. `make_poster.py` is a standalone Pillow + numpy
renderer; it does not use `posterkit/render.py` or a `poster.yml`. It takes
the KIAS logo from `posterkit/assets/KIAS-banner.png`.

## Run

From the repository root:

```bash
python events/quc-workshop/2026/make_poster.py                      # 8 versions + contact sheet
python events/quc-workshop/2026/make_poster.py light waves futura   # one version
python events/quc-workshop/2026/make_poster.py patterns             # pattern-only figures
```

Output goes to `events/quc-workshop/2026/drafts/` (gitignored). Needs Pillow,
numpy and contourpy (in `pyproject.toml`).

The fonts are macOS system fonts (Futura, Avenir Next, Helvetica Neue), read
from `/System/Library/Fonts/`. The script runs on macOS only.

## Layout

The layout follows the 2025 poster: QUC / WORKSHOP / 2026 stacked at the top,
a figure in the middle, venue and dates near the bottom with the same
positions and sizes as in 2025, and the footer and KIAS logo at the bottom.
Canvas 2160x3840 px (9:16). All type is sans-serif.

## Versions

A version is theme × background × fonts. The default set is the 8
combinations of the light theme with backgrounds `waves`, `lensing`,
`embedding`, `geodesics` and fonts `futura`, `avenir`.

| background | figure |
|---|---|
| `waves` | interference of circular waves from two coherent sources |
| `lensing` | square grid seen through a point-mass gravitational lens, with the Einstein ring |
| `embedding` | Flamm paraboloid of the Schwarzschild spatial slice, rings at equal proper radial distance |
| `geodesics` | null geodesics bent around a Schwarzschild black hole, photon sphere at 1.5 r_s |

Other backgrounds (`oscillator`, `orbital`, `bloch`), the `blue` theme of the
2025 poster, and the font sets `avenir-light`, `helvetica`, `helvetica-thin`
remain available from the command line.

## Pattern-only figures

`patterns` writes the four figures above without text, for the
commissioned designer, into `drafts/patterns/`:

- `QUC_pattern_<name>.{png,pdf}`: 2160x2160 px preview on white.
- `QUC_pattern_<name>.svg` and `QUC_pattern_<name>_transparent.png`: 3840x3840
  px, large enough to crop a full 2160x3840 poster from any position.
- `QUC_patterns.png`: the four previews in a 2×2 sheet on white, no labels.
  This is the file sent to the designer.

The figures are square on purpose, so they do not read as a finished poster.
