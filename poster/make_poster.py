#!/usr/bin/env python3
"""
KIAS Summer School 2026 poster generator.

Edit the CONTENT block below, run the script, and three files get written:
    kias_summer_school_2026.svg   ← editable (Apple SD Gothic Neo first)
    kias_summer_school_2026.png   ← 2040x2880, good for screens / decent for print
    kias_summer_school_2026.pdf   ← vector, scales to any print size

Requirements:
    pip install cairosvg
    macOS: brew install cairo
    Linux: Noto Sans CJK KR installed for Korean rendering in the PNG.
    (On macOS the .svg itself uses Apple SD Gothic Neo for native editing.)
"""
import base64
import mimetypes
import os
import sys
from html import escape as _esc
from pathlib import Path

# On macOS, point cairocffi at the Homebrew cairo before importing cairosvg.
if sys.platform == "darwin":
    _brew_cairo = "/opt/homebrew/opt/cairo/lib"
    if os.path.isdir(_brew_cairo):
        existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            f"{_brew_cairo}:{existing}" if existing else _brew_cairo
        )

from cairosvg import svg2png, svg2pdf  # noqa: E402


def x(s: str) -> str:
    """XML-escape user-provided text before inserting into the SVG."""
    return _esc(str(s), quote=True)


# ============================================================
# CONTENT — edit these to change what appears on the poster
# ============================================================

TITLE_KR = [
    ("고등과학원 천체물리 여름학교 2026", 28),  # (line, font-size)
    ("외부은하와 우주론",        54),
]
SUBTITLE_EN   = [
    "2026 KIAS Summer School on",
    "Extragalactic Astronomy and Cosmology",
]
SECTION_LABEL = "토론 주제 및 발제 강연자"

# Three discussion themes; "lecturers" lists the 발제 강연자 for each.
TOPICS = [
    {
        "num":       "01",
        "title":     "우주거대구조 관측을 통한 새로운 물리 탐색",
        "lecturers": "박현배 (IBS) · 심준섭 (부산대)",
    },
    {
        "num":       "02",
        "title":     "은하 서베이",
        "lecturers": "정동희 (KIAS · PSU) · 황호성 (서울대)",
    },
    {
        "num":       "03",
        "title":     "천문학에서의 인공지능",
        "lecturers": "김지훈 (서울대) · 홍성욱 (천문연)",
    },
]

# Logistics rows. `placeholder=True` italicizes the value.
INFO_FIELDS = [
    {"label": "기간",      "value": "7월 13일(월)–16일(목)"},
    {"label": "등록 마감", "value": "6월 19일(금)"},
    {"label": "장소",      "value": "양평 수향더한옥 펜션"},
    {"label": "참가 대상", "value": "천문학 관련 대학원생 및 연구원"},
]

# Organizing committee and contact, shown above the footer.
COMMITTEE = "박창범, 김정규, 김주한, 정동희, 황호성"
CONTACT   = "고등과학원 위선미 (smwee@kias.re.kr, 02-958-2640)"

FOOTER     = "고등과학원 KIAS · http://events.kias.re.kr/h/astroschool2026"
FOOTER_URL = "http://events.kias.re.kr/h/astroschool2026"

IMAGE_CREDIT = "NASA/JPL-Caltech — SPHEREx all-sky reference map (LinesRB/StarsRGB)"

# Oval all-sky image shown as a banner under the title. Use the transparent
# cutout produced by cut_oval.py (black background removed); a 2:1 ellipse on a
# transparent field sits cleanly on the white poster. Set to None to omit it.
CENTER_IMAGE = "images/SPHEREx_Merged_cut.png"

# Spacecraft over the white layout. BLEND is None (oval banner only) or
# "craft" (cut-out spacecraft placed over the oval banner).
SATELLITE_IMAGE = "images/SPHEREx_March2022-Satellite.png"
BLEND = "craft"

# Placement of the cut-out spacecraft when BLEND == "craft".
#   CRAFT_BOX    — (x, y, width, height) in the 680x960 poster space
#   CRAFT_FLIP   — mirror left-right (True = aperture faces into the oval)
#   CRAFT_ROTATE — extra rotation in degrees, counter-clockwise
CRAFT_BOX = (470, 170, 198, 198)
CRAFT_FLIP = True
CRAFT_ROTATE = 30

# QR code + KIAS logo (bottom-right, like the 2024 poster). QR encodes QR_URL.
SHOW_QR = True
QR_URL = "http://events.kias.re.kr/h/astroschool2026/"
KIAS_LOGO = "images/KIAS-banner.png"

OUTPUT_BASENAME = "kias_summer_school_2026"
OUTPUT_DIR = "drafts"   # rendered posters and generated assets go here


# ============================================================
# SVG TEMPLATE — decorative elements (cosmic web, stars, AI nodes).
# You normally don't need to touch this; edit CONTENT above instead.
# ============================================================

SVG_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="680" height="960" viewBox="0 0 680 960" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img">
<title>2026 KIAS Summer School Poster — 외부은하와 우주론</title>
<desc>KIAS Summer School 2026 poster: SPHEREx all-sky map banner over a white layout.</desc>

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


# ============================================================
# SVG ASSEMBLY
# ============================================================

def build_topics_block(topics):
    """Render the three-lecture-themes section (monochrome, left-aligned)."""
    out = []
    for i, t in enumerate(topics):
        y = 692 + i * 54
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
        y = 546 + i * 26
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


# Banner box for the oval all-sky image (a 2:1 ellipse). x, y, width, height.
BANNER = (40, 204, 600, 300)


def build_qr_asset(url):
    """Build (and cache) a QR-code PNG encoding url. Needs the qrcode package."""
    import qrcode

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "_qr.png")
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


def build_svg():
    """Assemble the full SVG string from the CONTENT variables."""
    topics_svg = build_topics_block(TOPICS)
    info_svg = build_info_block(INFO_FIELDS)

    overlay = ""
    if BLEND == "craft":
        # Cut-out spacecraft over the oval banner: trim the transparent margins
        # of SATELLITE_IMAGE, then apply the optional flip/rotation.
        from PIL import Image
        img = Image.open(SATELLITE_IMAGE).convert("RGBA")
        img = img.crop(img.split()[-1].getbbox())
        if CRAFT_FLIP:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if CRAFT_ROTATE:
            img = img.rotate(CRAFT_ROTATE, expand=True, resample=Image.BICUBIC)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        sat_path = os.path.join(OUTPUT_DIR, "_craft_satellite.png")
        img.save(sat_path)
        cx, cy, cw, ch = CRAFT_BOX
        href = _image_href(sat_path)
        overlay = (f'<image href="{href}" x="{cx}" y="{cy}" width="{cw}" height="{ch}" '
                   f'preserveAspectRatio="xMidYMid meet"/>')
    elif BLEND is not None:
        raise ValueError(f"unknown BLEND mode: {BLEND!r}")

    qr = ""
    if SHOW_QR:
        qr_href = _image_href(build_qr_asset(QR_URL))
        logo_href = _image_href(KIAS_LOGO)
        # QR and logo share the same height, top and bottom so they line up.
        qr = (f'<image href="{qr_href}" x="488" y="856" width="60" height="60"/>'
              f'<image href="{logo_href}" x="562" y="856" width="68" height="60" '
              f'preserveAspectRatio="xMidYMid meet"/>')

    header = SVG_HEADER.replace(
        "__BACKGROUND_IMAGE__", build_background_image(CENTER_IMAGE) + "\n" + overlay)

    text_block = f'''
<text class="kr" x="340" y="74" text-anchor="middle" letter-spacing="2"><tspan x="340" font-size="{TITLE_KR[0][1]}" font-weight="600" fill="#2a3350">{x(TITLE_KR[0][0])}</tspan><tspan x="340" dy="66" font-size="{TITLE_KR[1][1]}" font-weight="700" fill="#15151c">{x(TITLE_KR[1][0])}</tspan></text>

<text class="en" x="340" y="166" text-anchor="middle" fill="#7a86a0" font-size="14" letter-spacing="2"><tspan x="340">{x(SUBTITLE_EN[0])}</tspan><tspan x="340" dy="20">{x(SUBTITLE_EN[1])}</tspan></text>

<text class="en" x="636" y="520" text-anchor="end" fill="#aab2c2" font-size="7">{x(IMAGE_CREDIT)}</text>

{info_svg}

<line x1="50" y1="642" x2="630" y2="642" stroke="#dde1ea" stroke-width="1"/>

<text class="kr" x="50" y="666" fill="#3a4a6a" font-size="14" letter-spacing="3" font-weight="600">{x(SECTION_LABEL)}</text>

{topics_svg}

<line x1="50" y1="838" x2="630" y2="838" stroke="#dde1ea" stroke-width="1"/>

<text class="kr" x="50" y="858" fill="#2a3350" font-size="13" font-weight="700">조직위원</text>
<text class="kr" x="150" y="858" fill="#15151c" font-size="13">{x(COMMITTEE)}</text>
<text class="kr" x="50" y="882" fill="#2a3350" font-size="13" font-weight="700">문의사항</text>
<text class="kr" x="150" y="882" fill="#15151c" font-size="13">{x(CONTACT)}</text>

<a href="{x(FOOTER_URL)}" xlink:href="{x(FOOTER_URL)}" target="_blank"><text class="kr" x="50" y="910" fill="#8893a8" font-size="10" letter-spacing="1">{x(FOOTER)}</text></a>
{qr}
'''

    return header + text_block + "</svg>\n"


# ============================================================
# RENDERING
# ============================================================

def render_outputs(svg_text, basename=OUTPUT_BASENAME, out_dir=OUTPUT_DIR):
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
    _add_pdf_link(pdf_path, FOOTER_URL,
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


def main():
    svg_text = build_svg()
    svg_path, png_path, pdf_path = render_outputs(svg_text)
    print(f"Wrote: {svg_path}")
    print(f"Wrote: {png_path}")
    print(f"Wrote: {pdf_path}")


if __name__ == "__main__":
    main()
