"""
템플릿 PPTX 기반 스펙북 생성기.
template.pptx의 슬라이드 마스터/테마를 그대로 상속하고
기존 슬라이드를 삭제한 뒤 새 슬라이드를 추가한다.
"""
import io
import copy
import requests
from pathlib import Path
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

TEMPLATE_PATH = Path(__file__).parent / "template.pptx"

# ── 템플릿과 동일한 색상 팔레트 ───────────────────────────────────────────────
C_BG     = RGBColor(0xF7, 0xF5, 0xF2)
C_DARK   = RGBColor(0x2C, 0x2C, 0x2C)
C_ACCENT = RGBColor(0xC8, 0xA9, 0x7E)
C_MID    = RGBColor(0x8C, 0x7B, 0x6B)
C_LIGHT  = RGBColor(0xE8, 0xE0, 0xD8)
C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)

TIER_COLORS = {
    "최저가": RGBColor(0x6A, 0xA8, 0x4F),
    "보통":   RGBColor(0xC8, 0xA9, 0x7E),
    "최고가": RGBColor(0x8E, 0x44, 0xAD),
}

SLIDE_W = Inches(10)
SLIDE_H = Inches(5.63)


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _remove_all_slides(prs: Presentation):
    """기존 슬라이드를 모두 삭제하고 슬라이드 마스터/테마만 유지한다."""
    slide_ids = list(prs.slides._sldIdLst)
    for slide_id in slide_ids:
        r_id = slide_id.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        prs.part.drop_rel(r_id)
        prs.slides._sldIdLst.remove(slide_id)


def _blank_slide(prs: Presentation):
    """Blank 레이아웃(index 6)으로 새 슬라이드 생성."""
    layout = prs.slide_layouts[6]
    return prs.slides.add_slide(layout)


def _rect(slide, left, top, width, height, fill: RGBColor = None, line: RGBColor = None, line_pt=0.5):
    shape = slide.shapes.add_shape(1, left, top, width, height)
    f = shape.fill
    if fill:
        f.solid(); f.fore_color.rgb = fill
    else:
        f.background()
    ln = shape.line
    if line:
        ln.color.rgb = line; ln.width = Pt(line_pt)
    else:
        ln.fill.background()
    return shape


def _text(slide, text, left, top, width, height,
          size=10, bold=False, color=C_DARK, align=PP_ALIGN.LEFT, wrap=True):
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text       = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color
    return txb


def _fetch(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
        ct = r.headers.get("Content-Type", "")
        if r.status_code == 200 and "image" in ct:
            return r.content
    except Exception:
        pass
    return None


# ── 슬라이드 빌더 ─────────────────────────────────────────────────────────────

def _cover_slide(prs: Presentation, project: dict):
    """템플릿 슬라이드 1과 동일한 표지 슬라이드."""
    slide = _blank_slide(prs)

    # 배경
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=C_BG)
    # 왼쪽 골드 바
    _rect(slide, 0, 0, Inches(0.15), SLIDE_H, fill=C_ACCENT)
    # 제목
    _text(slide, project.get("name", "인테리어 스펙북"),
          Inches(0.5), Inches(1.2), Inches(7), Inches(1.0),
          size=28, bold=True, color=C_DARK)
    # 구분선
    _rect(slide, Inches(0.5), Inches(2.3), Inches(1.5), Emu(36000), fill=C_ACCENT)
    # 프로젝트 정보
    lines = "\n".join([
        f"위치: {project.get('location','')}",
        f"면적: {project.get('area','')}",
        f"공사기간: {project.get('period','')}",
        f"담당자: {project.get('designer','')}",
        f"작성일: {project.get('date','')}",
    ])
    _text(slide, lines,
          Inches(0.5), Inches(2.6), Inches(5.5), Inches(2.5),
          size=11, color=C_MID)


def _space_slide(prs: Presentation, space_name: str, selections: list[dict]):
    """
    공간 슬라이드 — 카드 최대 3개 (템플릿 슬라이드 2와 동일 레이아웃).
    selections: [{"item", "tier", "product", "brand", "spec",
                  "price", "note", "image_url", "source_url"}, ...]
    """
    slide = _blank_slide(prs)

    # 배경
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=C_BG)
    # 상단 다크 바
    _rect(slide, 0, 0, SLIDE_W, Inches(0.75), fill=C_DARK)
    # 공간명
    _text(slide, space_name,
          Inches(0.3), Inches(0.1), Inches(4), Inches(0.6),
          size=18, bold=True, color=C_WHITE)

    # 카드 레이아웃 (템플릿과 동일 수치)
    CARD_W  = Inches(3.0)
    CARD_H  = Inches(4.2)
    IMG_H   = Inches(1.9)
    GAP     = Inches(0.18)
    START_X = Inches(0.22)
    START_Y = Inches(0.90)

    for i, sel in enumerate(selections[:3]):
        cx = START_X + i * (CARD_W + GAP)
        cy = START_Y

        # 카드 배경 (흰색 + 테두리)
        _rect(slide, cx, cy, CARD_W, CARD_H,
              fill=C_WHITE, line=C_LIGHT, line_pt=0.5)

        # 이미지 영역
        img_bytes = _fetch(sel.get("image_url", "")) if sel.get("image_url") else None
        if img_bytes:
            try:
                slide.shapes.add_picture(
                    io.BytesIO(img_bytes), cx, cy, CARD_W, IMG_H)
            except Exception:
                _rect(slide, cx, cy, CARD_W, IMG_H, fill=C_LIGHT)
        else:
            _rect(slide, cx, cy, CARD_W, IMG_H, fill=C_LIGHT)

        # 등급 뱃지
        tier        = sel.get("tier", "보통")
        badge_color = TIER_COLORS.get(tier, C_ACCENT)
        badge_top   = cy + IMG_H + Inches(0.08)
        _rect(slide, cx + Inches(0.08), badge_top,
              Inches(0.65), Inches(0.22), fill=badge_color)
        _text(slide, tier,
              cx + Inches(0.08), cy + IMG_H + Inches(0.07),
              Inches(0.65), Inches(0.24),
              size=7, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # 품목명 (오른쪽)
        _text(slide, sel.get("item", ""),
              cx + Inches(0.78), cy + IMG_H + Inches(0.08),
              Inches(2.1), Inches(0.24),
              size=8, color=C_MID)

        # 제품명
        _text(slide, sel.get("product", ""),
              cx + Inches(0.08), cy + IMG_H + Inches(0.36),
              CARD_W - Inches(0.16), Inches(0.35),
              size=10, bold=True, color=C_DARK)

        # 브랜드 | 사양
        _text(slide, f"{sel.get('brand','')}  |  {sel.get('spec','')}",
              cx + Inches(0.08), cy + IMG_H + Inches(0.72),
              CARD_W - Inches(0.16), Inches(0.30),
              size=8, color=C_MID)

        # 가격
        _text(slide, sel.get("price", ""),
              cx + Inches(0.08), cy + IMG_H + Inches(1.0),
              CARD_W - Inches(0.16), Inches(0.28),
              size=9, bold=True, color=C_ACCENT)

        # 메모
        _text(slide, sel.get("note", ""),
              cx + Inches(0.08), cy + IMG_H + Inches(1.28),
              CARD_W - Inches(0.16), Inches(0.55),
              size=7, color=C_MID)

        # 출처 URL
        src = sel.get("source_url", "")
        if src:
            _text(slide, f"출처: {src[:60]}",
                  cx + Inches(0.08), cy + IMG_H + Inches(1.85),
                  CARD_W - Inches(0.16), Inches(0.22),
                  size=6, color=RGBColor(0x33, 0x66, 0xCC))


# ── 공개 API ──────────────────────────────────────────────────────────────────

def generate_pptx(project: dict, space_selections: dict) -> bytes:
    """
    project         : {name, location, area, period, designer, date}
    space_selections: {공간명: [{item, tier, product, ...}, ...]}
    반환             : PPTX 파일 bytes
    """
    # 템플릿 로드 → 슬라이드 마스터/테마/폰트 상속
    prs = Presentation(TEMPLATE_PATH)
    # 기존 예시 슬라이드 삭제
    _remove_all_slides(prs)

    _cover_slide(prs, project)

    for space_name, sels in space_selections.items():
        if not sels:
            continue
        # 카드 3개씩 페이지 분할
        for chunk_start in range(0, len(sels), 3):
            _space_slide(prs, space_name, sels[chunk_start:chunk_start + 3])

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
