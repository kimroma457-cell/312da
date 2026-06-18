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

# 템플릿 슬라이드 인덱스 (0-based, 12장 기준)
IDX_COVER     = 0   # 표지
IDX_DESIGN    = 1   # Design Direction — 변경 없음
IDX_COLOR     = 2   # Color Story — 변경 없음
IDX_MATERIALS = 3   # Materials & Finishes — 공통 자재
IDX_SPEC      = 4   # Space Spec 템플릿 (거실)
IDX_MODEL     = 5   # Modeling Image 템플릿 (거실)
# 6,7: 침실 spec+model  8,9: 주방 spec+model  → 모두 삭제
IDX_FFANDE    = 10  # FF&E Schedule
IDX_THANKS    = 11  # Thank You — 변경 없음
N_EXAMPLE_ROOM_SLIDES = 6  # 인덱스 4~9 (거실/침실/주방 spec+model 6장)

ROW_TOPS_IN = [1.505, 2.325, 3.145, 3.965, 4.785]  # Space Spec 행 Y 위치(인치)
IMG_BOX_L   = 0.50   # 이미지 박스 X (인치)
IMG_BOX_W   = 0.70   # 이미지 박스 너비
IMG_BOX_H   = 0.70   # 이미지 박스 높이


def _emu(inches: float) -> int:
    return int(inches * 914400)


def _fetch_image(url: str) -> io.BytesIO | None:
    """URL에서 이미지를 다운로드해 BytesIO로 반환. 실패 시 None."""
    if not url:
        return None
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return io.BytesIO(r.content)
    except Exception:
        return None


def _hide_shape(shape):
    """도형을 투명하게 숨긴다 (fill/line 제거, 텍스트 클리어)."""
    try:
        sp = shape._element
        # spPr 안의 fill → noFill
        ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
        spPr = sp.find(f"{{{ns}}}spPr")
        if spPr is None:
            spPr = etree.SubElement(sp, f"{{{ns}}}spPr")
        # 기존 fill 제거 후 noFill 삽입
        for tag in ["solidFill", "gradFill", "pattFill", "blipFill", "noFill"]:
            el = spPr.find(f"{{{ns}}}{tag}")
            if el is not None:
                spPr.remove(el)
        etree.SubElement(spPr, f"{{{ns}}}noFill")
        # 테두리 제거
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


# ── 자재 자동 선택 ────────────────────────────────────────────────────────────

# item_code → 슬라이드 슬롯 매핑 (우선순위 순서)
_CODE_TO_SLOT = {
    "FLOOR": "FLOOR",
    "WALL":  "WALL",
    "TILE":  "TILE",
    "CEIL":  "PANEL",
    "PAINT": "PANEL",
    "LIGHT": "METAL",
    "BATH":  "METAL",
    "ELEC":  "METAL",
    "FILM":  "TEXTILE",
    "MOLD":  "TEXTILE",
    "FURN":  "TEXTILE",
}
# 슬라이드 4 슬롯 정의: code, 이미지박스X, 텍스트X, 행Y
_SLIDE4_SLOTS = [
    {"code": "FLOOR",   "img_l": 0.50, "txt_l": 1.55, "t": 1.32},
    {"code": "WALL",    "img_l": 5.10, "txt_l": 6.15, "t": 1.32},
    {"code": "PANEL",   "img_l": 0.50, "txt_l": 1.55, "t": 2.62},
    {"code": "TILE",    "img_l": 5.10, "txt_l": 6.15, "t": 2.62},
    {"code": "METAL",   "img_l": 0.50, "txt_l": 1.55, "t": 3.92},
    {"code": "TEXTILE", "img_l": 5.10, "txt_l": 6.15, "t": 3.92},
]
# 슬라이드 3 — 벽/바닥/타일 3개만, 슬라이드 내 기존 6개 X 위치
_SWATCH_X_ORIG = [0.50, 2.05, 3.60, 5.15, 6.70, 8.25]
# 3개 중앙 정렬 X (슬라이드 10", 콘텐츠 0.5~9.5" = 9", 스와치 W=1.32", gap=1.5")
_SWATCH_X_NEW  = [1.52, 4.34, 7.16]
# Color Story 대상: 벽 → 바닥 → 타일 순 고정
_COLOR_CODES   = ["WALL", "FLOOR", "TILE"]


def _auto_select_materials(rooms: list[dict]) -> dict[str, dict]:
    """
    모든 공간의 자재에서 item_code별로 qty 합산 후 슬롯별 최다 자재를 선택한다.
    반환: {"FLOOR": item_dict, "WALL": item_dict, ...}
    """
    from collections import defaultdict

    # code → {product_key: (total_qty, item)}
    tally: dict[str, dict] = defaultdict(dict)
    for room in rooms:
        for it in room.get("items", []):
            code = it.get("item_code", "").upper()
            slot = _CODE_TO_SLOT.get(code)
            if not slot:
                continue
            key = it.get("product", "") or it.get("name", "")
            qty = it.get("qty", 1)
            if key not in tally[slot]:
                tally[slot][key] = [0, it]
            tally[slot][key][0] += qty

    result: dict[str, dict] = {}
    for slot, products in tally.items():
        # qty 합산이 가장 높은 자재 선택
        best_key = max(products, key=lambda k: products[k][0])
        result[slot] = products[best_key][1]
    return result


def _top_items_ordered(rooms: list[dict]) -> list[dict]:
    """Color Story용: 벽→바닥→타일 순서로 최대 3개 반환."""
    from collections import defaultdict

    code_tally: dict[str, dict] = defaultdict(dict)
    for room in rooms:
        for it in room.get("items", []):
            code = it.get("item_code", "").upper()
            if code not in _COLOR_CODES:
                continue
            key = it.get("product", "") or it.get("name", "")
            qty = it.get("qty", 1)
            if key not in code_tally[code]:
                code_tally[code][key] = [0, it]
            code_tally[code][key][0] += qty

    result = []
    for code in _COLOR_CODES:
        if code in code_tally:
            products = code_tally[code]
            best_key = max(products, key=lambda k: products[k][0])
            result.append(products[best_key][1])
    return result  # 최대 3개


def _dominant_hex(img_data: io.BytesIO | None) -> str:
    """이미지에서 지배적인 색상을 추출하여 #RRGGBB 반환. 실패 시 빈 문자열."""
    if not img_data:
        return ""
    try:
        from PIL import Image
        from collections import Counter
        img_data.seek(0)
        img = Image.open(img_data).convert("RGB").resize((80, 80))
        pixels = list(img.getdata())
        # 흰색(>230)·검정(<20) 제외 후 16단계 양자화
        filtered = [
            (r // 16 * 16, g // 16 * 16, b // 16 * 16)
            for r, g, b in pixels
            if not (r > 230 and g > 230 and b > 230)
            and not (r < 20 and g < 20 and b < 20)
        ]
        if not filtered:
            filtered = [(r // 16 * 16, g // 16 * 16, b // 16 * 16) for r, g, b in pixels]
        r, g, b = Counter(filtered).most_common(1)[0][0]
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return ""


# ── 슬라이드 조작 ─────────────────────────────────────────────────────────────

def _copy_slide(prs: Presentation, src_idx: int):
    """src_idx 슬라이드를 복사해 프레젠테이션 끝에 추가한다."""
    src = prs.slides[src_idx]
    layout = src.slide_layout
    new = prs.slides.add_slide(layout)

    sp_tree = new.shapes._spTree
    for sp in list(sp_tree):
        sp_tree.remove(sp)
    for sp in src.shapes._spTree:
        sp_tree.append(deepcopy(sp))

    return new


def _delete_slide(prs: Presentation, idx: int):
    """idx 슬라이드를 삭제한다."""
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    elem = slides[idx]
    rid = elem.get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    )
    prs.part.drop_rel(rid)
    xml_slides.remove(elem)


def _move_slide(prs: Presentation, old_idx: int, new_idx: int):
    """슬라이드 순서를 바꾼다."""
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    elem = slides[old_idx]
    xml_slides.remove(elem)
    xml_slides.insert(new_idx, elem)


# ── 텍스트 교체 ───────────────────────────────────────────────────────────────

def _set_text(shape, text: str, font_size_pt: float | None = None, word_wrap: bool = False):
    """shape 텍스트를 교체한다 (서식은 첫 run 기준 유지)."""
    if not shape or not shape.has_text_frame:
        return
    tf = shape.text_frame
    tf.word_wrap = word_wrap
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE  # 셀 크기에 맞게 자동 축소
    for para in tf.paragraphs:
        for run in para.runs:
            run.text = ""
    if tf.paragraphs:
        p = tf.paragraphs[0]
        if p.runs:
            run = p.runs[0]
        else:
            run = p.add_run()
        run.text = str(text)
        if font_size_pt is not None:
            run.font.size = Pt(font_size_pt)


# ── 슬라이드 업데이트 함수 ────────────────────────────────────────────────────

def _update_cover(slide, project: dict):
    """슬라이드 1: 표지 — 회사명·프로젝트 정보 업데이트."""
    company  = project.get("company", "")
    subtitle = (f"{project.get('name','')}  ·  "
                f"{project.get('date','')}  ·  "
                f"{project.get('designer','')}")
    info     = (f"위치: {project.get('location','')}   |   "
                f"면적: {project.get('area','')}   |   "
                f"공사기간: {project.get('period','')}")

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip()
        text_flat = text.upper().replace('\n', ' ')  # 개행 정규화

        # 회사명 플레이스홀더 (TAILORED CLASSIC — 개행 포함 가능)
        if "TAILORED" in text_flat and "CLASSIC" in text_flat:
            _set_text(shape, company or text)
        # 위치·면적·공사기간 줄 (템플릿에 해당 shape이 있으면)
        elif any(kw in text for kw in ["위치:", "면적:", "공사기간:"]):
            _set_text(shape, info)
        # 서브타이틀: DESICODE 포함이거나 '·' 구분자 있는 텍스트
        elif ("DESICODE" in text or ("·" in text and len(text) < 100
              and "INTERIOR" not in text_flat and "SPEC BOOK" not in text_flat)):
            _set_text(shape, subtitle)


def _update_color_story(slide, top_items: list[dict]):
    """슬라이드 3: Color Story — 벽/바닥/타일 3개 스와치, 중앙 정렬, 지배 색상 자동 추출."""
    # 1단계: 원본 6개 스와치 영역의 모든 shape 숨기기
    # 각 스와치 그룹은 cx_orig ~ cx_orig+1.40" 범위, Y: 1.20~3.60"
    SWATCH_Y_TOP = _emu(1.20)
    SWATCH_Y_BOT = _emu(3.60)
    swatch_ranges = [(_emu(cx - 0.05), _emu(cx + 1.40)) for cx in _SWATCH_X_ORIG]

    for shape in slide.shapes:
        l, t = shape.left, shape.top
        # 스와치 Y 범위 안에 있는지 확인
        if not (SWATCH_Y_TOP <= t <= SWATCH_Y_BOT):
            continue
        # 어떤 스와치 그룹 X 범위에 속하는지 확인
        for sx_min, sx_max in swatch_ranges:
            if sx_min <= l <= sx_max:
                _hide_shape(shape)
                break

    # 텍스트 라벨도 초기화 (T > 3.5")
    for cx_orig in _SWATCH_X_ORIG:
        for shape in slide.shapes:
            if shape.has_text_frame and _near(shape.left, cx_orig, 0.20) and shape.top > _emu(3.5):
                _set_text(shape, "")

    if not top_items:
        return

    # 이미지 다운로드 + 지배 색상 추출
    images = [_fetch_image(it.get("image_url", "")) for it in top_items]
    hex_colors = [_dominant_hex(img) for img in images]

    # 2단계: 3개 스와치를 새 중앙 X 위치에 배치
    for si, (cx_new, cx_orig) in enumerate(zip(_SWATCH_X_NEW, _SWATCH_X_ORIG)):
        if si >= len(top_items):
            break
        item      = top_items[si]
        img_data  = images[si]
        hex_color = hex_colors[si]

        brand   = item.get("brand", "")
        product = item.get("product", "") or item.get("name", "")
        code    = ["WALL", "FLOOR", "TILE"][si]
        usage   = item.get("location", "") or code

        # 스와치 이미지 박스: 원래 첫 번째 스와치(cx_orig=0.50)의 크기 기준으로 새 위치에 삽입
        # 이미지 박스 크기 (W=1.32", H=2.1")
        box_w = _emu(1.32)
        box_t = _emu(1.42)
        box_h = _emu(2.10)
        box_l = _emu(cx_new)

        if img_data:
            img_data.seek(0)
            slide.shapes.add_picture(io.BytesIO(img_data.read()), box_l, box_t, box_w, box_h)
        # 이미지 없으면 빈 박스 → 색상으로 채우기는 skip (투명)

        # 텍스트 박스들 — 원래 해당 cx_orig 위치 shape을 이동 후 내용 업데이트
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            l = shape.left
            t = shape.top
            if not _near(l, cx_orig, 0.20):
                continue
            if t < _emu(3.5):
                continue  # 스와치 박스 영역 건너뜀

            # shape을 새 X 위치로 이동
            shape.left = _emu(cx_new) + (shape.left - _emu(cx_orig))

            cur = shape.text_frame.text.strip()
            # 브랜드명 라벨 (T≈3.62)
            if _near(t, 3.62, 0.12):
                _set_text(shape, (brand or product[:12]).upper(), font_size_pt=7)
            # 제품명 (T≈3.86)
            elif _near(t, 3.86, 0.12):
                _set_text(shape, product[:22], font_size_pt=6.5)
            # 색상 hex 코드 (T≈4.07) — 이미지 지배 색상
            elif _near(t, 4.07, 0.12):
                _set_text(shape, hex_color, font_size_pt=6)
            # 적용 위치 (T≈4.30, 내용 있는 것만)
            elif _near(t, 4.30, 0.12) and cur:
                _set_text(shape, usage[:18], font_size_pt=6)


def _update_materials(slide, slot_items: dict[str, dict]):
    """슬라이드 4: Materials & Finishes — 자동 선택 자재로 이미지+텍스트 업데이트."""
    if not slot_items:
        return

    # 이미지 미리 다운로드
    slot_images = {
        code: _fetch_image(item.get("image_url", ""))
        for code, item in slot_items.items()
    }

    for slot in _SLIDE4_SLOTS:
        code  = slot["code"]
        item  = slot_items.get(code)
        if not item:
            continue
        img_data = slot_images.get(code)

        il  = slot["img_l"]   # 이미지박스 X
        tl  = slot["txt_l"]   # 텍스트 X
        row_t = slot["t"]     # 행 Y

        brand   = item.get("brand", "")
        product = item.get("product", "") or item.get("name", "")
        spec    = item.get("spec", "") or item.get("size", "")
        finish  = item.get("finish", "") or item.get("material", "") or item.get("color", "")
        usage   = item.get("location", "")

        for shape in slide.shapes:
            l, t, w, h = shape.left, shape.top, shape.width, shape.height

            # 이미지 박스 (W≈0.9, H≈0.9, 이미지X, 행Y)
            if _near(l, il, 0.15) and _near(t, row_t, 0.15) and \
               _near(w / 914400, 0.9, 0.15) and _near(h / 914400, 0.9, 0.15):
                if img_data:
                    img_data.seek(0)
                    _hide_shape(shape)
                    slide.shapes.add_picture(io.BytesIO(img_data.read()), l, t, w, h)
                continue

            if not shape.has_text_frame:
                continue

            # 슬롯 코드 라벨 → 그대로 유지
            if _near(l, tl, 0.15) and _near(t, row_t, 0.15):
                pass  # 슬롯 코드(FLOOR 등) 유지
            # 제품명 (T+0.28) — 브랜드 포함
            elif _near(l, tl, 0.15) and _near(t, row_t + 0.28, 0.15):
                label = f"{brand} {product}".strip() if brand else product
                _set_text(shape, label, font_size_pt=7.5)
            # 규격/마감 (T+0.55)
            elif _near(l, tl, 0.15) and _near(t, row_t + 0.55, 0.15):
                detail = " / ".join(filter(None, [spec, finish]))
                _set_text(shape, detail, font_size_pt=6.5)
            # 적용 위치 (T+0.74)
            elif _near(l, tl, 0.15) and _near(t, row_t + 0.74, 0.15):
                _set_text(shape, f"적용  {usage}" if usage else "", font_size_pt=6.5)


def _update_spec_slide(slide, room_name: str, room_en: str, items: list[dict]):
    """공간 스펙 슬라이드: 방 이름 + 5행 데이터 업데이트."""
    # 이미지 박스 플레이스홀더 shapes 수집 (text == "+", L≈0.5)
    img_placeholders: dict[int, list] = {ri: [] for ri in range(len(ROW_TOPS_IN))}
    for shape in slide.shapes:
        l, t = shape.left, shape.top
        if not _near(l, IMG_BOX_L, 0.12):
            continue
        for ri, rt in enumerate(ROW_TOPS_IN):
            if _near(t, rt, 0.12):
                img_placeholders[ri].append(shape)
                break

    # 이미지 삽입 또는 플레이스홀더 숨김
    for ri, rt in enumerate(ROW_TOPS_IN):
        item = items[ri] if ri < len(items) else {}
        img_url = item.get("image_url", "")
        ph_shapes = img_placeholders[ri]

        if img_url:
            img_data = _fetch_image(img_url)
        else:
            img_data = None

        if img_data:
            # 플레이스홀더 숨기고 실제 이미지 삽입
            for s in ph_shapes:
                _hide_shape(s)
            slide.shapes.add_picture(
                img_data,
                _emu(IMG_BOX_L), _emu(rt),
                _emu(IMG_BOX_W), _emu(IMG_BOX_H),
            )
        else:
            # 이미지 없으면 "+" 박스 숨김
            for s in ph_shapes:
                _hide_shape(s)

    # 텍스트 업데이트
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        l, t = shape.left, shape.top
        text = shape.text_frame.text.strip()

        # 타이틀 (공간명)
        if "공간 스펙" in text:
            _set_text(shape, f"{room_name} 공간 스펙  ·  {room_en}")
            continue

        # 배경 구분선 제외 (너비 > 2.5인치인 빈 shape)
        if shape.width > _emu(2.5) and not shape.text_frame.text.strip():
            continue

        # 행별 데이터 — word_wrap=False, 전체 텍스트 표시 (폰트로 수용)
        for ri, rt in enumerate(ROW_TOPS_IN):
            item = items[ri] if ri < len(items) else {}

            if _near(l, 1.38) and _near(t, rt + 0.05, 0.12):
                _set_text(shape, item.get("item_code", "").upper(), font_size_pt=7)
                break
            if _near(l, 1.38) and _near(t, rt + 0.24, 0.14):
                brand_v = item.get("brand", "")
                prod_v  = item.get("product", "")
                _set_text(shape, f"{brand_v} {prod_v}".strip() if brand_v else prod_v, font_size_pt=7)
                break
            if _near(l, 1.38) and _near(t, rt + 0.50, 0.14):
                _set_text(shape, item.get("spec", ""), font_size_pt=6.5)
                break
            if _near(l, 4.45, 0.18) and _near(t, rt, 0.15):
                _set_text(shape, item.get("finish", ""), font_size_pt=6.5)
                break
            if _near(l, 8.80, 0.18) and _near(t, rt, 0.15):
                _set_text(shape, item.get("vendor", ""), font_size_pt=6.5)
                break


def _update_model_slide(slide, room_name: str, model_images: list | None = None):
    """모델링 이미지 슬라이드: VIEW 박스에 이미지 삽입 + 방 이름 업데이트."""
    model_images = model_images or [None, None, None, None]

    # 이미지 플레이스홀더 수집 — 동일 위치의 여러 shape을 (t_key, l_key)로 그룹화
    from collections import defaultdict
    quadrant_shapes: dict = defaultdict(list)
    for shape in slide.shapes:
        if shape.width < _emu(3) or shape.height < _emu(2):
            continue
        text = shape.text_frame.text.strip() if shape.has_text_frame else ""
        if text in ("", "+"):
            t_key = round(shape.top / 914400)   # 인치 반올림
            l_key = round(shape.left / 914400)
            quadrant_shapes[(t_key, l_key)].append(shape)

    # 좌상→우상→좌하→우하 정렬 (t 우선, l 다음)
    sorted_keys = sorted(quadrant_shapes.keys())

    for i, key in enumerate(sorted_keys[:4]):
        shapes = quadrant_shapes[key]
        img_bytes = model_images[i] if i < len(model_images) else None
        ref = shapes[0]  # 위치/크기 기준 shape
        for s in shapes:
            _hide_shape(s)  # 빈 배경 + "+" 모두 숨기기
        if img_bytes:
            slide.shapes.add_picture(
                io.BytesIO(img_bytes),
                ref.left, ref.top, ref.width, ref.height,
            )

    # VIEW 라벨에 방 이름 추가
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip()
        if text.startswith("VIEW"):
            _set_text(shape, f"{text}  |  {room_name}")


def _update_ffande(slide, items: list[dict]):
    """FF&E 슬라이드: 행 데이터 업데이트 (최대 8행).
    ITEM 컬럼을 3.10"으로 확장하고 나머지 컬럼을 우측으로 재배치한다."""
    ROW_Y = [1.75, 2.22, 2.69, 3.16, 3.63, 4.10, 4.57, 5.04]

    # 원본 템플릿 컬럼 위치 (매칭용)
    ORIG_X = [0.50, 2.15, 3.05, 3.58, 5.98, 7.63, 8.60]
    ORIG_W = [1.55, 0.85, 0.45, 2.35, 1.60, 0.90, 0.90]

    # 새 컬럼 위치 — ITEM(3.10") 확장 후 나머지 우측 이동
    NEW_X  = [0.50, 3.65, 4.50, 4.98, 6.10, 7.25, 8.20]
    NEW_W  = [3.10, 0.80, 0.45, 1.08, 1.10, 0.90, 0.90]

    COL_KEY = ["product", "room", "qty", "spec", "finish", "vendor", "note"]
    COL_PT  = {k: 6.0 for k in COL_KEY}

    HEADER_Y_MAX = _emu(1.60)  # 헤더 행 Y 상한

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        l, t = shape.left, shape.top
        w = shape.width

        # 빈 배경 구분선 제외
        if w > _emu(2.5) and not shape.text_frame.text.strip():
            continue

        for i, (ox, ow, nw_f, nx_f, ckey) in enumerate(
                zip(ORIG_X, ORIG_W, NEW_W, NEW_X, COL_KEY)):
            if not (_near(l, ox, 0.12) and _near(w, ow, 0.25)):
                continue

            # 헤더 행 처리
            if t < HEADER_Y_MAX:
                shape.left  = _emu(nx_f)
                shape.width = _emu(nw_f)
                break

            # 데이터 행 처리
            for ri, ry in enumerate(ROW_Y):
                if not _near(t, ry, 0.20):
                    continue
                item = items[ri] if ri < len(items) else None

                shape.left  = _emu(nx_f)
                shape.width = _emu(nw_f)

                if item is None:
                    _set_text(shape, "", font_size_pt=COL_PT[ckey])
                elif ckey == "product":
                    brand_v = item.get("brand", "")
                    prod_v  = item.get("product", "")
                    val = f"{brand_v} {prod_v}".strip() if brand_v else prod_v
                    _set_text(shape, val, font_size_pt=COL_PT[ckey], word_wrap=True)
                else:
                    val = item.get(ckey, "")
                    val = str(val) if val else ("1" if ckey == "qty" else "")
                    _set_text(shape, val, font_size_pt=COL_PT[ckey])
                break


# ── 공개 API ──────────────────────────────────────────────────────────────────

def generate_pptx(
    project: dict,
    rooms: list[dict],
    common_materials: list[dict] | None = None,
    logo_bytes: bytes | None = None,
) -> bytes:
    """
    project: {company, name, location, area, period, designer, date}
    rooms:   [{name, name_en, items:[{item_code, product, brand, spec, finish,
                                      vendor, qty, note, image_url, room}]}]
    """
    prs = Presentation(TEMPLATE_PATH)

    # 1. 표지 수정
    _update_cover(prs.slides[IDX_COVER], project)
    if logo_bytes:
        try:
            prs.slides[IDX_COVER].shapes.add_picture(
                io.BytesIO(logo_bytes),
                _emu(0.25), _emu(0.15), _emu(1.6), _emu(0.55),
            )
        except Exception:
            pass

    # 2. 벽/바닥/타일/천장 자재 자동 선택 → Color Story + Materials & Finishes 업데이트
    slot_items = _auto_select_materials(rooms)
    top_items  = _top_items_ordered(rooms)
    _update_color_story(prs.slides[IDX_COLOR], top_items)
    _update_materials(prs.slides[IDX_MATERIALS], slot_items)

    # 3. 각 방 스펙+모델링 슬라이드 복사 (prs 끝에 추가)
    room_slide_counts = []
    for room in rooms:
        items = room.get("items", [])
        n_chunks = max(1, -(-len(items) // 5))  # ceil(len/5)

        for chunk_i in range(n_chunks):
            chunk = items[chunk_i * 5: chunk_i * 5 + 5]
            s = _copy_slide(prs, IDX_SPEC)
            _update_spec_slide(s, room["name"], room.get("name_en", ""), chunk)

        m = _copy_slide(prs, IDX_MODEL)
        _update_model_slide(m, room["name"], room.get("model_images"))

        room_slide_counts.append(n_chunks + 1)

    total_room_slides = sum(room_slide_counts)

    # 4. FF&E 수정 + 8개 초과 시 슬라이드 복사
    all_ff = []
    for room in rooms:
        for it in room.get("items", []):
            all_ff.append({**it, "room": it.get("room") or room["name"]})

    _update_ffande(prs.slides[IDX_FFANDE], all_ff[:8])
    for extra_start in range(8, len(all_ff), 8):
        extra = _copy_slide(prs, IDX_FFANDE)
        _update_ffande(extra, all_ff[extra_start: extra_start + 8])

    # 5. 예제 방 슬라이드 삭제 (인덱스 4~9: 항상 4번을 반복 삭제)
    for _ in range(N_EXAMPLE_ROOM_SLIDES):
        _delete_slide(prs, IDX_SPEC)

    # 삭제 후 순서: [0:Cover,1:Design,2:Color,3:Materials,4:FF&E,5:TY, 6+:새방슬라이드들]
    # 방 슬라이드를 인덱스 4 위치로 이동
    for i in range(total_room_slides):
        _move_slide(prs, 6 + i, 4 + i)

    # 6. Thank You 슬라이드를 항상 맨 마지막으로
    total = len(prs.slides)
    for idx in range(total - 1, -1, -1):
        s = prs.slides[idx]
        for shape in s.shapes:
            if shape.has_text_frame and "THANK" in shape.text_frame.text.upper():
                if idx != total - 1:
                    _move_slide(prs, idx, total - 1)
                break

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
