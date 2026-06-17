"""
템플릿 기반 스펙북 PPTX 생성기.
2026_Interior_Spec_Book_White_v7.pptx 의 디자인을 정확히 재현한다.
"""
import io
import requests
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

TEMPLATE_PATH = Path(__file__).parent / "template.pptx"

# ── 템플릿 색상 (실측값) ───────────────────────────────────────────────────────
C_BG       = RGBColor(0xF7, 0xF5, 0xF2)
C_DARK     = RGBColor(0x1A, 0x18, 0x16)
C_SIDEBAR  = RGBColor(0x1A, 0x18, 0x16)
C_LABEL    = RGBColor(0x8C, 0x7F, 0x74)
C_HEAD     = RGBColor(0x9A, 0x8F, 0x86)
C_BODY     = RGBColor(0x4A, 0x45, 0x40)
C_ICON_BG  = RGBColor(0xF0, 0xED, 0xE8)
C_ICON_FG  = RGBColor(0xB8, 0xAF, 0xA8)
C_ACCENT   = RGBColor(0xC8, 0xA9, 0x7E)
C_WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
C_DIVIDER  = RGBColor(0xD8, 0xD2, 0xCC)

TIER_BADGE = {
    "최저가": RGBColor(0x6A, 0xA8, 0x4F),
    "보통":   RGBColor(0xC8, 0xA9, 0x7E),
    "최고가": RGBColor(0x8E, 0x44, 0xAD),
}

SLIDE_W = Inches(10)
SLIDE_H = Inches(5.625)

# 각 행의 Y 위치 (템플릿 실측)
ROW_TOPS = [
    Inches(1.505),
    Inches(2.325),
    Inches(3.145),
    Inches(3.965),
    Inches(4.785),
]
ROW_H = Inches(0.70)


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _remove_all_slides(prs: Presentation):
    slide_ids = list(prs.slides._sldIdLst)
    for sid in slide_ids:
        rid = sid.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        prs.part.drop_rel(rid)
        prs.slides._sldIdLst.remove(sid)


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[0])


def _rect(slide, l, t, w, h, fill=None, line=None, lw=0.5):
    s = slide.shapes.add_shape(1, l, t, w, h)
    f = s.fill
    if fill:
        f.solid(); f.fore_color.rgb = fill
    else:
        f.background()
    ln = s.line
    if line:
        ln.color.rgb = line; ln.width = Pt(lw)
    else:
        ln.fill.background()
    return s


def _text(slide, txt, l, t, w, h,
          size=10, bold=False, color=C_DARK, align=PP_ALIGN.LEFT, wrap=True):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = txt
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return tb


def _fetch(url: str) -> bytes | None:
    if not url:
        return None
    try:
        r = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            return r.content
    except Exception:
        pass
    return None


def _divider(slide, y):
    _rect(slide, Inches(0.5), y, Inches(9.0), Emu(9144), fill=C_DIVIDER)


# ── 슬라이드 빌더 ─────────────────────────────────────────────────────────────

def _cover_slide(prs, project: dict):
    slide = _blank(prs)

    # 왼쪽 다크 사이드바
    _rect(slide, 0, 0, Inches(0.06), SLIDE_H, fill=C_SIDEBAR)

    # 배경
    _rect(slide, Inches(0.06), 0, SLIDE_W - Inches(0.06), SLIDE_H, fill=C_BG)

    # 년도
    _text(slide, "2026",
          Inches(0.5), Inches(0.6), Inches(3), Inches(0.5),
          size=11, bold=True, color=C_LABEL)

    # 메인 타이틀
    _text(slide, "INTERIOR",
          Inches(0.5), Inches(1.1), Inches(7), Inches(0.7),
          size=42, bold=True, color=C_DARK)
    _text(slide, "SPEC BOOK",
          Inches(0.5), Inches(1.75), Inches(7), Inches(0.7),
          size=42, bold=True, color=C_DARK)

    # 서브 라인
    subtitle = f"{project.get('name','')}  ·  {project.get('date','')}  ·  {project.get('designer','')}"
    _text(slide, subtitle,
          Inches(0.5), Inches(2.65), Inches(8), Inches(0.3),
          size=7, bold=False, color=C_LABEL)

    # 구분선
    _rect(slide, Inches(0.5), Inches(3.1), Inches(9.0), Emu(9144), fill=C_DIVIDER)

    # 프로젝트 정보
    info = f"위치: {project.get('location','')}   |   면적: {project.get('area','')}   |   공사기간: {project.get('period','')}"
    _text(slide, info,
          Inches(0.5), Inches(3.25), Inches(9), Inches(0.35),
          size=8, color=C_BODY)

    # 하단 키워드
    _text(slide, "TAILORED CLASSIC",
          Inches(0.5), Inches(4.8), Inches(5), Inches(0.4),
          size=22, bold=True, color=C_DARK)


def _spec_slide(prs, space_name: str, space_en: str, items: list[dict]):
    """
    items: [{"item_label","item_code","tier","product","spec","finish","vendor","note","image_url"}, ...]
    최대 5개 행
    """
    slide = _blank(prs)

    # 사이드바
    _rect(slide, 0, 0, Inches(0.06), SLIDE_H, fill=C_SIDEBAR)
    # 배경
    _rect(slide, Inches(0.06), 0, SLIDE_W - Inches(0.06), SLIDE_H, fill=C_BG)

    # 섹션 라벨
    _text(slide, "SPACE SPECIFICATION",
          Inches(0.5), Inches(0.28), Inches(9), Inches(0.26),
          size=7, bold=True, color=C_LABEL)

    # 구분선
    _rect(slide, Inches(0.5), Inches(0.64), Inches(9.0), Emu(9144), fill=C_DIVIDER)

    # 공간명
    _text(slide, f"{space_name} 공간 스펙  ·  {space_en}",
          Inches(0.5), Inches(0.70), Inches(8.5), Inches(0.52),
          size=22, bold=True, color=C_DARK)

    # 컬럼 헤더
    _text(slide, "품목",   Inches(1.38), Inches(1.26), Inches(2.8), Inches(0.20), size=7, bold=True, color=C_HEAD)
    _text(slide, "재질 / 마감", Inches(4.45), Inches(1.26), Inches(3.5), Inches(0.20), size=7, bold=True, color=C_HEAD)
    _text(slide, "비고",   Inches(8.80), Inches(1.26), Inches(0.70), Inches(0.20), size=7, bold=True, color=C_HEAD)

    _divider(slide, Inches(1.46))

    for i, item in enumerate(items[:5]):
        row_top = ROW_TOPS[i]
        tier = item.get("tier", "보통")
        badge_color = TIER_BADGE.get(tier, C_ACCENT)

        # 아이콘 박스 (이미지 or + 박스)
        img_bytes = _fetch(item.get("image_url", ""))
        if img_bytes:
            try:
                slide.shapes.add_picture(
                    io.BytesIO(img_bytes),
                    Inches(0.5), row_top, Inches(0.70), ROW_H)
            except Exception:
                _rect(slide, Inches(0.5), row_top, Inches(0.70), ROW_H, fill=C_ICON_BG)
                _text(slide, "+", Inches(0.5), row_top, Inches(0.70), ROW_H,
                      size=18, color=C_ICON_FG, align=PP_ALIGN.CENTER)
        else:
            _rect(slide, Inches(0.5), row_top, Inches(0.70), ROW_H, fill=C_ICON_BG)
            _text(slide, "+", Inches(0.5), row_top, Inches(0.70), ROW_H,
                  size=18, color=C_ICON_FG, align=PP_ALIGN.CENTER)

        # 등급 뱃지
        _rect(slide, Inches(1.38), row_top + Inches(0.02),
              Inches(0.55), Inches(0.17), fill=badge_color)
        _text(slide, tier,
              Inches(1.38), row_top + Inches(0.01),
              Inches(0.55), Inches(0.19),
              size=6, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # 품목 코드
        _text(slide, item.get("item_code", "").upper(),
              Inches(1.38), row_top + Inches(0.21),
              Inches(1.5), Inches(0.18),
              size=7, bold=True, color=C_LABEL)

        # 제품명
        _text(slide, item.get("product", ""),
              Inches(1.38), row_top + Inches(0.38),
              Inches(2.9), Inches(0.28),
              size=11, bold=True, color=C_DARK)

        # 규격
        _text(slide, item.get("spec", ""),
              Inches(1.38), row_top + Inches(0.53),
              Inches(2.9), Inches(0.20),
              size=7, color=C_HEAD)

        # 재질 / 마감
        _text(slide, item.get("finish", ""),
              Inches(4.45), row_top + Inches(0.12),
              Inches(3.6), Inches(0.26),
              size=9, color=C_BODY)

        # 비고
        _text(slide, item.get("vendor", ""),
              Inches(8.80), row_top + Inches(0.12),
              Inches(0.70), Inches(0.26),
              size=8, color=C_HEAD)

        # 행 구분선
        if i < len(items) - 1:
            _divider(slide, row_top + ROW_H + Inches(0.015))


# ── 공개 API ──────────────────────────────────────────────────────────────────

def generate_pptx(project: dict, rooms: list[dict]) -> bytes:
    """
    project: {name, location, area, period, designer, date}
    rooms:   [{"name":"거실","name_en":"Living Room","items":[item_dict,...]}, ...]

    item_dict: {item_label, item_code, tier, product, spec, finish, vendor, note, image_url}
    """
    prs = Presentation(TEMPLATE_PATH)
    _remove_all_slides(prs)

    _cover_slide(prs, project)

    for room in rooms:
        items = room.get("items", [])
        if not items:
            continue
        # 5개씩 페이지 분할
        for chunk in range(0, len(items), 5):
            _spec_slide(
                prs,
                room.get("name", ""),
                room.get("name_en", ""),
                items[chunk:chunk + 5],
            )

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
