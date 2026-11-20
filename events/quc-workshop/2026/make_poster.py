#!/usr/bin/env python3
"""QUC Workshop 2026 poster (Quantum Universe Center, KIAS).

Renders 2160x3840 PNG + PDF versions into drafts/. Every version
stacks QUC / WORKSHOP / 2026 at the top, as on the 2025 poster, puts a
figure in the middle and the dates and venue near the bottom. A version is a
combination of
  theme      light   - white paper, black type
             blue    - the blue of the 2025 poster, white type
  background waves      - circular waves from two coherent sources
             oscillator - quantum harmonic oscillator densities |psi_n|^2
                          stacked at their energies inside the potential
             orbital    - density contours of the hydrogen 4f (m = 0) orbital
             lensing    - a square grid seen through a point-mass gravitational lens
             embedding  - Flamm paraboloid of the Schwarzschild spatial slice
             geodesics  - null geodesics bent around a Schwarzschild black hole
             bloch      - Bloch sphere with a qubit state vector
  fonts      futura, avenir, avenir-light, helvetica, helvetica-thin
             (geometric and neo-grotesque sans-serif faces shipped with macOS)
Every background also carries a dot field: a crystal lattice at the bottom
that loosens into a random star field toward the top.

    python make_poster.py                                # curated set + contact sheet
    python make_poster.py light waves futura             # one version
    python make_poster.py patterns                       # pattern-only figures

Needs Pillow, numpy and contourpy, and the macOS system fonts above.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "drafts"
KIAS_LOGO = HERE.parents[2] / "posterkit" / "assets" / "KIAS-banner.png"

W, H = 2160, 3840
MARGIN = 150

SUP = "/System/Library/Fonts/Supplemental/"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
HELVETICA = "/System/Library/Fonts/HelveticaNeue.ttc"
AVENIR_BOLD, AVENIR_DEMI, AVENIR_MEDIUM, AVENIR_REGULAR, AVENIR_ULTRALIGHT = (
    (AVENIR, i) for i in (0, 2, 5, 7, 10))
HELV_REGULAR, HELV_BOLD, HELV_LIGHT, HELV_MEDIUM, HELV_THIN = (
    (HELVETICA, i) for i in (0, 1, 7, 10, 12))
FUTURA = (SUP + "Futura.ttc", 0)

FONTSETS = {
    "futura": dict(title=FUTURA, year=FUTURA, info=AVENIR_MEDIUM, foot=AVENIR_BOLD,
                   ws_track=0.06),
    "avenir": dict(title=AVENIR_MEDIUM, year=AVENIR_MEDIUM, info=AVENIR_MEDIUM,
                   foot=AVENIR_BOLD, ws_track=0.06),
    "avenir-light": dict(title=AVENIR_ULTRALIGHT, year=AVENIR_REGULAR, info=AVENIR_MEDIUM,
                         foot=AVENIR_BOLD, ws_track=0.06),
    "helvetica": dict(title=HELV_MEDIUM, year=HELV_MEDIUM, info=HELV_REGULAR,
                      foot=HELV_BOLD, ws_track=0.05),
    "helvetica-thin": dict(title=HELV_THIN, year=HELV_LIGHT, info=HELV_REGULAR,
                           foot=HELV_BOLD, ws_track=0.05),
}

VERSIONS = [
    (theme, bg, fonts)
    for bg in ("waves", "lensing", "embedding", "geodesics")
    for theme in ("light",)
    for fonts in ("futura", "avenir")
]

EARLIER_VERSIONS = [
    ("light", "waves", "avenir-light"),
    ("blue", "waves", "futura"),
    ("light", "oscillator", "helvetica-thin"),
    ("light", "orbital", "avenir"),
    ("blue", "lensing", "avenir-light"),
    ("light", "bloch", "helvetica-thin"),
    ("blue", "orbital", "futura"),
    ("blue", "oscillator", "helvetica"),
    ("light", "lensing", "futura"),
    ("light", "waves", "helvetica"),
    ("light", "bloch", "avenir-light"),
    ("blue", "lensing", "avenir"),
]

VENUE_LINES = ["SONO CALM GOYANG", "WEST TOWER 2F, LILAC HALL 1"]
DATE_LINE = "NOVEMBER 25 – 27, 2026"
FOOTER_LINES = ["KOREA INSTITUTE", "FOR ADVANCED STUDY"]
YEAR = "2026"

# Text block geometry measured on the 2025 poster (pixels on the 2160x3840 canvas).
VENUE_BASES = [2617, 2737]
DATE_BASE = 3011
TEXT_CAP = 60
TEXT_TRACK_EM = 0.1
FOOT_X = 218
FOOT_BASES = [3556, 3629]
FOOT_CAP = 42
LOGO_HEIGHT, LOGO_RIGHT, LOGO_BOTTOM = 191, 1962, 3639

THEMES = {
    "light": dict(bg_center=(255, 255, 255), bg_edge=(255, 255, 255),
                  ink=(17, 17, 17), line=(120, 120, 120), line_alpha=1.0),
    "blue": dict(bg_center=(6, 128, 228), bg_edge=(4, 74, 150),
                 ink=(255, 255, 255), line=(255, 255, 255), line_alpha=0.42),
}

WAVELENGTH = 46.0
SOURCE_SEPARATION = 520
FADE_RADIUS = 1000.0
LATTICE_SPACING = 46.0
LATTICE_Y0, LATTICE_Y1 = 3500.0, 1900.0


def font(face, size):
    return ImageFont.truetype(face[0], size, index=face[1])


def draw_tracked(draw, xy, text, fnt, tracking, fill):
    """Draw text with extra letter spacing, keeping the font's pair kerning."""
    x0, y0 = xy
    for i, ch in enumerate(text):
        x = x0 + fnt.getlength(text[:i]) + i * tracking
        draw.text((x, y0), ch, font=fnt, fill=fill, anchor="ls")


def tracked_width(text, fnt, tracking):
    return fnt.getlength(text) + tracking * (len(text) - 1)


def fit_size(face, text, width, tracking_em=0.0):
    """Font size whose ink width of `text` equals `width`."""
    lo, hi = 10, 2000
    while hi - lo > 1:
        mid = (lo + hi) // 2
        l, _, r, _ = font(face, mid).getbbox(text, anchor="ls")
        ink = (r - l) + tracking_em * mid * (len(text) - 1)
        lo, hi = (mid, hi) if ink <= width else (lo, mid)
    return lo


def wave_layer(center):
    """Alpha map (0-1) of ring wavefronts from two coherent sources."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = center
    sources = (cx - SOURCE_SEPARATION / 2, cx + SOURCE_SEPARATION / 2)
    alpha = np.zeros((H, W), np.float32)
    radii = []
    for sx in sources:
        r = np.hypot(xx - sx, yy - cy)
        radii.append(r)
        dist = np.abs(r - WAVELENGTH * np.round(r / WAVELENGTH))
        ring = np.clip(1.0 - dist / 2.6, 0.0, 1.0)
        ring *= np.exp(-((r / FADE_RADIUS) ** 2))
        ring[r < WAVELENGTH * 0.5] = 0.0
        alpha = np.maximum(alpha, ring)
    fringe = np.cos(np.pi * (radii[0] - radii[1]) / WAVELENGTH) ** 2
    rc = np.hypot(xx - cx, yy - cy)
    alpha += 0.06 * fringe * np.exp(-((rc / (1.3 * FADE_RADIUS)) ** 2))
    return np.clip(alpha, 0.0, 1.0)


def hermite_densities(n_max, xi):
    """|psi_n(xi)|^2 for n = 0..n_max, from the normalized recurrence."""
    psi = np.zeros((n_max + 1, xi.size))
    psi[0] = np.pi ** -0.25 * np.exp(-xi ** 2 / 2)
    if n_max > 0:
        psi[1] = np.sqrt(2.0) * xi * psi[0]
    for n in range(2, n_max + 1):
        psi[n] = np.sqrt(2.0 / n) * xi * psi[n - 1] - np.sqrt((n - 1) / n) * psi[n - 2]
    return psi ** 2


def oscillator_layer(y_ground, y_top, n_max=34):
    """Energy ladder: |psi_n|^2 drawn on the level E_n, inside V = xi^2 / 2."""
    s = 2
    img = Image.new("L", (W * s, H * s), 0)
    d = ImageDraw.Draw(img)
    xi_max = np.sqrt(2 * n_max + 1) * 1.08
    xs = np.linspace(-120, W + 120, 1400)
    xi = (xs - W / 2) / ((W / 2 + 60) / xi_max)
    dens = hermite_densities(n_max, xi)
    dy = (y_ground - y_top) / (n_max + 0.5)
    amp = 3.2 * dy / dens[0].max()

    def energy_y(e):
        return y_ground - (e - 0.5) * dy

    for n in range(n_max + 1):
        base = energy_y(n + 0.5)
        ys = base - amp * dens[n] * (1 + 0.5 * np.sqrt(n))
        fade = 0.35 + 0.65 * np.exp(-n / 18)
        pts = list(zip(s * xs, s * ys))
        d.line(pts, fill=int(255 * fade), width=int(2.4 * s), joint="curve")
        d.line([(0, s * base), (W * s, s * base)], fill=int(70 * fade), width=s)
    ys = energy_y(xi ** 2 / 2)
    keep = ys > y_top - 200
    d.line(list(zip(s * xs[keep], s * ys[keep])), fill=255, width=int(3.2 * s), joint="curve")
    img = img.resize((W, H), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32) / 255.0


def contour_lines(f, spacing, width=1.3, mask=None):
    """Anti-aliased lines along f = k * spacing, with constant pixel width."""
    gy, gx = np.gradient(f)
    g = np.hypot(gx, gy) + 1e-9
    dist = np.abs(f - spacing * np.round(f / spacing)) / g
    lines = np.clip(1.0 - dist / width, 0.0, 1.0)
    if mask is not None:
        lines *= mask
    return lines


def orbital_layer(center, scale=34.0):
    """Hydrogen 4f (m = 0) density in the x-z plane, drawn as log-density contours."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    x = (xx - center[0]) / scale
    z = -(yy - center[1]) / scale
    r = np.hypot(x, z) + 1e-6
    c = z / r
    rho = r ** 6 * np.exp(-r / 2) * (5 * c ** 3 - 3 * c) ** 2
    rho /= rho.max()
    f = np.log(rho + 1e-12)
    mask = np.clip((f + 9.0) / 1.5, 0, 1)
    lines = contour_lines(f, 0.55, mask=mask)
    lines *= 0.45 + 0.55 * np.clip(rho * 4, 0, 1)
    return lines.astype(np.float32)


def lensing_layer(center, theta_e=430.0, spacing=70.0):
    """Square grid behind a point-mass lens, mapped to the image plane."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    dx, dy = xx - center[0], yy - center[1]
    r2 = dx ** 2 + dy ** 2 + 30.0 ** 2
    bx = dx - theta_e ** 2 * dx / r2
    by = dy - theta_e ** 2 * dy / r2
    fade = np.exp(-(r2 / (1.6 * 1000.0) ** 2))
    lines = np.maximum(contour_lines(bx, spacing), contour_lines(by, spacing))
    ring = np.clip(1.0 - np.abs(np.sqrt(r2) - theta_e) / 1.6, 0, 1)
    out = np.maximum(lines * fade, 0.8 * ring)
    out *= np.clip((np.sqrt(r2) - 0.3 * theta_e) / (0.25 * theta_e), 0, 1)
    return out.astype(np.float32)


def bloch_layer(center, radius=760.0, tilt=0.32, state=(0.85, 0.75)):
    """Wireframe Bloch sphere (orthographic view) with a state vector."""
    s = 2
    img = Image.new("L", (W * s, H * s), 0)
    d = ImageDraw.Draw(img)
    cx, cy = center
    ct, st = np.cos(tilt), np.sin(tilt)

    def project(x, y, z):
        return cx + radius * x, cy - radius * (z * ct - y * st), y * ct + z * st

    def curve(x, y, z, front=210, back=70, width=2.4):
        px, py, depth = project(x, y, z)
        for i in range(len(px) - 1):
            v = front if depth[i] <= 0 else back
            d.line([(s * px[i], s * py[i]), (s * px[i + 1], s * py[i + 1])],
                   fill=v, width=int(width * s))

    t = np.linspace(0, 2 * np.pi, 721)
    for lat in np.radians([-60, -30, 0, 30, 60]):
        curve(np.cos(lat) * np.cos(t), np.cos(lat) * np.sin(t), np.full_like(t, np.sin(lat)),
              width=3.2 if lat == 0 else 2.2)
    for lon in np.radians(np.arange(0, 180, 30)):
        curve(np.cos(t) * np.cos(lon), np.cos(t) * np.sin(lon), np.sin(t))
    curve(np.cos(t), np.zeros_like(t), np.sin(t), front=255, back=255, width=0.1)
    d.ellipse((s * (cx - radius), s * (cy - radius), s * (cx + radius), s * (cy + radius)),
              outline=255, width=int(3.4 * s))

    for axis in [(0, 0, 1.25), (0, 0, -1.25), (1.25, 0, 0), (-1.25, 0, 0)]:
        px, py, _ = project(*[np.array([0.0, a]) for a in axis])
        d.line([(s * px[0], s * py[0]), (s * px[1], s * py[1])], fill=150, width=int(1.6 * s))

    theta, phi = state
    v = np.array([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)])
    px, py, _ = project(*[np.array([0.0, c]) for c in v])
    d.line([(s * px[0], s * py[0]), (s * px[1], s * py[1])], fill=255, width=int(5 * s))
    ang = np.arctan2(py[1] - py[0], px[1] - px[0])
    head = 34
    tip = (px[1], py[1])
    left = (tip[0] - head * np.cos(ang - 0.4), tip[1] - head * np.sin(ang - 0.4))
    right = (tip[0] - head * np.cos(ang + 0.4), tip[1] - head * np.sin(ang + 0.4))
    d.polygon([(s * p[0], s * p[1]) for p in (tip, left, right)], fill=255)
    r_dot = 12
    d.ellipse((s * (tip[0] - r_dot), s * (tip[1] - r_dot), s * (tip[0] + r_dot),
               s * (tip[1] + r_dot)), outline=255, width=int(2 * s))
    img = img.resize((W, H), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32) / 255.0


def split_runs(xs, ys, keep):
    """Split a polyline into the runs where `keep` is true."""
    out, start = [], None
    for i, k in enumerate(list(keep) + [False]):
        if k and start is None:
            start = i
        elif not k and start is not None:
            if i - start > 1:
                out.append((xs[start:i], ys[start:i]))
            start = None
    return out


def draw_strokes(strokes, size=(W, H)):
    """Raster alpha map (0-1) of strokes given as (xs, ys, value 0-255, width px)."""
    s = 2
    img = Image.new("L", (size[0] * s, size[1] * s), 0)
    d = ImageDraw.Draw(img)
    for xs, ys, v, wdt in strokes:
        d.line(list(zip(s * np.asarray(xs), s * np.asarray(ys))), fill=int(v),
               width=max(1, int(round(wdt * s))), joint="curve")
    img = img.resize(size, Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32) / 255.0


def write_svg(path, strokes, size, offset=(0.0, 0.0)):
    """Strokes as SVG polylines (black, opacity from value), shifted by -offset."""
    ox, oy = offset
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" '
             f'viewBox="0 0 {size[0]} {size[1]}">',
             f'<rect width="{size[0]}" height="{size[1]}" fill="none"/>',
             '<g fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">']
    for xs, ys, v, wdt in strokes:
        pts = " ".join(f"{x - ox:.1f},{y - oy:.1f}" for x, y in zip(xs, ys))
        lines.append(f'<polyline points="{pts}" stroke-width="{wdt:.2f}" '
                     f'stroke-opacity="{v / 255:.3f}"/>')
    lines.append("</g></svg>")
    Path(path).write_text("\n".join(lines))


def wave_strokes(center, r_max=2600.0):
    """Wavefronts of wave_layer as circles, opacity following the same Gaussian fade."""
    cx, cy = center
    t = np.linspace(0, 2 * np.pi, 721)
    strokes = []
    for sx in (cx - SOURCE_SEPARATION / 2, cx + SOURCE_SEPARATION / 2):
        for n in range(1, int(r_max / WAVELENGTH) + 1):
            r = n * WAVELENGTH
            v = 255 * np.exp(-((r / FADE_RADIUS) ** 2))
            if v < 4:
                break
            strokes.append((sx + r * np.cos(t), cy + r * np.sin(t), v, 2.6))
    return strokes


def lensing_strokes(center, theta_e=430.0, spacing=70.0, bounds=(0, 0, W, H)):
    """Grid lines of lensing_layer, traced as contours of the source-plane coordinates."""
    import contourpy

    cx, cy = center
    step = 2.0
    x0, y0, x1, y1 = bounds
    xx, yy = np.meshgrid(np.arange(x0, x1 + step, step), np.arange(y0, y1 + step, step))
    dx, dy = xx - cx, yy - cy
    r2 = dx ** 2 + dy ** 2 + 30.0 ** 2
    bx = dx - theta_e ** 2 * dx / r2
    by = dy - theta_e ** 2 * dy / r2
    strokes = []
    for field in (bx, by):
        gen = contourpy.contour_generator(xx, yy, field)
        k_lo, k_hi = int(field.min() // spacing), int(field.max() // spacing) + 1
        for k in range(k_lo, k_hi + 1):
            for seg in gen.lines(k * spacing):
                xs, ys = seg[:, 0], seg[:, 1]
                rr = np.hypot(xs - cx, ys - cy)
                keep = rr > 0.45 * theta_e
                for rx, ry in split_runs(xs, ys, keep):
                    for i in range(0, len(rx) - 1, 24):
                        px, py = rx[i:i + 25], ry[i:i + 25]
                        r_mid = np.hypot(px.mean() - cx, py.mean() - cy)
                        v = 255 * np.exp(-((r_mid / 1600.0) ** 2))
                        if v > 4:
                            strokes.append((px, py, v, 1.3))
    t = np.linspace(0, 2 * np.pi, 721)
    strokes.append((cx + theta_e * np.cos(t), cy + theta_e * np.sin(t), 204, 1.6))
    return strokes


def flamm_strokes(center, r_max=11.0, scale=95.0, elevation=0.30):
    """Schwarzschild embedding diagram, z = 2 sqrt(r_s (r - r_s)), in units of r_s.

    Circles are spaced by equal proper radial distance along the surface. The far
    side of the funnel is drawn fainter than the near side.
    """
    cx, cy = center
    se, ce = np.sin(elevation), np.cos(elevation)
    z_top = 2 * np.sqrt(r_max - 1)

    def project(r, phi):
        x, y = r * np.cos(phi), r * np.sin(phi)
        h = 2 * np.sqrt(np.maximum(r - 1, 0)) - z_top
        return cx + scale * x, cy - scale * (y * se + h * ce) - 0.5 * scale * z_top * ce, y

    strokes = []

    def add(px, py, depth_y, front, back, width):
        near = depth_y < 0
        for xs, ys in split_runs(px, py, near):
            strokes.append((xs, ys, front, width))
        for xs, ys in split_runs(px, py, ~near):
            strokes.append((xs, ys, back, width))

    # proper radial distance l(r) = sqrt(r(r-1)) + ln(sqrt(r) + sqrt(r-1))
    r_fine = np.linspace(1.0, r_max, 4000)
    ell = np.sqrt(r_fine * (r_fine - 1)) + np.log(np.sqrt(r_fine) + np.sqrt(r_fine - 1))
    rings = np.interp(np.linspace(0, ell[-1], 30), ell, r_fine)

    phi = np.linspace(0, 2 * np.pi, 721)
    for r in rings:
        px, py, y = project(np.full_like(phi, r), phi)
        fade = 0.45 + 0.55 * (r / r_max)
        add(px, py, y, 230 * fade, 90 * fade, 2.2)
    rr = np.linspace(1.0, r_max, 600)
    for ang in np.radians(np.arange(0, 360, 10)):
        px, py, y = project(rr, np.full_like(rr, ang))
        add(px, py, y, 210, 80, 1.8)
    return strokes


def flamm_layer(center, r_max=11.0, scale=95.0, elevation=0.30):
    return draw_strokes(flamm_strokes(center, r_max, scale, elevation))


def null_geodesic(b, r_start=60.0, h=0.002):
    """Schwarzschild light ray with impact parameter b (units of r_s), entering from +y.

    Integrates u'' = -u + (3/2) u^2 with u = r_s / r (RK4 in phi). Stops at the
    horizon or when the ray is back at r = 2 r_start.
    """
    u = 1.0 / r_start
    du = np.sqrt(max(1.0 / b ** 2 - u ** 2 + u ** 3, 0.0))
    phi = np.arcsin(b / r_start)
    pts = []

    def f(u_, du_):
        return du_, -u_ + 1.5 * u_ ** 2

    for _ in range(20000):
        pts.append((phi, u))
        k1 = f(u, du)
        k2 = f(u + 0.5 * h * k1[0], du + 0.5 * h * k1[1])
        k3 = f(u + 0.5 * h * k2[0], du + 0.5 * h * k2[1])
        k4 = f(u + h * k3[0], du + h * k3[1])
        u += h * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]) / 6
        du += h * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]) / 6
        phi += h
        if u >= 1.0 or u <= 1.0 / (2 * r_start):
            pts.append((phi, min(max(u, 1e-6), 1.0)))
            break
    phi_a, u_a = np.array(pts).T
    r = 1.0 / u_a
    return r * np.sin(phi_a), r * np.cos(phi_a)


def geodesic_strokes(center, scale=88.0, b_max=11.5):
    """Parallel beam of light rays past a Schwarzschild black hole, with the
    photon sphere (1.5 r_s) and the horizon (r_s) drawn as circles."""
    cx, cy = center
    b_crit = 1.5 * np.sqrt(3)
    n_rays = int(round((b_max - 0.3) / ((11.5 - 0.3) / 23))) + 1
    b_values = np.sort(np.concatenate([np.linspace(0.3, b_max, n_rays),
                                       b_crit + np.geomspace(0.3, 1e-5, 9)]))
    strokes = []
    for b in b_values:
        x, y = null_geodesic(b)
        v = 200 if abs(b - b_crit) < 0.31 else 165
        for sign in (1, -1):
            strokes.append((cx + sign * scale * x, cy - scale * y, v, 1.8))
    t = np.linspace(0, 2 * np.pi, 721)
    for r, v, wdt in [(1.5, 120, 1.6), (1.0, 255, 3.0)]:
        strokes.append((cx + r * scale * np.cos(t), cy + r * scale * np.sin(t), v, wdt))
    return strokes


def geodesic_layer(center, scale=88.0):
    return draw_strokes(geodesic_strokes(center, scale))


def dot_layer(seed=2026):
    """Triangular lattice at the bottom that loosens into a random star field at the top."""
    rng = np.random.default_rng(seed)
    a = LATTICE_SPACING
    rows = np.arange(-2, H / (a * np.sqrt(3) / 2) + 2)
    cols = np.arange(-2, W / a + 2)
    jj, ii = np.meshgrid(rows, cols, indexing="ij")
    x0 = ((ii + 0.5 * (jj % 2)) * a).ravel()
    y0 = (jj * a * np.sqrt(3) / 2).ravel()

    t = np.clip((LATTICE_Y0 - y0) / (LATTICE_Y0 - LATTICE_Y1), 0.0, 1.0)
    disorder = t * t * (3 - 2 * t)
    keep = rng.uniform(0, 1, x0.size) > 0.75 * disorder
    x0, y0, disorder = x0[keep], y0[keep], disorder[keep]
    n = x0.size
    xs = x0 + disorder * rng.uniform(-6 * a, 6 * a, n)
    ys = y0 + disorder * rng.uniform(-6 * a, 6 * a, n)
    star = 1.5 + 6.0 * rng.pareto(2.5, n).clip(0, 1.5)
    sizes = (1 - disorder) * 3.2 + disorder * 0.6 * star
    levels = (1 - disorder) * 190 + disorder * rng.uniform(60, 200, n)

    img = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(img)
    for x, y, r, v in zip(2 * xs, 2 * ys, 2 * sizes, levels):
        d.ellipse((x - r, y - r, x + r, y + r), fill=int(v))
    img = img.resize((W, H), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32) / 255.0


def text_shield(boxes, pad=40, blur=50):
    """Mask that is 1 over text boxes, used to thin the background there."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for l, t, r, b in boxes:
        d.rectangle((l - pad, t - pad, r + pad, b + pad), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m, np.float32) / 255.0


def background(theme):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / W, (yy - 0.45 * H) / H)
    t = np.clip(r / 0.75, 0, 1)[..., None]
    c0 = np.array(theme["bg_center"], np.float32)
    c1 = np.array(theme["bg_edge"], np.float32)
    return c0 * (1 - t) + c1 * t


def logo_image(height, theme):
    """KIAS logo recolored: dark parts take the ink color, light parts the paper color."""
    logo = Image.open(KIAS_LOGO).convert("RGBA")
    a = np.asarray(logo, np.float32)
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0
    light = (lum > 0.8)[..., None]
    rgb = np.where(light, np.array(theme["bg_edge"]), np.array(theme["ink"]))
    out = np.dstack([rgb.astype(np.uint8), a[..., 3].astype(np.uint8)])
    img = Image.fromarray(out, "RGBA")
    w = round(img.width * height / img.height)
    return img.resize((w, height), Image.Resampling.LANCZOS)


def render(theme_name, bg_name, fontset_name):
    theme = THEMES[theme_name]
    fs = FONTSETS[fontset_name]
    ink = theme["ink"]
    text_w = W - 2 * MARGIN

    quc = font(fs["title"], fit_size(fs["title"], "QUC", text_w))
    ws_size = fit_size(fs["title"], "WORKSHOP", text_w, fs["ws_track"])
    ws = font(fs["title"], ws_size)
    ws_track = fs["ws_track"] * ws_size
    def cap(fnt, text):
        return -fnt.getbbox(text, anchor="ls")[1]

    def size_for_cap(face, target):
        size = 10
        while cap(font(face, size + 1), "H") <= target:
            size += 1
        return size

    info = font(fs["info"], size_for_cap(fs["info"], TEXT_CAP))
    track = TEXT_TRACK_EM * info.size
    foot = font(fs["foot"], size_for_cap(fs["foot"], FOOT_CAP))
    foot_track = 0.02 * foot.size

    quc_cap = cap(quc, "UC")
    quc_desc = quc.getbbox("QUC", anchor="ls")[3]
    ws_cap = cap(ws, "WORKSHOP")
    yr_size = 10
    while cap(font(fs["year"], yr_size + 2), YEAR) < 1.45 * ws_cap:
        yr_size += 2
    yr = font(fs["year"], yr_size)
    yr_track = 0.08 * yr_size

    quc_base = 250 + quc_cap
    ws_base = quc_base + max(0.2 * quc_cap, quc_desc + 0.6 * ws_cap) + ws_cap
    yr_base = ws_base + 0.5 * ws_cap + cap(yr, YEAR)
    quc_x = MARGIN - quc.getbbox("QUC", anchor="ls")[0]
    ws_x = MARGIN - ws.getbbox("W", anchor="ls")[0]
    yr_w = tracked_width(YEAR, yr, yr_track)
    yr_x = (W - yr_w) / 2 - yr.getbbox(YEAR[0], anchor="ls")[0]

    info_lines = VENUE_LINES + [DATE_LINE]
    info_base = VENUE_BASES + [DATE_BASE]
    info_x = [(W - tracked_width(s, info, track)) / 2 for s in info_lines]

    fig_top, fig_bottom = yr_base + 120, VENUE_BASES[0] - TEXT_CAP - 120
    fig_center = (W / 2, (fig_top + fig_bottom) / 2)
    fig_half = (fig_bottom - fig_top) / 2

    info_boxes = [(x, y - TEXT_CAP, x + tracked_width(s, info, track), y + 15)
                  for x, y, s in zip(info_x, info_base, info_lines)]
    foot_w = max(tracked_width(s, foot, foot_track) for s in FOOTER_LINES)
    boxes = info_boxes + [
        (MARGIN, quc_base - quc_cap, W - MARGIN, yr_base + 10),
        (FOOT_X, FOOT_BASES[0] - FOOT_CAP, FOOT_X + foot_w, FOOT_BASES[-1] + 10),
    ]

    if bg_name == "waves":
        figure = wave_layer((fig_center[0], fig_center[1] + 0.1 * fig_half))
    elif bg_name == "oscillator":
        figure = 0.75 * oscillator_layer(fig_bottom + 80, fig_top + 40)
    elif bg_name == "orbital":
        figure = orbital_layer(fig_center, scale=fig_half / 17.0)
    elif bg_name == "lensing":
        figure = lensing_layer(fig_center, theta_e=0.6 * fig_half)
    elif bg_name == "embedding":
        figure = flamm_layer((W / 2, fig_center[1] + 0.35 * fig_half), r_max=16.0, scale=80.0,
                             elevation=0.55)
    elif bg_name == "geodesics":
        figure = geodesic_layer((W / 2, fig_center[1] - 0.2 * fig_half), scale=62.0)
        rows = np.arange(H, dtype=np.float32)[:, None]
        figure = figure * np.clip((rows - (yr_base - 150)) / 300.0, 0, 1)
    else:
        figure = bloch_layer(fig_center, radius=1.05 * fig_half)
    alpha = np.maximum(figure, 0.6 * dot_layer())
    alpha *= 1.0 - 0.7 * text_shield(boxes)
    alpha = (alpha * theme["line_alpha"])[..., None]

    rgb = background(theme) * (1 - alpha) + np.array(theme["line"], np.float32) * alpha
    canvas = Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB")

    d = ImageDraw.Draw(canvas)
    d.text((quc_x, quc_base), "QUC", font=quc, fill=ink, anchor="ls")
    draw_tracked(d, (ws_x, ws_base), "WORKSHOP", ws, ws_track, ink)
    draw_tracked(d, (yr_x, yr_base), YEAR, yr, yr_track, ink)
    for x, y, s in zip(info_x, info_base, info_lines):
        draw_tracked(d, (x, y), s, info, track, ink)
    for y, s in zip(FOOT_BASES, FOOTER_LINES):
        draw_tracked(d, (FOOT_X, y), s, foot, foot_track, ink)

    logo = logo_image(LOGO_HEIGHT, theme)
    canvas.paste(logo, (LOGO_RIGHT - logo.width, LOGO_BOTTOM - logo.height), logo)
    return canvas


def contact_sheet(paths, cols=4, thumb_w=540):
    thumb_h = thumb_w * H // W
    gap, label_h = 30, 60
    rows = -(-len(paths) // cols)
    sheet = Image.new("RGB", (cols * (thumb_w + gap) + gap,
                              rows * (thumb_h + label_h + gap) + gap), (235, 235, 235))
    d = ImageDraw.Draw(sheet)
    lab = font(AVENIR_MEDIUM, 28)
    for k, p in enumerate(paths):
        x = gap + (k % cols) * (thumb_w + gap)
        y = gap + (k // cols) * (thumb_h + label_h + gap)
        sheet.paste(Image.open(p).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
        d.text((x, y + thumb_h + 14), p.stem.replace("QUC_Workshop_2026_", ""),
               font=lab, fill=(40, 40, 40))
    out = OUT_DIR / "QUC_Workshop_2026_versions.png"
    sheet.save(out)
    return out


def render_patterns():
    """Pattern-only figures (no text, logo or dots).

    Per pattern: a W x W preview on white (PNG and PDF), and a BIG x BIG square
    as editable SVG vector lines and as a PNG with a transparent background.
    BIG equals the poster height, so a full 9:16 poster crop fits inside it.
    """
    out_dir = OUT_DIR / "patterns"
    out_dir.mkdir(parents=True, exist_ok=True)
    big = H
    center = (W / 2, H / 2)
    emb = dict(center=(W / 2, H * 0.60), r_max=16.0, scale=118.0, elevation=0.55)
    geo = dict(center=(W / 2, H * 0.36), scale=95.0)

    def big_bounds(cy):
        return (W / 2 - big / 2, cy - big / 2, W / 2 + big / 2, cy + big / 2)

    layers = {
        "interference": (wave_layer(center), wave_strokes(center), H / 2),
        "lensing": (lensing_layer(center, theta_e=430.0),
                    lensing_strokes(center, theta_e=430.0, bounds=big_bounds(H / 2)), H / 2),
        "embedding": (flamm_layer(**emb), flamm_strokes(**emb), 2035),
        "geodesics": (geodesic_layer(**geo),
                      geodesic_strokes(**geo, b_max=0.5 * big / geo["scale"] + 1), 1700),
    }
    ink = 40.0
    paths = []
    for name, (alpha, strokes, crop_y) in layers.items():
        x0, y0, _, _ = big_bounds(crop_y)
        shifted = [(np.asarray(xs) - x0, np.asarray(ys) - y0, v, wdt)
                   for xs, ys, v, wdt in strokes]
        write_svg(out_dir / f"QUC_pattern_{name}.svg", shifted, (big, big))
        a_big = draw_strokes(shifted, size=(big, big))
        a8 = (a_big * (255.0 - ink)).clip(0, 255).astype(np.uint8)
        rgba = np.dstack([np.zeros((big, big, 3), np.uint8), a8])
        Image.fromarray(rgba, "RGBA").save(out_dir / f"QUC_pattern_{name}_transparent.png",
                                           dpi=(300, 300))
        top = int(np.clip(crop_y - W / 2, 0, H - W))
        alpha = alpha[top:top + W]
        gray = 255.0 - alpha * (255.0 - ink)
        img = Image.fromarray(gray.clip(0, 255).astype(np.uint8), "L")
        png = out_dir / f"QUC_pattern_{name}.png"
        img.save(png, dpi=(300, 300))
        img.save(png.with_suffix(".pdf"), resolution=300)
        paths.append(png)
        print(png)

    cols, gap, label_h = 2, 60, 0
    thumb_w = thumb_h = 1080
    rows = -(-len(paths) // cols)
    sheet = Image.new("L", (cols * thumb_w + (cols + 1) * gap,
                            rows * (thumb_h + label_h + gap) + gap), 255)
    for k, p in enumerate(paths):
        x = gap + (k % cols) * (thumb_w + gap)
        y = gap + (k // cols) * (thumb_h + label_h + gap)
        sheet.paste(Image.open(p).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
    out = out_dir / "QUC_patterns.png"
    sheet.save(out)
    print(out)


def main(argv):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if argv == ["patterns"]:
        render_patterns()
        return
    combos = [tuple(argv)] if argv else VERSIONS
    paths = []
    for theme, bg, fontset in combos:
        img = render(theme, bg, fontset)
        png = OUT_DIR / f"QUC_Workshop_2026_{theme}_{bg}_{fontset}.png"
        img.save(png, dpi=(300, 300))
        img.save(png.with_suffix(".pdf"), resolution=300)
        paths.append(png)
        print(png)
    if len(paths) > 1:
        print(contact_sheet(paths))


if __name__ == "__main__":
    main(sys.argv[1:])
