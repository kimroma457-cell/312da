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

def _set_text(shape, text: str, font_size_pt: float | None = None):
    """shape 텍스트를 교체한다 (서식은 첫 run 기준 유지). word_wrap 강제 비활성화."""
    if not shape or not shape.has_text_frame:
        return
    tf = shape.text_frame
    tf.word_wrap = False  # 줄바꿈 금지 — 셀 경계 초과 방지
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

        if "TAILORED CLASSIC" in text.upper():
            _set_text(shape, company or text)
        elif any(kw in text for kw in ["위치:", "면적:", "공사기간:"]):
            _set_text(shape, info)
        elif len(text) > 0 and len(text) < 80 and "INTERIOR" not in text.upper() \
                and "SPEC" not in text.upper() and "2026" not in text:
            # 서브타이틀 후보 (짧은 텍스트이면서 메인 타이틀이 아닌 것)
            if any(kw in text for kw in ["·", "DESICODE", "아파트", "리모델링", "designer"]):
                _set_text(shape, subtitle)


def _update_materials(slide, common_materials: list[dict]):
    """슬라이드 4: Materials & Finishes — 공통 자재 슬롯 업데이트."""
    if not common_materials:
        return
    SLOT_CODES = ["FLOOR", "WALL", "PANEL", "TILE", "METAL", "TEXTILE"]
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip().upper()
        for si, code in enumerate(SLOT_CODES):
            if code == text and si < len(common_materials):
                mat = common_materials[si]
                _set_text(shape, mat.get("item_code", code))
                break


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
                _set_text(shape, item.get("product", ""), font_size_pt=6)
                break
            if _near(l, 1.38) and _near(t, rt + 0.50, 0.14):
                _set_text(shape, item.get("spec", ""), font_size_pt=6.5)
                break
            if _near(l, 4.45, 0.18) and _near(t, rt, 0.30):
                _set_text(shape, item.get("finish", ""), font_size_pt=6.5)
                break
            if _near(l, 8.80, 0.18) and _near(t, rt, 0.30):
                _set_text(shape, item.get("vendor", ""), font_size_pt=6.5)
                break


def _update_model_slide(slide, room_name: str):
    """모델링 이미지 슬라이드: VIEW 박스에 방 이름 추가."""
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip()
        if text.startswith("VIEW"):
            _set_text(shape, f"{text}  |  {room_name}")


def _update_ffande(slide, items: list[dict]):
    """FF&E 슬라이드: 행 데이터 업데이트 (최대 8행)."""
    ROW_Y   = [1.75, 2.22, 2.69, 3.16, 3.63, 4.10, 4.57, 5.04]
    # 실제 컬럼: ITEM=1.55" ROOM=0.85" QTY=0.45" SPEC=2.35" FINISH=1.6" VENDOR=0.9" NOTE=0.9"
    COL_X   = [0.50, 2.15, 3.05, 3.58, 5.98, 7.63, 8.60]
    COL_W   = [1.55, 0.85, 0.45, 2.35, 1.60, 0.90, 0.90]  # 각 컬럼 실제 너비
    COL_KEY = ["product", "room", "qty", "spec", "finish", "vendor", "note"]
    COL_PT  = {"product": 6.0, "room": 6.5, "qty": 6.5,
               "spec": 6.5, "finish": 6.5, "vendor": 6.5, "note": 6.5}

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        l, t = shape.left, shape.top
        w = shape.width

        # 배경 구분선(전체 행 너비) 제외 — W > 2.5" 이면 데이터 셀이 아님
        if w > _emu(2.5) and shape.has_text_frame and not shape.text_frame.text.strip():
            continue

        for ri, ry in enumerate(ROW_Y):
            if ri >= len(items):
                break
            item = items[ri]
            for cx, cw, ckey in zip(COL_X, COL_W, COL_KEY):
                # X 위치와 너비 모두 검증해서 배경 shape 오매칭 방지
                if _near(l, cx, 0.12) and _near(w / 914400, cw, 0.25) and _near(t, ry, 0.20):
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
    rooms:   [{name, name_en, items:[{item_code, product, spec, finish,
                                      vendor, qty, note, image_url, room}]}]
    common_materials: [{item_code, product, spec, finish, vendor}] 최대 6개
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

    # 2. 공통 자재 수정
    if common_materials:
        _update_materials(prs.slides[IDX_MATERIALS], common_materials)

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
        _update_model_slide(m, room["name"])

        room_slide_counts.append(n_chunks + 1)

    total_room_slides = sum(room_slide_counts)

    # 4. FF&E 수정 + 8개 초과 시 슬라이드 복사
    all_ff = []
    for room in rooms:
        for it in room.get("items", []):
            all_ff.append({**it, "room": it.get("room", room["name"])})

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
