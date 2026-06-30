"""
템플릿 기반 스펙북 PPTX 생성기.
template.pptx 슬라이드를 복사·수정하여 재현한다.
"""
import io
import requests
from copy import deepcopy
from pathlib import Path
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE

TEMPLATE_PATH = Path(__file__).parent / "template.pptx"

# 템플릿 슬라이드 인덱스 (0-based)
IDX_COVER     = 0   # 표지
IDX_DESIGN    = 1   # Design Direction — 생성 직후 삭제
IDX_COLOR     = 2   # Color Story      (삭제 후 → 1)
IDX_MATERIALS = 3   # Materials        (삭제 후 → 2)
IDX_SPEC      = 4   # Space Spec 템플릿 (삭제 후 → 3)
IDX_MODEL     = 5   # Modeling Image   (삭제 후 → 4)
IDX_FFANDE    = 10  # FF&E Schedule    (삭제 후 → 8)
IDX_THANKS    = 11  # Thank You
N_EXAMPLE_ROOM_SLIDES = 6

ROW_TOPS_IN = [1.505, 2.325, 3.145, 3.965, 4.785]
IMG_BOX_L   = 0.50
IMG_BOX_W   = 0.70
IMG_BOX_H   = 0.70

# ── 카테고리 매핑 (한국어 → 슬롯 코드) ───────────────────────────────────────
_CAT_TO_SLOT = {
    "바닥": "FLOOR", "floor": "FLOOR",
    "벽":   "WALL",  "wall":  "WALL",
    "타일": "TILE",  "tile":  "TILE",
    "천장": "PANEL", "도장":  "PANEL",
    "조명": "METAL", "설비":  "METAL", "전기": "METAL",
    "필름": "TEXTILE", "몰딩/걸레받이": "TEXTILE",
    "가구/목공": "TEXTILE", "문/도어": "TEXTILE", "창호": "TEXTILE",
    # 영문 item_code 하위 호환
    "FLOOR": "FLOOR", "WALL": "WALL", "TILE": "TILE",
    "CEIL": "PANEL",  "PAINT": "PANEL",
    "LIGHT": "METAL", "BATH": "METAL", "ELEC": "METAL",
    "FILM": "TEXTILE", "MOLD": "TEXTILE", "FURN": "TEXTILE",
}

_SLIDE4_SLOTS = [
    {"code": "FLOOR",   "img_l": 0.50, "txt_l": 1.55, "t": 1.32},
    {"code": "WALL",    "img_l": 5.10, "txt_l": 6.15, "t": 1.32},
    {"code": "PANEL",   "img_l": 0.50, "txt_l": 1.55, "t": 2.62},
    {"code": "TILE",    "img_l": 5.10, "txt_l": 6.15, "t": 2.62},
    {"code": "METAL",   "img_l": 0.50, "txt_l": 1.55, "t": 3.92},
    {"code": "TEXTILE", "img_l": 5.10, "txt_l": 6.15, "t": 3.92},
]

_SWATCH_X_ORIG = [0.50, 2.05, 3.60, 5.15, 6.70, 8.25]
_SWATCH_X_NEW  = [1.52, 4.34, 7.16]   # 3개 중앙 정렬

# 모델링 슬라이드 뷰 위치 (l, t, w, h) in inches
_VIEW_QUADS = [
    (0.06, 0.52,  4.94, 2.522),  # VIEW 01
    (5.06, 0.52,  4.94, 2.522),  # VIEW 02
    (0.06, 3.103, 4.94, 2.522),  # VIEW 03
    (5.06, 3.103, 4.94, 2.522),  # VIEW 04
]


def _emu(inches: float) -> int:
    return int(inches * 914400)


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 200, 168, 124


def _fetch_image(url: str) -> io.BytesIO | None:
    if not url:
        return None
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return io.BytesIO(r.content)
    except Exception:
        return None


def _hide_shape(shape):
    try:
        sp  = shape._element
        ns  = "http://schemas.openxmlformats.org/drawingml/2006/main"
        spPr = sp.find(f"{{{ns}}}spPr")
        if spPr is None:
            spPr = etree.SubElement(sp, f"{{{ns}}}spPr")
        for tag in ["solidFill", "gradFill", "pattFill", "blipFill", "noFill"]:
            el = spPr.find(f"{{{ns}}}{tag}")
            if el is not None:
                spPr.remove(el)
        etree.SubElement(spPr, f"{{{ns}}}noFill")
        ln = spPr.find(f"{{{ns}}}ln")
        if ln is None:
            ln = etree.SubElement(spPr, f"{{{ns}}}ln")
        for tag in ["solidFill", "gradFill", "pattFill", "noFill"]:
            el = ln.find(f"{{{ns}}}{tag}")
            if el is not None:
                ln.remove(el)
        etree.SubElement(ln, f"{{{ns}}}noFill")
    except Exception:
        pass
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                run.text = ""


def _near(a: int, b: float, tol_in: float = 0.14) -> bool:
    return abs(a - _emu(b)) <= _emu(tol_in)


def _add_colored_rect(slide, l_in, t_in, w_in, h_in, r, g, b):
    """색상으로 채워진 사각형을 슬라이드에 추가한다."""
    shape = slide.shapes.add_shape(1, _emu(l_in), _emu(t_in), _emu(w_in), _emu(h_in))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(r, g, b)
    shape.line.fill.background()
    return shape


def _add_label(slide, text, l_in, t_in, w_in, h_in,
               font_size=7, bold=False, color=(0x4A, 0x45, 0x40)):
    """텍스트 박스를 슬라이드에 추가한다."""
    tb = slide.shapes.add_textbox(_emu(l_in), _emu(t_in), _emu(w_in), _emu(h_in))
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = str(text)
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(*color)
    return tb


# ── 슬라이드 조작 ─────────────────────────────────────────────────────────────
def _copy_slide(prs, src_idx):
    src    = prs.slides[src_idx]
    layout = src.slide_layout
    new    = prs.slides.add_slide(layout)
    sp_tree = new.shapes._spTree
    for sp in list(sp_tree):
        sp_tree.remove(sp)
    for sp in src.shapes._spTree:
        sp_tree.append(deepcopy(sp))
    return new


def _delete_slide(prs, idx):
    xml_slides = prs.slides._sldIdLst
    slides     = list(xml_slides)
    elem       = slides[idx]
    rid        = elem.get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    prs.part.drop_rel(rid)
    xml_slides.remove(elem)


def _move_slide(prs, old_idx, new_idx):
    xml_slides = prs.slides._sldIdLst
    slides     = list(xml_slides)
    elem       = slides[old_idx]
    xml_slides.remove(elem)
    xml_slides.insert(new_idx, elem)


# ── 텍스트 교체 ───────────────────────────────────────────────────────────────
def _set_text(shape, text, font_size_pt=None, word_wrap=False):
    if not shape or not shape.has_text_frame:
        return
    tf = shape.text_frame
    tf.word_wrap  = word_wrap
    tf.auto_size  = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    for para in tf.paragraphs:
        for run in para.runs:
            run.text = ""
    if tf.paragraphs:
        p   = tf.paragraphs[0]
        run = p.runs[0] if p.runs else p.add_run()
        run.text = str(text)
        if font_size_pt is not None:
            run.font.size = Pt(font_size_pt)


# ══════════════════════════════════════════════════════════════════════════════
# 슬라이드 2: 표지
# ══════════════════════════════════════════════════════════════════════════════
def _update_cover(slide, project):
    company  = project.get("company", "")
    name     = project.get("name", "")
    start    = project.get("start_date", "")
    end      = project.get("end_date", "")
    period   = f"{start} ~ {end}" if (start or end) else ""
    address  = project.get("address", "")
    subtitle = f"{name}  ·  {period}"

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text_flat = shape.text_frame.text.strip().upper().replace("\n", " ")
        if "TAILORED" in text_flat and "CLASSIC" in text_flat:
            _set_text(shape, company or shape.text_frame.text)
        elif any(kw in shape.text_frame.text for kw in ["위치:", "면적:", "공사기간:"]):
            _set_text(shape, f"위치: {address}")
        elif ("DESICODE" in text_flat or
              ("·" in shape.text_frame.text and len(shape.text_frame.text) < 100
               and "INTERIOR" not in text_flat and "SPEC BOOK" not in text_flat)):
            _set_text(shape, subtitle)


# ══════════════════════════════════════════════════════════════════════════════
# 슬라이드 2 (C_COLOR): Color Story
# 주조/보조/강조 3색 스와치 + RGB 코드
# ══════════════════════════════════════════════════════════════════════════════
def _update_color_story(slide, project: dict):
    # 1. "COLOR PALETTE 2026" → "전체 분위기 색상"
    for shape in slide.shapes:
        if shape.has_text_frame:
            txt = shape.text_frame.text.upper()
            if "COLOR PALETTE" in txt or "2026" in txt:
                _set_text(shape, "전체 분위기 색상")
                break

    # 2. 원본 6개 스와치 전체 숨기기
    SWATCH_Y_TOP = _emu(1.15)
    SWATCH_Y_BOT = _emu(4.70)
    swatch_ranges = [(_emu(cx - 0.05), _emu(cx + 1.45)) for cx in _SWATCH_X_ORIG]
    for shape in slide.shapes:
        l, t = shape.left, shape.top
        if not (SWATCH_Y_TOP <= t <= SWATCH_Y_BOT):
            continue
        for sx_min, sx_max in swatch_ranges:
            if sx_min <= l <= sx_max:
                _hide_shape(shape)
                break

    # 3. 주조/보조/강조 3개 색상 정의
    palette = [
        (project.get("primary_color",   "#C9A87C"), "주조색"),
        (project.get("secondary_color", "#1C1C1E"), "보조색"),
        (project.get("accent_color",    "#E8C97A"), "강조색"),
    ]

    # 4. 각 색상 사각형 + 레이블 + RGB + HEX 추가
    for cx, (hex_color, label) in zip(_SWATCH_X_NEW, palette):
        r, g, b = _hex_to_rgb(hex_color)

        # 색상 사각형 (W=1.32", H=2.10")
        _add_colored_rect(slide, cx, 1.42, 1.32, 2.10, r, g, b)

        # 색상 역할 레이블 (주조색 / 보조색 / 강조색)
        _add_label(slide, label,       cx, 3.65, 1.32, 0.20,
                   font_size=7, bold=True, color=(0x2C, 0x2C, 0x2E))

        # RGB 코드
        _add_label(slide, f"RGB  {r}, {g}, {b}",
                   cx, 3.88, 1.32, 0.20,
                   font_size=6.5, color=(0x6B, 0x70, 0x80))

        # HEX 코드
        _add_label(slide, hex_color.upper(),
                   cx, 4.10, 1.32, 0.20,
                   font_size=6.5, color=(0x6B, 0x70, 0x80))


# ══════════════════════════════════════════════════════════════════════════════
# 슬라이드 3 (C_MATERIALS): Materials & Finishes
# 각 슬롯: 방에 2종 이상이면 이미지 겹치기, 1종이면 단독
# ══════════════════════════════════════════════════════════════════════════════
def _collect_slot_items(rooms: list[dict]) -> dict[str, list[dict]]:
    """슬롯별 자재 목록 수집 (중복 허용). 반환: {slot_code: [item, ...]}"""
    from collections import defaultdict
    result = defaultdict(list)
    seen: dict[str, set] = defaultdict(set)

    for room in rooms:
        for mat in room.get("materials", []):
            cat  = mat.get("category", "").strip()
            code = mat.get("item_code", "").upper()
            slot = _CAT_TO_SLOT.get(cat) or _CAT_TO_SLOT.get(code)
            if not slot:
                continue
            key = mat.get("product_id") or mat.get("name","")
            if key in seen[slot]:
                continue
            seen[slot].add(key)
            result[slot].append(mat)

    return dict(result)


def _update_materials(slide, rooms: list[dict]):
    """
    Materials 슬라이드: 슬롯별 이미지(최대 2개 겹치기) + 텍스트 업데이트.
    """
    slot_lists = _collect_slot_items(rooms)
    if not slot_lists:
        return

    for slot in _SLIDE4_SLOTS:
        code  = slot["code"]
        items = slot_lists.get(code, [])
        if not items:
            continue

        il    = slot["img_l"]
        tl    = slot["txt_l"]
        row_t = slot["t"]
        item  = items[0]  # 대표 자재 (텍스트용)

        # 이미지 최대 2개 겹치기
        imgs = []
        for it in items[:2]:
            url = it.get("image", "") or it.get("image_url", "")
            img = _fetch_image(url)
            if img:
                imgs.append(img)

        OFFSET = 0.06  # 겹치기 오프셋 (인치)

        for shape in slide.shapes:
            l, t, w, h = shape.left, shape.top, shape.width, shape.height
            # 이미지 박스 (W≈0.9, H≈0.9)
            if _near(l, il, 0.15) and _near(t, row_t, 0.15) and \
               _near(w, 0.9, 0.15) and _near(h, 0.9, 0.15):
                _hide_shape(shape)
                if len(imgs) == 1:
                    imgs[0].seek(0)
                    slide.shapes.add_picture(io.BytesIO(imgs[0].read()), l, t, w, h)
                elif len(imgs) >= 2:
                    # 이미지 1 (뒤, 약간 오프셋)
                    off = _emu(OFFSET)
                    imgs[1].seek(0)
                    slide.shapes.add_picture(io.BytesIO(imgs[1].read()),
                                             l + off, t + off, w, h)
                    # 이미지 2 (앞)
                    imgs[0].seek(0)
                    slide.shapes.add_picture(io.BytesIO(imgs[0].read()), l, t, w, h)
                break

        # 텍스트 업데이트
        brand   = item.get("brand", "")
        name    = item.get("name",  "") or item.get("product", "")
        spec    = item.get("spec",  "") or item.get("size", "")
        finish  = item.get("finish","") or item.get("material","")
        n_items = len(items)
        qty_txt = f"{n_items}종 적용" if n_items > 1 else ""

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            l, t = shape.left, shape.top
            if _near(l, tl, 0.15) and _near(t, row_t + 0.28, 0.15):
                label = f"{brand} {name}".strip() if brand else name
                if n_items > 1:
                    label += f"  외 {n_items-1}종"
                _set_text(shape, label, font_size_pt=7.5)
            elif _near(l, tl, 0.15) and _near(t, row_t + 0.55, 0.15):
                detail = " / ".join(filter(None, [spec, finish]))
                _set_text(shape, detail, font_size_pt=6.5)
            elif _near(l, tl, 0.15) and _near(t, row_t + 0.74, 0.15):
                _set_text(shape, qty_txt, font_size_pt=6.5)


# ══════════════════════════════════════════════════════════════════════════════
# 슬라이드 5 (C_MODEL): Modeling Image
# VIEW 01~04 텍스트 유지 + 이미지/품목/재질마감 연동
# ══════════════════════════════════════════════════════════════════════════════
def _update_model_slide(slide, room_name: str, modeling_views: list | None = None):
    """
    modeling_views: [
        {"image": bytes_or_none, "품목": str, "재질마감": str},
        ... (최대 4)
    ]
    VIEW 라벨은 "VIEW 01" ~ "VIEW 04"만 표시.
    """
    modeling_views = (modeling_views or []) + [{}] * 4
    modeling_views = modeling_views[:4]

    from collections import defaultdict
    quadrant_shapes: dict = defaultdict(list)
    for shape in slide.shapes:
        if shape.width < _emu(3) or shape.height < _emu(2):
            continue
        text = shape.text_frame.text.strip() if shape.has_text_frame else ""
        if text in ("", "+"):
            t_key = round(shape.top  / 914400)
            l_key = round(shape.left / 914400)
            quadrant_shapes[(t_key, l_key)].append(shape)

    sorted_keys = sorted(quadrant_shapes.keys())

    for i, key in enumerate(sorted_keys[:4]):
        shapes     = quadrant_shapes[key]
        view_data  = modeling_views[i]
        img_bytes  = view_data.get("image")
        품목        = view_data.get("품목", "")
        재질마감     = view_data.get("재질마감", "")

        ref = shapes[0]
        # 뷰 영역 위치/크기
        vl = ref.left
        vt = ref.top
        vw = ref.width
        vh = ref.height

        for s in shapes:
            _hide_shape(s)

        if img_bytes:
            slide.shapes.add_picture(io.BytesIO(img_bytes), vl, vt, vw, vh)

        # VIEW 번호 라벨 (좌하단 다크 바)
        bar_h = _emu(0.22)
        bar_t = vt + vh - bar_h
        bar   = slide.shapes.add_shape(1, vl, bar_t, vw, bar_h)
        bar.fill.solid()
        bar.fill.fore_color.rgb = RGBColor(0x1A, 0x18, 0x16)
        bar.line.fill.background()

        view_num = f"VIEW 0{i+1}"
        tb_view  = slide.shapes.add_textbox(vl + _emu(0.08), bar_t, _emu(0.8), bar_h)
        tf       = tb_view.text_frame
        tf.word_wrap = False
        run      = tf.paragraphs[0].add_run()
        run.text = view_num
        run.font.size  = Pt(6.5)
        run.font.bold  = True
        run.font.color.rgb = RGBColor(0xF0, 0xED, 0xE8)

        # 품목 / 재질마감 (오른쪽 정렬)
        if 품목 or 재질마감:
            info_text = f"{품목}  ·  {재질마감}" if (품목 and 재질마감) else (품목 or 재질마감)
            tb_info   = slide.shapes.add_textbox(
                vl + _emu(0.85), bar_t, vw - _emu(0.95), bar_h)
            tf2 = tb_info.text_frame
            tf2.word_wrap = False
            from pptx.enum.text import PP_ALIGN
            p2  = tf2.paragraphs[0]
            p2.alignment = PP_ALIGN.RIGHT
            run2 = p2.add_run()
            run2.text = info_text
            run2.font.size  = Pt(6)
            run2.font.color.rgb = RGBColor(0xC8, 0xC0, 0xB4)

    # VIEW 텍스트 라벨 정리 (원본 텍스트 제거)
    for shape in slide.shapes:
        if shape.has_text_frame:
            txt = shape.text_frame.text.strip()
            if txt.startswith("VIEW") and "|" in txt:
                _set_text(shape, "")


# ══════════════════════════════════════════════════════════════════════════════
# 슬라이드 4 (C_SPEC): Space Specification
# ══════════════════════════════════════════════════════════════════════════════
def _update_spec_slide(slide, room_name: str, room_en: str, items: list[dict]):
    """공간 스펙 슬라이드: 방 이름 + 5행 데이터."""
    img_placeholders: dict[int, list] = {ri: [] for ri in range(len(ROW_TOPS_IN))}
    for shape in slide.shapes:
        l, t = shape.left, shape.top
        if not _near(l, IMG_BOX_L, 0.12):
            continue
        for ri, rt in enumerate(ROW_TOPS_IN):
            if _near(t, rt, 0.12):
                img_placeholders[ri].append(shape)
                break

    for ri, rt in enumerate(ROW_TOPS_IN):
        item    = items[ri] if ri < len(items) else {}
        img_url = item.get("image", "") or item.get("image_url", "")
        ph_shapes = img_placeholders[ri]

        img_data = _fetch_image(img_url) if img_url else None
        if img_data:
            for s in ph_shapes:
                _hide_shape(s)
            slide.shapes.add_picture(img_data,
                _emu(IMG_BOX_L), _emu(rt), _emu(IMG_BOX_W), _emu(IMG_BOX_H))
        else:
            for s in ph_shapes:
                _hide_shape(s)

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        l, t  = shape.left, shape.top
        text  = shape.text_frame.text.strip()

        if "공간 스펙" in text:
            _set_text(shape, f"{room_name} 공간 스펙  ·  {room_en}")
            continue
        if shape.width > _emu(2.5) and not text:
            continue

        for ri, rt in enumerate(ROW_TOPS_IN):
            item = items[ri] if ri < len(items) else {}

            if _near(l, 1.38) and _near(t, rt + 0.05, 0.12):
                cat = item.get("category","") or item.get("item_code","")
                _set_text(shape, cat, font_size_pt=7)
                break
            if _near(l, 1.38) and _near(t, rt + 0.24, 0.14):
                brand_v = item.get("brand","")
                prod_v  = item.get("name","") or item.get("product","")
                shape.width = _emu(3.00)
                _set_text(shape, f"{brand_v} {prod_v}".strip() if brand_v else prod_v,
                          font_size_pt=7, word_wrap=True)
                break
            if _near(l, 1.38) and _near(t, rt + 0.50, 0.14):
                shape.width = _emu(3.00)
                _set_text(shape, item.get("spec",""), font_size_pt=6.5, word_wrap=True)
                break
            if _near(l, 4.45, 0.18) and _near(t, rt, 0.15):
                _set_text(shape, item.get("finish",""), font_size_pt=6.5)
                break
            if _near(l, 8.80, 0.18) and _near(t, rt, 0.15):
                _set_text(shape, item.get("brand",""), font_size_pt=6.5)
                break


# ══════════════════════════════════════════════════════════════════════════════
# FF&E
# ══════════════════════════════════════════════════════════════════════════════
def _update_ffande(slide, items: list[dict]):
    ROW_Y  = [1.75, 2.22, 2.69, 3.16, 3.63, 4.10, 4.57, 5.04]
    ORIG_X = [0.50, 2.15, 3.05, 3.58, 5.98, 7.63, 8.60]
    ORIG_W = [1.55, 0.85, 0.45, 2.35, 1.60, 0.90, 0.90]
    NEW_X  = [0.50, 3.65, 4.50, 4.98, 6.10, 7.25, 8.20]
    NEW_W  = [3.10, 0.80, 0.45, 1.08, 1.10, 0.90, 0.90]
    COL_KEY = ["product", "room", "qty", "spec", "finish", "vendor", "note"]
    COL_PT  = {k: 6.0 for k in COL_KEY}
    HEADER_Y_MAX = _emu(1.60)

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        l, t, w = shape.left, shape.top, shape.width
        if w > _emu(2.5) and not shape.text_frame.text.strip():
            continue
        for i, (ox, ow, nw_f, nx_f, ckey) in enumerate(
                zip(ORIG_X, ORIG_W, NEW_W, NEW_X, COL_KEY)):
            if not (_near(l, ox, 0.12) and _near(w, ow, 0.25)):
                continue
            if t < HEADER_Y_MAX:
                shape.left  = _emu(nx_f)
                shape.width = _emu(nw_f)
                break
            for ri, ry in enumerate(ROW_Y):
                if not _near(t, ry, 0.20):
                    continue
                item = items[ri] if ri < len(items) else None
                shape.left  = _emu(nx_f)
                shape.width = _emu(nw_f)
                if item is None:
                    _set_text(shape, "", font_size_pt=COL_PT[ckey])
                elif ckey == "product":
                    brand_v = item.get("brand","")
                    prod_v  = item.get("name","") or item.get("product","")
                    val = f"{brand_v} {prod_v}".strip() if brand_v else prod_v
                    _set_text(shape, val, font_size_pt=COL_PT[ckey], word_wrap=True)
                else:
                    val = item.get(ckey,"")
                    val = str(val) if val else ("1" if ckey == "qty" else "")
                    wrap = ckey in ("spec","finish","note")
                    _set_text(shape, val, font_size_pt=COL_PT[ckey], word_wrap=wrap)
                break


# ══════════════════════════════════════════════════════════════════════════════
# 공개 API
# ══════════════════════════════════════════════════════════════════════════════
def generate_pptx(
    project: dict,
    rooms: list[dict],
    common_materials: list[dict] | None = None,
    logo_bytes: bytes | None = None,
) -> bytes:
    """
    project: {company, name, address, start_date, end_date,
              primary_color, secondary_color, accent_color}
    rooms:   [{name, materials:[{category, name, brand, spec, finish,
                                  image(url), qty, ...}],
               modeling_views:[{image(bytes), 품목, 재질마감}]}]
    """
    prs = Presentation(TEMPLATE_PATH)

    # 0. Design Direction 슬라이드 삭제
    _delete_slide(prs, IDX_DESIGN)
    C_COLOR     = IDX_COLOR     - 1   # 1
    C_MATERIALS = IDX_MATERIALS - 1   # 2
    C_SPEC      = IDX_SPEC      - 1   # 3
    C_MODEL     = IDX_MODEL     - 1   # 4
    C_FFANDE    = IDX_FFANDE    - 1   # 9

    # 1. 표지
    _update_cover(prs.slides[IDX_COVER], project)
    if logo_bytes:
        try:
            prs.slides[IDX_COVER].shapes.add_picture(
                io.BytesIO(logo_bytes),
                _emu(0.25), _emu(0.15), _emu(1.6), _emu(0.55))
        except Exception:
            pass

    # 2. Color Story — 프로젝트 색상 3개
    _update_color_story(prs.slides[C_COLOR], project)

    # 3. Materials — 방별 자재, 슬롯별 이미지 겹치기
    _update_materials(prs.slides[C_MATERIALS], rooms)

    # 4. 각 방: Modeling(5p) → Spec(6p) 순서로 복사
    room_slide_counts = []
    for room in rooms:
        materials = room.get("materials", [])
        n_chunks  = max(1, -(-len(materials) // 5))

        # 5p: 모델링 이미지 슬라이드
        m = _copy_slide(prs, C_MODEL)
        _update_model_slide(m, room["name"], room.get("modeling_views"))

        # 6p~: 공간 스펙 슬라이드 (자재 5개씩)
        for chunk_i in range(n_chunks):
            chunk = materials[chunk_i * 5: chunk_i * 5 + 5]
            s = _copy_slide(prs, C_SPEC)
            _update_spec_slide(s, room["name"], room.get("name_en",""), chunk)

        room_slide_counts.append(1 + n_chunks)

    total_room_slides = sum(room_slide_counts)

    # 5. FF&E 업데이트
    all_ff = []
    for room in rooms:
        for it in room.get("materials", []):
            all_ff.append({**it, "room": it.get("room") or room["name"]})

    _update_ffande(prs.slides[C_FFANDE], all_ff[:8])
    for extra_start in range(8, len(all_ff), 8):
        extra = _copy_slide(prs, C_FFANDE)
        _update_ffande(extra, all_ff[extra_start: extra_start + 8])

    # 6. 예제 방 슬라이드 삭제 (N_EXAMPLE_ROOM_SLIDES = 6)
    for _ in range(N_EXAMPLE_ROOM_SLIDES):
        _delete_slide(prs, C_SPEC)

    # 7. 방 슬라이드를 인덱스 3 위치로 이동
    for i in range(total_room_slides):
        _move_slide(prs, 5 + i, 3 + i)

    # 8. Thank You 항상 마지막
    total = len(prs.slides)
    for idx in range(total - 1, -1, -1):
        for shape in prs.slides[idx].shapes:
            if shape.has_text_frame and "THANK" in shape.text_frame.text.upper():
                if idx != total - 1:
                    _move_slide(prs, idx, total - 1)
                break

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
