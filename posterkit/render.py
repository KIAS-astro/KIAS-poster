#!/usr/bin/env python3
"""KIAS Summer School poster generator (engine).

The engine is year-agnostic: it reads a year's ``poster.yml`` (content and
render settings) and writes three files into that year's ``drafts/``:

    <basename>.svg   ← editable (Apple SD Gothic Neo first)
    <basename>.png   ← 2040x2880, good for screens / decent for print
    <basename>.pdf   ← vector, scales to any print size

Run from the repository root:

    python -m posterkit --year years/2026

Edit ``years/<year>/poster.yml``, not this file. To make a new year, copy an
existing ``years/<year>/`` directory and edit its ``poster.yml`` and images.

Requirements: cairosvg, qrcode, pillow, pypdf, pyyaml (see pyproject.toml).
    macOS: brew install cairo
    Linux: Noto Sans CJK KR installed for Korean rendering in the PNG.
    (On macOS the .svg itself uses Apple SD Gothic Neo for native editing.)
"""
import argparse
import base64
import mimetypes
import os
import sys
from html import escape as _esc
from pathlib import Path

import yaml

# On macOS, point cairocffi at the Homebrew cairo before importing cairosvg.
if sys.platform == "darwin":
    _brew_cairo = "/opt/homebrew/opt/cairo/lib"
    if os.path.isdir(_brew_cairo):
        existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            f"{_brew_cairo}:{existing}" if existing else _brew_cairo
        )

from cairosvg import svg2png, svg2pdf  # noqa: E402

KIT_DIR = Path(__file__).resolve().parent


def x(s: str) -> str:
    """XML-escape user-provided text before inserting into the SVG."""
    return _esc(str(s), quote=True)


# ============================================================
# SVG TEMPLATE — decorative frame. Content comes from poster.yml.
# ============================================================

SVG_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="680" height="960" viewBox="0 0 680 960" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img">
<title>__DOC_TITLE__</title>
<desc>__DOC_DESC__</desc>

<defs>
<style type="text/css">
.kr { font-family: 'Apple SD Gothic Neo', 'Noto Sans CJK KR', 'Noto Sans KR', sans-serif; }
.en { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.mono { font-family: 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace; }
</style>
</defs>

<rect width="680" height="960" fill="#ffffff"/>
__BACKGROUND_IMAGE__
'''

# Banner box for the oval all-sky image (a 2:1 ellipse). x, y, width, height.
BANNER = (40, 204, 600, 300)


# ============================================================
# SVG ASSEMBLY
# ============================================================

def build_topics_block(topics):
    """Render the three-lecture-themes section (monochrome, left-aligned)."""
    out = []
    for i, t in enumerate(topics):
        y = 706 + i * 54
        out.append(
            f'<text class="mono" x="50" y="{y}" fill="#2a3350" font-size="16" font-weight="600">{x(t["num"])}</text>\n'
            f'<text class="kr" x="86" y="{y}" fill="#15151c" font-size="20" font-weight="600">{x(t["title"])}</text>\n'
            f'<text class="kr" x="86" y="{y + 21}" fill="#66718c" font-size="14">{x(t["lecturers"])}</text>'
        )
    return "\n".join(out)


def build_info_block(fields):
    """Render the logistics rows (bold label, then value on the same line)."""
    out = []
    for i, f in enumerate(fields):
        y = 560 + i * 26
        placeholder = f.get("placeholder", False)
        if placeholder:
            value_attrs = 'fill="#8893a8" font-size="16" font-style="italic"'
        else:
            value_attrs = 'fill="#15151c" font-size="16"'
        out.append(
            f'<text class="kr" x="50" y="{y}" fill="#2a3350" font-size="16" font-weight="700">{x(f["label"])}</text>\n'
            f'<text class="kr" x="150" y="{y}" {value_attrs}>{x(f["value"])}</text>'
        )
    return "\n".join(out)


def _image_href(path):
    """Inline the image as a base64 data URI so the SVG is self-contained."""
    p = Path(path)
    mime, _ = mimetypes.guess_type(p.name)
    if mime is None:
        mime = "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def build_qr_asset(url, out_dir):
    """Build (and cache) a QR-code PNG encoding url. Needs the qrcode package."""
    import qrcode

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "_qr.png")
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=12, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="#15151c", back_color="white").save(out_path)
    return out_path


def build_background_image(path):
    """Place the oval all-sky image as a banner under the title."""
    if not path:
        return ""
    bx, by, bw, bh = BANNER
    href = _image_href(path)
    return (
        f'\n<image href="{href}" x="{bx}" y="{by}" width="{bw}" height="{bh}" '
        f'preserveAspectRatio="xMidYMid meet"/>'
    )


def build_svg(content, cfg, resolve, out_dir):
    """Assemble the full SVG string from the poster.yml content and settings."""
    topics_svg = build_topics_block(content["topics"])
    info_svg = build_info_block(content["info_fields"])
    # SPHEREx note follows the image credit (after a line break), under the banner.
    note_svg = "".join(
        f'<tspan x="636" dy="{14 if i == 0 else 12}" font-size="9" fill="#565f78">{x(line)}</tspan>'
        for i, line in enumerate(content["spherex_note"])
    )

    overlay = ""
    blend = cfg.get("blend")
    if blend == "craft":
        # Cut-out spacecraft over the oval banner: trim the transparent margins
        # of satellite_image, then apply the optional flip/rotation.
        from PIL import Image
        img = Image.open(resolve(cfg["satellite_image"])).convert("RGBA")
        img = img.crop(img.split()[-1].getbbox())
        if cfg.get("craft_flip"):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if cfg.get("craft_rotate"):
            img = img.rotate(cfg["craft_rotate"], expand=True, resample=Image.BICUBIC)
        os.makedirs(out_dir, exist_ok=True)
        sat_path = os.path.join(out_dir, "_craft_satellite.png")
        img.save(sat_path)
        cx, cy, cw, ch = cfg["craft_box"]
        href = _image_href(sat_path)
        overlay = (f'<image href="{href}" x="{cx}" y="{cy}" width="{cw}" height="{ch}" '
                   f'preserveAspectRatio="xMidYMid meet"/>')
    elif blend is not None:
        raise ValueError(f"unknown blend mode: {blend!r}")

    qr = ""
    if cfg.get("show_qr"):
        qr_href = _image_href(build_qr_asset(content["qr_url"], out_dir))
        logo_href = _image_href(resolve(cfg["kias_logo"]))
        # QR and logo share the same height, top and bottom so they line up.
        qr = (f'<image href="{qr_href}" x="488" y="870" width="60" height="60"/>'
              f'<image href="{logo_href}" x="562" y="870" width="68" height="60" '
              f'preserveAspectRatio="xMidYMid meet"/>')

    header = (
        SVG_HEADER
        .replace("__DOC_TITLE__", x(content["doc_title"]))
        .replace("__DOC_DESC__", x(content["doc_desc"]))
        .replace(
            "__BACKGROUND_IMAGE__",
            build_background_image(resolve(cfg.get("center_image"))) + "\n" + overlay,
        )
    )

    title_kr = content["title_kr"]
    subtitle_en = content["subtitle_en"]

    text_block = f'''
<text class="kr" x="340" y="74" text-anchor="middle" letter-spacing="2"><tspan x="340" font-size="{title_kr[0][1]}" font-weight="600" fill="#2a3350">{x(title_kr[0][0])}</tspan><tspan x="340" dy="66" font-size="{title_kr[1][1]}" font-weight="700" fill="#15151c">{x(title_kr[1][0])}</tspan></text>

<text class="en" x="340" y="166" text-anchor="middle" fill="#7a86a0" font-size="14" letter-spacing="2"><tspan x="340">{x(subtitle_en[0])}</tspan><tspan x="340" dy="20">{x(subtitle_en[1])}</tspan></text>

<text class="{content["credit_class"]}" x="636" y="512" text-anchor="end" fill="#9aa3b5" font-size="8"><tspan x="636">{x(content["image_credit"])}</tspan>{note_svg}</text>

{info_svg}

<line x1="50" y1="656" x2="630" y2="656" stroke="#dde1ea" stroke-width="1"/>

<text class="kr" x="50" y="680" fill="#3a4a6a" font-size="14" letter-spacing="3" font-weight="600">{x(content["section_label"])}</text>

{topics_svg}

<line x1="50" y1="852" x2="630" y2="852" stroke="#dde1ea" stroke-width="1"/>

<text class="kr" x="50" y="872" fill="#2a3350" font-size="13" font-weight="700">조직위원</text>
<text class="kr" x="150" y="872" fill="#15151c" font-size="13">{x(content["committee"])}</text>
<text class="kr" x="50" y="896" fill="#2a3350" font-size="13" font-weight="700">문의사항</text>
<text class="kr" x="150" y="896" fill="#15151c" font-size="13">{x(content["contact"])}</text>

<a href="{x(content["footer_url"])}" xlink:href="{x(content["footer_url"])}" target="_blank"><text class="kr" x="50" y="924" fill="#8893a8" font-size="10" letter-spacing="1">{x(content["footer"])}</text></a>
{qr}
'''

    return header + text_block + "</svg>\n"


# ============================================================
# RENDERING
# ============================================================

def render_outputs(svg_text, out_dir, basename, footer_url):
    """Write SVG, PNG, and PDF to out_dir."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    svg_path = out / f"{basename}.svg"
    png_path = out / f"{basename}.png"
    pdf_path = out / f"{basename}.pdf"

    svg_path.write_text(svg_text, encoding="utf-8")

    # cairosvg's font fallback walks the family list left-to-right; if the
    # first one is missing it may not find a CJK glyph in later entries. On
    # macOS Apple SD Gothic Neo is installed; on Linux Noto Sans CJK KR is.
    # We pick a single CJK family per platform so cairo/pango finds it first.
    if sys.platform == "darwin":
        kr_family = "'Apple SD Gothic Neo', sans-serif"
        en_family = "'Helvetica Neue', sans-serif"
        mono_family = "'Menlo', monospace"
    else:
        kr_family = "'Noto Sans CJK KR', 'Noto Sans KR', sans-serif"
        en_family = "'DejaVu Sans', sans-serif"
        mono_family = "'DejaVu Sans Mono', monospace"

    render_svg = (
        svg_text
        .replace(
            "'Apple SD Gothic Neo', 'Noto Sans CJK KR', 'Noto Sans KR', sans-serif",
            kr_family,
        )
        .replace(
            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            en_family,
        )
        .replace(
            "'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace",
            mono_family,
        )
    )
    render_bytes = render_svg.encode("utf-8")

    svg2png(bytestring=render_bytes, write_to=str(png_path),
            output_width=2040, output_height=2880)
    svg2pdf(bytestring=render_bytes, write_to=str(pdf_path))

    # cairosvg ignores <a> tags, so inject a clickable Link annotation over
    # the footer rectangle using pypdf. SVG is 680x960; the PDF cairosvg
    # produces is 510x720 pt (factor 0.75) with origin bottom-left.
    _add_pdf_link(pdf_path, footer_url,
                  svg_rect=(50, 897, 470, 912),
                  svg_size=(680, 960))

    return svg_path, png_path, pdf_path


def _add_pdf_link(pdf_path, url, svg_rect, svg_size):
    """Overlay a clickable URI annotation onto the rendered PDF."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.annotations import Link
    from pypdf.generic import RectangleObject

    svg_w, svg_h = svg_size
    x1, y1_top, x2, y2_top = svg_rect
    reader = PdfReader(str(pdf_path))
    page = reader.pages[0]
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)
    sx, sy = pw / svg_w, ph / svg_h
    rect = RectangleObject([x1 * sx, ph - y2_top * sy, x2 * sx, ph - y1_top * sy])

    writer = PdfWriter(clone_from=reader)
    writer.add_annotation(page_number=0, annotation=Link(rect=rect, url=url))
    with open(pdf_path, "wb") as f:
        writer.write(f)


# ============================================================
# LOADING / CLI
# ============================================================

def make_resolver(year_dir):
    """Resolve an image path from poster.yml to an absolute Path.

    Paths starting with "assets/" resolve under posterkit/assets/ (year-invariant
    assets like the KIAS logo); all other relative paths resolve under year_dir.
    """
    year_dir = Path(year_dir)

    def resolve(path):
        if not path:
            return None
        p = Path(path)
        if p.is_absolute():
            return p
        if p.parts and p.parts[0] == "assets":
            return KIT_DIR / "assets" / Path(*p.parts[1:])
        return year_dir / p

    return resolve


def load_poster(year_dir):
    """Read poster.yml from year_dir; return (content, render_cfg)."""
    with open(Path(year_dir) / "poster.yml", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc["content"], doc["render"]


def build_year(year_dir):
    """Load a year's poster.yml, build the SVG, and render all outputs."""
    year_dir = Path(year_dir)
    content, cfg = load_poster(year_dir)
    resolve = make_resolver(year_dir)
    out_dir = year_dir / "drafts"
    svg_text = build_svg(content, cfg, resolve, out_dir)
    return render_outputs(svg_text, out_dir, cfg["output_basename"],
                          content["footer_url"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render a KIAS Summer School poster.")
    parser.add_argument("--year", required=True,
                        help="year directory holding poster.yml (e.g. years/2026)")
    args = parser.parse_args(argv)

    svg_path, png_path, pdf_path = build_year(args.year)
    print(f"Wrote: {svg_path}")
    print(f"Wrote: {png_path}")
    print(f"Wrote: {pdf_path}")


if __name__ == "__main__":
    main()
