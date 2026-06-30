import requests
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from io import BytesIO

# ───────────────────────────────────────────
# 네이버 API 설정 (재발급한 키로 입력하세요)
# ───────────────────────────────────────────
NAVER_CLIENT_ID = "E0ioOPF01SJFcYuk6viO"
NAVER_CLIENT_SECRET = "jlXrOVV8Ws"

# ───────────────────────────────────────────
# 색상 정의 (라이트톤)
# ───────────────────────────────────────────
COLOR_BG = RGBColor(0xFF, 0xFF, 0xFF)        # 흰 배경
COLOR_POINT = RGBColor(0x2C, 0x3E, 0x50)     # 네이비 포인트
COLOR_SUB = RGBColor(0xBD, 0xC3, 0xC7)       # 연회색
COLOR_TEXT = RGBColor(0x2C, 0x2C, 0x2C)      # 진한 텍스트
COLOR_ACCENT = RGBColor(0xC8, 0xA9, 0x7E)    # 골드 포인트

# ───────────────────────────────────────────
# 네이버 이미지 검색
# ───────────────────────────────────────────
def search_image(query):
    url = "https://openapi.naver.com/v1/search/image"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": 1, "filter": "large"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        items = res.json().get("items", [])
        if items:
            return items[0]["link"]
    except:
        pass
    return None

def download_image(url):
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return BytesIO(res.content)
    except:
        pass
    return None

# ───────────────────────────────────────────
# 슬라이드 헬퍼
# ───────────────────────────────────────────
def add_textbox(slide, text, left, top, width, height,
                font_size=12, bold=False, color=None, align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color if color else COLOR_TEXT
    return txBox

def add_rect(slide, left, top, width, height, fill_color, line_color=None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape

# ───────────────────────────────────────────
# 표지 슬라이드
# ───────────────────────────────────────────
def make_cover(prs, project):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 빈 슬라이드
    W, H = 10, 7.5

    # 배경
    add_rect(slide, 0, 0, W, H, COLOR_BG)

    # 왼쪽 포인트 바
    add_rect(slide, 0, 0, 0.08, H, COLOR_POINT)

    # 상단 골드 라인
    add_rect(slide, 0.08, 1.2, W - 0.08, 0.03, COLOR_ACCENT)

    # 프로젝트명
    add_textbox(slide, project["name"], 0.5, 1.5, 7, 1.2,
                font_size=32, bold=True, color=COLOR_POINT)

    # 부제
    add_textbox(slide, "인테리어 스펙북  |  INTERIOR SPEC BOOK",
                0.5, 2.7, 7, 0.5, font_size=11, color=COLOR_SUB)

    # 구분선
    add_rect(slide, 0.5, 3.3, 5, 0.02, COLOR_SUB)

    # 프로젝트 정보
    info_lines = [
        f"위치      {project.get('location', '확인 필요')}",
        f"면적      {project.get('area', '확인 필요')}",
        f"공사기간  {project.get('period', '확인 필요')}",
        f"담당자    {project.get('designer', '확인 필요')}",
    ]
    for i, line in enumerate(info_lines):
        add_textbox(slide, line, 0.5, 3.5 + i * 0.38, 6, 0.4,
                    font_size=10, color=COLOR_TEXT)

    # 작성일
    add_textbox(slide, f"작성일  {project.get('date', '확인 필요')}",
                0.5, 6.8, 4, 0.4, font_size=9, color=COLOR_SUB)

    # 버전
    add_textbox(slide, f"Ver {project.get('version', '1.0')}",
                8.5, 6.8, 1.5, 0.4, font_size=9, color=COLOR_SUB,
                align=PP_ALIGN.RIGHT)

# ───────────────────────────────────────────
# 공간별 스펙 슬라이드
# ───────────────────────────────────────────
def make_space_slide(prs, space_name, items):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    W, H = 10, 7.5

    add_rect(slide, 0, 0, W, H, COLOR_BG)
    add_rect(slide, 0, 0, 0.08, H, COLOR_POINT)
    add_rect(slide, 0.08, 0.9, W - 0.08, 0.03, COLOR_ACCENT)

    # 공간명
    add_textbox(slide, space_name, 0.5, 0.25, 7, 0.7,
                font_size=22, bold=True, color=COLOR_POINT)
    add_textbox(slide, "SPACE SPECIFICATION", 0.5, 0.82, 5, 0.3,
                font_size=8, color=COLOR_SUB)

    # 아이템 카드 (한 슬라이드에 최대 3개)
    for idx, item in enumerate(items[:3]):
        col_x = 0.4 + idx * 3.2
        card_y = 1.1

        # 카드 배경
        add_rect(slide, col_x, card_y, 3.0, 5.8,
                 RGBColor(0xF8, 0xF8, 0xF8),
                 line_color=RGBColor(0xE0, 0xE0, 0xE0))

        # 고유번호 태그
        add_rect(slide, col_x, card_y, 1.0, 0.28, COLOR_POINT)
        add_textbox(slide, item.get("code", ""), col_x + 0.05, card_y + 0.02,
                    0.9, 0.25, font_size=8, bold=True,
                    color=RGBColor(0xFF, 0xFF, 0xFF))

        # 부위명
        add_textbox(slide, item.get("part", ""), col_x + 0.1, card_y + 0.32,
                    2.8, 0.35, font_size=11, bold=True, color=COLOR_POINT)

        # 이미지 영역
        img_url = search_image(item.get("search_query", item.get("product", "")))
        img_data = download_image(img_url) if img_url else None
        if img_data:
            try:
                slide.shapes.add_picture(
                    img_data,
                    Inches(col_x + 0.1), Inches(card_y + 0.72),
                    Inches(2.8), Inches(2.2)
                )
            except:
                add_rect(slide, col_x + 0.1, card_y + 0.72, 2.8, 2.2, COLOR_SUB)
                add_textbox(slide, "이미지 없음", col_x + 0.9, card_y + 1.6,
                            1.2, 0.4, font_size=8, color=COLOR_BG)
        else:
            add_rect(slide, col_x + 0.1, card_y + 0.72, 2.8, 2.2, COLOR_SUB)

        # 제품명
        add_textbox(slide, item.get("product", "미정"),
                    col_x + 0.1, card_y + 3.05, 2.8, 0.4,
                    font_size=9, bold=True, color=COLOR_TEXT)

        # 선택 이유
        add_textbox(slide, f"선택 이유\n{item.get('reason', '-')}",
                    col_x + 0.1, card_y + 3.5, 2.8, 0.9,
                    font_size=8, color=COLOR_TEXT)

        # 예상금액
        add_rect(slide, col_x + 0.1, card_y + 4.5, 2.8, 0.35,
                 RGBColor(0xF0, 0xF0, 0xF0))
        add_textbox(slide, f"예상금액  {item.get('cost', '견적 후 확정')}",
                    col_x + 0.15, card_y + 4.52, 2.7, 0.3,
                    font_size=8, color=COLOR_POINT)

        # 상태 배지
        status = item.get("status", "확인 필요")
        status_color = {
            "확정": RGBColor(0x27, 0xAE, 0x60),
            "검토 중": RGBColor(0xF3, 0x9C, 0x12),
            "선택 필요": RGBColor(0xE7, 0x4C, 0x3C),
        }.get(status, COLOR_SUB)
        add_rect(slide, col_x + 0.1, card_y + 5.0, 1.2, 0.25, status_color)
        add_textbox(slide, status, col_x + 0.12, card_y + 5.02, 1.1, 0.22,
                    font_size=7, bold=True,
                    color=RGBColor(0xFF, 0xFF, 0xFF))

# ───────────────────────────────────────────
# 예산 요약 슬라이드
# ───────────────────────────────────────────
def make_budget_slide(prs, budget_items):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    W, H = 10, 7.5

    add_rect(slide, 0, 0, W, H, COLOR_BG)
    add_rect(slide, 0, 0, 0.08, H, COLOR_POINT)
    add_rect(slide, 0.08, 0.9, W - 0.08, 0.03, COLOR_ACCENT)

    add_textbox(slide, "전체 예산 요약", 0.5, 0.2, 7, 0.7,
                font_size=22, bold=True, color=COLOR_POINT)
    add_textbox(slide, "BUDGET SUMMARY", 0.5, 0.82, 5, 0.3,
                font_size=8, color=COLOR_SUB)

    # 헤더
    headers = ["공종", "예상금액", "상태"]
    col_w = [3.5, 2.5, 2.0]
    col_x = [0.5, 4.0, 6.5]
    row_y = 1.1

    add_rect(slide, 0.4, row_y, 9.2, 0.35, COLOR_POINT)
    for i, h in enumerate(headers):
        add_textbox(slide, h, col_x[i], row_y + 0.05, col_w[i], 0.28,
                    font_size=9, bold=True,
                    color=RGBColor(0xFF, 0xFF, 0xFF))

    for j, item in enumerate(budget_items):
        ry = row_y + 0.35 + j * 0.38
        bg = RGBColor(0xF8, 0xF8, 0xF8) if j % 2 == 0 else COLOR_BG
        add_rect(slide, 0.4, ry, 9.2, 0.36, bg)

        add_textbox(slide, item["name"], col_x[0], ry + 0.05,
                    col_w[0], 0.28, font_size=9, color=COLOR_TEXT)
        add_textbox(slide, item["amount"], col_x[1], ry + 0.05,
                    col_w[1], 0.28, font_size=9, color=COLOR_TEXT)
        add_textbox(slide, item["status"], col_x[2], ry + 0.05,
                    col_w[2], 0.28, font_size=9, color=COLOR_TEXT)

    # 합계선
    total_y = row_y + 0.35 + len(budget_items) * 0.38 + 0.1
    add_rect(slide, 0.4, total_y, 9.2, 0.02, COLOR_POINT)
    add_textbox(slide, "※ 위 금액은 부가세 별도이며, 현장 실측 후 확정됩니다.",
                0.5, total_y + 0.1, 8, 0.4, font_size=8, color=COLOR_SUB)

# ───────────────────────────────────────────
# 메인 실행
# ───────────────────────────────────────────
def create_specbook(project, spaces, budget_items, output_path="specbook.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # 1. 표지
    make_cover(prs, project)

    # 2. 예산 요약
    make_budget_slide(prs, budget_items)

    # 3. 공간별 슬라이드 (아이템 3개씩 나눠서 생성)
    for space_name, items in spaces.items():
        for i in range(0, len(items), 3):
            label = space_name if i == 0 else f"{space_name} (계속)"
            make_space_slide(prs, label, items[i:i+3])

    prs.save(output_path)
    print(f"✅ 스펙북 생성 완료: {output_path}")

# ───────────────────────────────────────────
# 실행 예시 데이터
# ───────────────────────────────────────────
if __name__ == "__main__":

    project = {
        "name": "확인 필요",
        "location": "확인 필요",
        "area": "확인 필요",
        "period": "확인 필요",
        "designer": "확인 필요",
        "date": "2026.06.17",
        "version": "1.0"
    }

    budget_items = [
        {"name": "철거 공사", "amount": "견적 후 확정", "status": "확인 필요"},
        {"name": "목공 공사", "amount": "견적 후 확정", "status": "확인 필요"},
        {"name": "바닥재", "amount": "견적 후 확정", "status": "확인 필요"},
        {"name": "도장 공사", "amount": "견적 후 확정", "status": "확인 필요"},
        {"name": "타일 공사", "amount": "견적 후 확정", "status": "확인 필요"},
        {"name": "조명", "amount": "견적 후 확정", "status": "확인 필요"},
        {"name": "가구", "amount": "견적 후 확정", "status": "확인 필요"},
        {"name": "욕실", "amount": "견적 후 확정", "status": "확인 필요"},
    ]

    spaces = {
        "거실": [
            {
                "code": "FL-01",
                "part": "바닥",
                "product": "LX하우시스 강마루",
                "search_query": "LX하우시스 강마루 거실 바닥",
                "reason": "내구성이 높고 관리가 쉬우며 한국 주거환경에 적합",
                "cost": "견적 후 확정",
                "status": "검토 중"
            },
            {
                "code": "WL-01",
                "part": "벽지",
                "product": "LG하우시스 실크벽지",
                "search_query": "LG하우시스 실크벽지 거실",
                "reason": "오염에 강하고 시공이 용이하며 고급스러운 질감",
                "cost": "견적 후 확정",
                "status": "검토 중"
            },
            {
                "code": "LT-01",
                "part": "조명",
                "product": "LED 매입등",
                "search_query": "거실 LED 매입등 인테리어",
                "reason": "천장을 깔끔하게 유지하면서 충분한 조도 확보",
                "cost": "견적 후 확정",
                "status": "선택 필요"
            }
        ],
        "주방": [
            {
                "code": "FL-02",
                "part": "바닥",
                "product": "포세린 타일",
                "search_query": "주방 포세린 타일 바닥",
                "reason": "물과 기름에 강하고 청소가 쉬움",
                "cost": "견적 후 확정",
                "status": "검토 중"
            },
            {
                "code": "KT-01",
                "part": "싱크대",
                "product": "한샘 키친바흐",
                "search_query": "한샘 키친바흐 싱크대",
                "reason": "국내 1위 브랜드, AS 용이, 다양한 컬러 옵션",
                "cost": "견적 후 확정",
                "status": "선택 필요"
            }
        ]
    }

    create_specbook(project, spaces, budget_items, "interior_specbook.pptx")
