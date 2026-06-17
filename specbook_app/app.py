"""
인테리어 스펙북 자동 생성기 — 디자인 리뉴얼
"""
import streamlit as st
from image_search import search_image
from materials_db import DB, SPACE_ITEMS, TIERS
from pptx_generator import generate_pptx

# ── 페이지 설정 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="스펙북 생성기",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 커스텀 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

  /* 전체 배경 */
  .stApp { background: #F7F5F2; }

  /* 헤더 숨김 */
  #MainMenu, footer, header { visibility: hidden; }

  /* 커스텀 헤더 */
  .app-header {
    background: #2C2C2C;
    padding: 28px 40px;
    margin: -1rem -1rem 2rem -1rem;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .app-header h1 {
    color: #fff;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
  }
  .app-header .accent { color: #C8A97E; }
  .app-header p { color: #999; font-size: 0.85rem; margin: 4px 0 0; }

  /* 섹션 타이틀 */
  .section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #C8A97E;
    margin-bottom: 12px;
  }

  /* 프로젝트 입력 카드 */
  .project-card {
    background: #fff;
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border: 1px solid #E8E0D8;
  }

  /* 공간 탭 */
  .space-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 0 8px;
    border-bottom: 2px solid #2C2C2C;
    margin-bottom: 20px;
  }
  .space-icon { font-size: 1.4rem; }
  .space-name { font-size: 1.15rem; font-weight: 700; color: #2C2C2C; }

  /* 자재 행 */
  .item-row {
    background: #fff;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border: 1px solid #E8E0D8;
    transition: box-shadow 0.2s;
  }
  .item-row:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.07); }
  .item-label { font-size: 0.82rem; font-weight: 700; color: #555; margin-bottom: 8px; }

  /* 등급 버튼 */
  div[data-testid="stButton"] > button {
    border-radius: 6px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    height: 36px !important;
    border: 1.5px solid #E0D8D0 !important;
    background: #fff !important;
    color: #555 !important;
    transition: all 0.15s !important;
  }
  div[data-testid="stButton"] > button:hover {
    border-color: #C8A97E !important;
    color: #C8A97E !important;
  }

  /* 선택된 카드 */
  .sel-card {
    background: #FAFAF8;
    border-radius: 8px;
    padding: 12px 14px;
    border-left: 3px solid #C8A97E;
    margin-top: 8px;
  }
  .sel-product { font-size: 0.92rem; font-weight: 700; color: #2C2C2C; }
  .sel-brand   { font-size: 0.78rem; color: #888; margin: 2px 0; }
  .sel-price   { font-size: 0.88rem; font-weight: 700; color: #C8A97E; }
  .sel-note    { font-size: 0.75rem; color: #aaa; margin-top: 4px; }

  /* 등급 뱃지 */
  .badge-최저가 { background:#E8F5E9; color:#2E7D32; padding:2px 8px; border-radius:20px; font-size:0.72rem; font-weight:700; }
  .badge-보통   { background:#FFF8E1; color:#F57F17; padding:2px 8px; border-radius:20px; font-size:0.72rem; font-weight:700; }
  .badge-최고가 { background:#F3E5F5; color:#7B1FA2; padding:2px 8px; border-radius:20px; font-size:0.72rem; font-weight:700; }

  /* 이미지 갤러리 */
  .img-gallery { display:flex; gap:8px; margin-top:8px; flex-wrap:wrap; }

  /* 생성 버튼 */
  .gen-section {
    background: #2C2C2C;
    border-radius: 12px;
    padding: 28px 32px;
    text-align: center;
    margin-top: 32px;
  }
  .gen-title { color: #fff; font-size: 1.1rem; font-weight: 700; margin-bottom: 6px; }
  .gen-sub   { color: #888; font-size: 0.82rem; margin-bottom: 20px; }

  /* Streamlit 기본 스타일 오버라이드 */
  .stTextInput > div > div > input {
    border-radius: 8px !important;
    border: 1.5px solid #E0D8D0 !important;
    background: #FAFAF8 !important;
    font-size: 0.88rem !important;
  }
  .stMultiSelect > div { border-radius: 8px !important; }

  /* 탭 스타일 */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #EEEBE6;
    padding: 4px;
    border-radius: 10px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    font-weight: 600;
    font-size: 0.85rem;
    color: #888;
  }
  .stTabs [aria-selected="true"] {
    background: #fff !important;
    color: #2C2C2C !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  }

  .stDivider { border-color: #E8E0D8 !important; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div>
    <h1>Interior <span class="accent">Spec Book</span> Generator</h1>
    <p>등급을 선택하면 AI가 자재를 추천하고 PPT를 자동 생성합니다</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 세션 초기화 ──────────────────────────────────────────────────────────────────
if "selections" not in st.session_state:
    st.session_state.selections = {}
if "images" not in st.session_state:
    st.session_state.images = {}

# ── 탭 구성 ────────────────────────────────────────────────────────────────────
tab_project, tab_materials, tab_export = st.tabs(["① 프로젝트 정보", "② 자재 선택", "③ PPT 생성"])

# ════════════════════════════════════════════════════════════════════════════════
# 탭 1 — 프로젝트 정보
# ════════════════════════════════════════════════════════════════════════════════
with tab_project:
    st.markdown('<p class="section-title">Project Information</p>', unsafe_allow_html=True)
    st.markdown('<div class="project-card">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        proj_name     = st.text_input("프로젝트명", "○○ 아파트 리모델링", key="pname")
        proj_location = st.text_input("위치",      "서울시 강남구",       key="ploc")
    with c2:
        proj_area     = st.text_input("면적",       "84㎡ (25.4평)",       key="parea")
        proj_period   = st.text_input("공사기간",   "2026.07 ~ 2026.08",   key="pper")
    with c3:
        proj_designer = st.text_input("담당자",     "홍길동",              key="pdes")
        proj_date     = st.text_input("작성일",     "2026.06.17",          key="pdate")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<p class="section-title">공간 선택</p>', unsafe_allow_html=True)
    spaces = list(SPACE_ITEMS.keys())
    SPACE_ICONS = {"거실": "🛋", "침실": "🛏", "주방": "🍳", "욕실": "🚿", "현관": "🚪"}
    selected_spaces = st.multiselect(
        "적용할 공간",
        spaces,
        default=spaces[:3],
        format_func=lambda s: f"{SPACE_ICONS.get(s, '')} {s}",
        key="spaces",
    )

    if selected_spaces:
        st.info(f"**{len(selected_spaces)}개 공간** 선택됨 — ② 자재 선택 탭으로 이동하세요")

project = {
    "name":     st.session_state.get("pname",  "○○ 아파트 리모델링"),
    "location": st.session_state.get("ploc",   "서울시 강남구"),
    "area":     st.session_state.get("parea",  "84㎡"),
    "period":   st.session_state.get("pper",   ""),
    "designer": st.session_state.get("pdes",   ""),
    "date":     st.session_state.get("pdate",  ""),
}

# ════════════════════════════════════════════════════════════════════════════════
# 탭 2 — 자재 선택
# ════════════════════════════════════════════════════════════════════════════════
with tab_materials:
    selected_spaces = st.session_state.get("spaces", list(SPACE_ITEMS.keys())[:3])
    if not selected_spaces:
        st.info("① 프로젝트 정보 탭에서 공간을 먼저 선택해주세요.")
    else:
        TIER_LABEL = {"최저가": "🟢 최저가", "보통": "🟡 보통", "최고가": "🟣 최고가"}

        for space in selected_spaces:
            icon = SPACE_ICONS.get(space, "")
            st.markdown(f"""
            <div class="space-header">
              <span class="space-icon">{icon}</span>
              <span class="space-name">{space}</span>
            </div>""", unsafe_allow_html=True)

            items = SPACE_ITEMS[space]
            if space not in st.session_state.selections:
                st.session_state.selections[space] = {}

            for item in items:
                key = f"{space}_{item}"
                sel = st.session_state.selections[space].get(item)

                with st.container():
                    st.markdown(f'<div class="item-label">· {item}</div>', unsafe_allow_html=True)
                    btn_cols = st.columns([1, 1, 1, 4])

                    for ti, tier in enumerate(TIERS):
                        with btn_cols[ti]:
                            is_selected = sel and sel.get("tier") == tier
                            btn_type = "primary" if is_selected else "secondary"
                            if st.button(TIER_LABEL[tier], key=f"btn_{key}_{tier}",
                                         use_container_width=True, type=btn_type):
                                mat = DB[space][item][tier]
                                imgs = search_image(mat["search_query"], count=3)
                                st.session_state.selections[space][item] = {
                                    "tier": tier, **mat,
                                    "image_url":  imgs[0]["url"]  if imgs else "",
                                    "source_url": imgs[0]["page"] if imgs else "",
                                }
                                st.session_state.images[key] = imgs
                                st.rerun()

                    # 선택 결과 표시
                    if sel:
                        with btn_cols[3]:
                            img_c, info_c = st.columns([1, 2])
                            imgs = st.session_state.images.get(key, [])

                            with img_c:
                                if imgs:
                                    st.image(imgs[0]["url"], use_container_width=True)
                                    # 이미지 교체 옵션
                                    if len(imgs) > 1:
                                        alt_cols = st.columns(len(imgs) - 1)
                                        for ii, img in enumerate(imgs[1:], 1):
                                            with alt_cols[ii - 1]:
                                                st.image(img["url"], use_container_width=True)
                                                if st.button("선택", key=f"alt_{key}_{ii}", use_container_width=True):
                                                    st.session_state.selections[space][item]["image_url"]  = img["url"]
                                                    st.session_state.selections[space][item]["source_url"] = img["page"]
                                                    st.rerun()

                            with info_c:
                                tier_badge = f'<span class="badge-{sel["tier"]}">{sel["tier"]}</span>'
                                st.markdown(f"""
                                <div class="sel-card">
                                  {tier_badge}
                                  <div class="sel-product">{sel['product']}</div>
                                  <div class="sel-brand">{sel['brand']} &nbsp;|&nbsp; {sel.get('spec','')}</div>
                                  <div class="sel-price">{sel['price']}</div>
                                  <div class="sel-note">{sel.get('note','')}</div>
                                </div>""", unsafe_allow_html=True)
                                if sel.get("source_url"):
                                    st.caption(f"[이미지 출처]({sel['source_url']})")

                    st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:6px 0;'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# 탭 3 — PPT 생성
# ════════════════════════════════════════════════════════════════════════════════
with tab_export:
    total = sum(len(v) for v in st.session_state.selections.values())
    spaces_done = [s for s, v in st.session_state.selections.items() if v]

    st.markdown('<p class="section-title">Export Summary</p>', unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    m1.metric("선택된 공간", f"{len(spaces_done)}개")
    m2.metric("선택된 자재", f"{total}개")

    if spaces_done:
        st.markdown("**선택 현황**")
        for space in spaces_done:
            items_list = ", ".join(
                f"{item} ({sel['tier']})"
                for item, sel in st.session_state.selections[space].items()
            )
            st.markdown(f"- **{space}**: {items_list}")

    st.markdown("---")

    col_gen, _ = st.columns([2, 3])
    with col_gen:
        if st.button("🎨  PPT 스펙북 생성", type="primary", use_container_width=True, disabled=total == 0):
            with st.spinner("이미지 로딩 및 PPT 생성 중..."):
                space_data = {
                    space: [{"item": item, **sel} for item, sel in items.items()]
                    for space, items in st.session_state.selections.items()
                    if items
                }
                pptx_bytes = generate_pptx(project, space_data)

            proj_name = st.session_state.get("pname", "스펙북")
            st.download_button(
                label="⬇️  PPT 다운로드",
                data=pptx_bytes,
                file_name=f"{proj_name}_스펙북.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
            st.success("생성 완료! 위 버튼으로 다운로드하세요.")

    if total == 0:
        st.caption("② 자재 선택 탭에서 자재를 선택하면 생성 버튼이 활성화됩니다.")
