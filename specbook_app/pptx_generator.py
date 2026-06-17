"""
Generates a spec book PPTX based on the template design.
One slide per space with material cards (tier + product info + image).
"""
import io
import requests
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

TEMPLATE_PATH = Path(__file__).parent / "template.pptx"

# Design constants matching template palette
C_BG = RGBColor(0xF7, 0xF5, 0xF2)       # warm white
C_DARK = RGBColor(0x2C, 0x2C, 0x2C)      # near black
C_ACCENT = RGBColor(0xC8, 0xA9, 0x7E)    # warm gold
C_MID = RGBColor(0x8C, 0x7B, 0x6B)       # mid brown
C_LIGHT = RGBColor(0xE8, 0xE0, 0xD8)     # light beige

TIER_COLORS = {
    "최저가": RGBColor(0x6A, 0xA8, 0x4F),
    "보통":   RGBColor(0xC8, 0xA9, 0x7E),
    "최고가": RGBColor(0x8E, 0x44, 0xAD),
}

SLIDE_W = Inches(10)
SLIDE_H = Inches(5.63)


def _add_rect(slide, left, top, width, height, fill_rgb=None, line_rgb=None, line_width=None):
    shape = slide.shapes.add_shape(1, left, top, width, height)
    fill = shape.fill
    if fill_rgb:
        fill.solid()
        fill.fore_color.rgb = fill_rgb
    else:
        fill.background()
    line = shape.line
    if line_rgb:
        line.color.rgb = line_rgb
        if line_width:
            line.width = line_width
    else:
        line.fill.background()
    return shape


def _add_textbox(slide, text, left, top, width, height, font_size=10,
                 bold=False, color=C_DARK, align=PP_ALIGN.LEFT, wrap=True):
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    return txb


def _fetch_image_bytes(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            return r.content
    except Exception:
        pass
    return None


def _add_cover_slide(prs: Presentation, project: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    # Background
    _add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill_rgb=C_BG)

    # Left accent bar
    _add_rect(slide, 0, 0, Inches(0.15), SLIDE_H, fill_rgb=C_ACCENT)

    # Title
    _add_textbox(slide, project.get("name", "인테리어 스펙북"),
                 Inches(0.5), Inches(1.2), Inches(6), Inches(1),
                 font_size=28, bold=True, color=C_DARK)

    # Subtitle line
    _add_rect(slide, Inches(0.5), Inches(2.3), Inches(1.5), Emu(36000), fill_rgb=C_ACCENT)

    info_lines = [
        f"위치: {project.get('location', '')}",
        f"면적: {project.get('area', '')}",
        f"공사기간: {project.get('period', '')}",
        f"담당자: {project.get('designer', '')}",
        f"작성일: {project.get('date', '')}",
    ]
    _add_textbox(slide, "\n".join(info_lines),
                 Inches(0.5), Inches(2.6), Inches(5), Inches(2.5),
                 font_size=11, color=C_MID)


def _add_space_slide(prs: Presentation, space_name: str, selections: list[dict]):
    """
    selections: list of {item, tier, product, brand, spec, price, note, image_url, source_url}
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Background
    _add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill_rgb=C_BG)

    # Top bar
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.75), fill_rgb=C_DARK)
    _add_textbox(slide, space_name,
                 Inches(0.3), Inches(0.1), Inches(4), Inches(0.6),
                 font_size=18, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))

    # Material cards — up to 3 per row
    card_w = Inches(3.0)
    card_h = Inches(4.2)
    gap = Inches(0.18)
    start_x = Inches(0.22)
    start_y = Inches(0.9)

    for i, sel in enumerate(selections[:3]):
        cx = start_x + i * (card_w + gap)
        cy = start_y

        # Card background
        _add_rect(slide, cx, cy, card_w, card_h,
                  fill_rgb=RGBColor(0xFF, 0xFF, 0xFF),
                  line_rgb=C_LIGHT, line_width=Pt(0.5))

        # Image area
        img_h = Inches(1.9)
        img_bytes = _fetch_image_bytes(sel.get("image_url", "")) if sel.get("image_url") else None
        if img_bytes:
            try:
                slide.shapes.add_picture(
                    io.BytesIO(img_bytes),
                    cx, cy, card_w, img_h
                )
            except Exception:
                _add_rect(slide, cx, cy, card_w, img_h, fill_rgb=C_LIGHT)
        else:
            _add_rect(slide, cx, cy, card_w, img_h, fill_rgb=C_LIGHT)

        # Tier badge
        tier = sel.get("tier", "보통")
        badge_color = TIER_COLORS.get(tier, C_ACCENT)
        _add_rect(slide, cx + Inches(0.08), cy + img_h + Inches(0.08),
                  Inches(0.65), Inches(0.22), fill_rgb=badge_color)
        _add_textbox(slide, tier,
                     cx + Inches(0.08), cy + img_h + Inches(0.07),
                     Inches(0.65), Inches(0.24),
                     font_size=7, bold=True,
                     color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)

        # Item label
        _add_textbox(slide, sel.get("item", ""),
                     cx + Inches(0.78), cy + img_h + Inches(0.08),
                     Inches(2.1), Inches(0.24),
                     font_size=8, color=C_MID)

        # Product name
        _add_textbox(slide, sel.get("product", ""),
                     cx + Inches(0.08), cy + img_h + Inches(0.36),
                     card_w - Inches(0.16), Inches(0.35),
                     font_size=10, bold=True, color=C_DARK)

        # Brand + spec
        brand_spec = f"{sel.get('brand', '')}  |  {sel.get('spec', '')}"
        _add_textbox(slide, brand_spec,
                     cx + Inches(0.08), cy + img_h + Inches(0.72),
                     card_w - Inches(0.16), Inches(0.3),
                     font_size=8, color=C_MID)

        # Price
        _add_textbox(slide, sel.get("price", ""),
                     cx + Inches(0.08), cy + img_h + Inches(1.0),
                     card_w - Inches(0.16), Inches(0.28),
                     font_size=9, bold=True, color=C_ACCENT)

        # Note
        _add_textbox(slide, sel.get("note", ""),
                     cx + Inches(0.08), cy + img_h + Inches(1.28),
                     card_w - Inches(0.16), Inches(0.55),
                     font_size=7, color=C_MID)

        # Source URL
        src = sel.get("source_url", "")
        if src:
            _add_textbox(slide, f"출처: {src[:55]}",
                         cx + Inches(0.08), cy + img_h + Inches(1.85),
                         card_w - Inches(0.16), Inches(0.22),
                         font_size=6, color=RGBColor(0x33, 0x66, 0xCC))


def generate_pptx(project: dict, space_selections: dict) -> bytes:
    """
    project: dict with name/location/area/period/designer/date
    space_selections: {space_name: [selection_dict, ...]}
    Returns bytes of the generated PPTX.
    """
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # Ensure blank layout exists
    while len(prs.slide_layouts) < 7:
        prs.slide_layouts._sldLayoutLst.append(prs.slide_layouts[0]._element)

    _add_cover_slide(prs, project)

    for space_name, selections in space_selections.items():
        if selections:
            _add_space_slide(prs, space_name, selections)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
