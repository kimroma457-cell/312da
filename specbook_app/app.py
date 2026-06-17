"""
인테리어 스펙북 생성기 — 검색 기반 AI 추천 + 다중 공간 지원
"""
import os
import streamlit as st
from image_search import search_image
from ai_recommender import recommend
from pptx_generator import generate_pptx

# ── 페이지 설정 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="스펙북 생성기",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;}
.stApp{background:#F7F5F2;}
#MainMenu,footer,header{visibility:hidden;}

/* 헤더 */
.top-bar{
  background:#1A1816;padding:20px 28px;
  margin:-1rem -1rem 1.5rem -1rem;
  display:flex;align-items:center;gap:14px;
}
.top-bar h1{color:#fff;font-size:1.4rem;font-weight:700;margin:0;letter-spacing:1px;}
.top-bar .sub{color:#8C7F74;font-size:0.78rem;margin:3px 0 0;}
.gold{color:#C8A97E;}

/* 카드 */
.card{background:#fff;border-radius:10px;padding:20px 24px;
      border:1px solid #E8E2DC;margin-bottom:12px;}
.card-dark{background:#1A1816;border-radius:10px;padding:20px 24px;margin-bottom:12px;}

/* 공간 헤더 */
.room-header{display:flex;align-items:center;justify-content:space-between;
             border-bottom:2px solid #1A1816;padding-bottom:8px;margin-bottom:16px;}
.room-name{font-size:1rem;font-weight:700;color:#1A1816;}
.room-en{font-size:0.75rem;color:#9A8F86;margin-left:8px;}

/* 자재 행 */
.item-row{display:flex;align-items:flex-start;gap:12px;
          padding:12px 0;border-bottom:1px solid #EDE8E2;}
.item-label-sm{font-size:0.7rem;font-weight:700;color:#9A8F86;letter-spacing:1px;}
.item-product{font-size:0.92rem;font-weight:700;color:#1A1816;}
.item-spec{font-size:0.75rem;color:#9A8F86;margin-top:2px;}
.item-finish{font-size:0.82rem;color:#4A4540;margin-top:2px;}

/* 등급 뱃지 */
.badge{display:inline-block;padding:2px 8px;border-radius:20px;
       font-size:0.68rem;font-weight:700;margin-bottom:4px;}
.badge-최저가{background:#E8F5E9;color:#2E7D32;}
.badge-보통  {background:#FFF8E1;color:#F57F17;}
.badge-최고가{background:#F3E5F5;color:#7B1FA2;}

/* 가격 */
.price-tag{font-size:0.82rem;font-weight:700;color:#C8A97E;}

/* 섹션 라벨 */
.sec-label{font-size:0.65rem;font-weight:700;letter-spacing:2px;
           text-transform:uppercase;color:#C8A97E;margin-bottom:8px;}

/* 사이드바 */
section[data-testid="stSidebar"]{background:#1A1816!important;}
section[data-testid="stSidebar"] *{color:#E8E2DC!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:#2C2A28!important;border:1px solid #3C3A38!important;
  color:#C8A97E!important;border-radius:6px!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:#C8A97E!important;color:#1A1816!important;}
section[data-testid="stSidebar"] input{
  background:#2C2A28!important;border-color:#3C3A38!important;color:#E8E2DC!important;}
section[data-testid="stSidebar"] select{
  background:#2C2A28!important;border-color:#3C3A38!important;}

/* 등급 선택 버튼 */
.stButton>button{border-radius:6px!important;font-size:0.8rem!important;font-weight:600!important;}

/* 탭 */
.stTabs [data-baseweb="tab-list"]{background:#EEEBE6;padding:4px;border-radius:10px;gap:3px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:600;font-size:0.83rem;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;box-shadow:0 1px 4px rgba(0,0,0,.1);}
</style>
""", unsafe_allow_html=True)

# ── 헤더 ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
  <div>
    <h1>INTERIOR <span class="gold">SPEC BOOK</span> GENERATOR</h1>
    <div class="sub">검색어를 입력하면 AI가 최저가 · 보통 · 최고가 자재를 추천합니다</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── API 키 입력 (사이드바 최상단) ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Anthropic API Key")
    api_key_input = st.text_input(
        "API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
        placeholder="sk-ant-api03-...",
        label_visibility="collapsed",
    )
    if api_key_input:
        os.environ["ANTHROPIC_API_KEY"] = api_key_input
        st.success("✓ 키 설정됨", icon="🔒")
    else:
        st.warning("API 키를 입력하세요")
    st.markdown("---")

# ── 세션 초기화 ──────────────────────────────────────────────────────────────────
if "rooms" not in st.session_state:
    # rooms: [{id, name, name_en, items:[{...}]}]
    st.session_state.rooms = []
if "project" not in st.session_state:
    st.session_state.project = {
        "name": "○○ 아파트 리모델링",
        "location": "서울시 강남구",
        "area": "84㎡ (25.4평)",
        "period": "2026.07 ~ 2026.08",
        "designer": "홍길동",
        "date": "2026.06.17",
    }

ROOM_PRESETS = {
    "거실": "Living Room",
    "침실": "Bedroom",
    "주방": "Kitchen",
    "욕실": "Bathroom",
    "현관": "Entrance",
    "드레스룸": "Dressing Room",
    "서재": "Study Room",
    "다이닝": "Dining Room",
}

# ── 사이드바 — 프로젝트 정보 + 공간 추가 ──────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 프로젝트 정보")
    p = st.session_state.project
    p["name"]     = st.text_input("프로젝트명", p["name"])
    p["location"] = st.text_input("위치",       p["location"])
    p["area"]     = st.text_input("면적",        p["area"])
    p["period"]   = st.text_input("공사기간",    p["period"])
    p["designer"] = st.text_input("담당자",      p["designer"])
    p["date"]     = st.text_input("작성일",      p["date"])

    st.markdown("---")
    st.markdown("### 🏠 공간 추가")
    st.caption("같은 공간을 여러 번 추가할 수 있습니다")

    preset = st.selectbox("공간 선택", list(ROOM_PRESETS.keys()) + ["직접 입력"])
    if preset == "직접 입력":
        custom_ko = st.text_input("공간명 (한글)")
        custom_en = st.text_input("공간명 (영어)")
        add_name    = custom_ko
        add_name_en = custom_en
    else:
        add_name    = preset
        add_name_en = ROOM_PRESETS[preset]

    # 이 공간이 몇 번째인지 자동 카운트
    same_count = sum(1 for r in st.session_state.rooms if r["name"] == add_name)
    display_name = f"{add_name}{same_count + 1}" if same_count > 0 else add_name

    if st.button("＋ 공간 추가", use_container_width=True):
        if add_name:
            st.session_state.rooms.append({
                "id":      len(st.session_state.rooms),
                "name":    display_name,
                "name_en": add_name_en,
                "items":   [],
            })
            st.rerun()

    # 공간 목록
    if st.session_state.rooms:
        st.markdown("---")
        st.markdown("**추가된 공간**")
        for i, room in enumerate(st.session_state.rooms):
            col_r, col_del = st.columns([4, 1])
            col_r.markdown(f"• {room['name']}")
            if col_del.button("✕", key=f"del_room_{i}"):
                st.session_state.rooms.pop(i)
                st.rerun()

# ── 메인 영역 ───────────────────────────────────────────────────────────────────
if not st.session_state.rooms:
    st.info("👈 왼쪽 사이드바에서 공간을 추가하세요.")
    st.stop()

# 탭: 각 공간 + PPT 생성
room_names = [r["name"] for r in st.session_state.rooms]
tabs = st.tabs(room_names + ["📄 PPT 생성"])

for tab_i, (tab, room) in enumerate(zip(tabs[:-1], st.session_state.rooms)):
    with tab:
        st.markdown(f"""
        <div class="room-header">
          <div><span class="room-name">{room['name']}</span>
               <span class="room-en">{room['name_en']}</span></div>
        </div>""", unsafe_allow_html=True)

        # ── 검색 ────────────────────────────────────────────────────────────
        with st.expander("🔍 자재 검색 및 추가", expanded=len(room["items"]) == 0):
            search_col, btn_col = st.columns([5, 1])
            with search_col:
                query = st.text_input(
                    "검색어 입력",
                    placeholder="예: 거실 소파, 오크 헤링본 마루, 펜던트 조명 ...",
                    key=f"search_{tab_i}",
                    label_visibility="collapsed",
                )
            with btn_col:
                do_search = st.button("AI 분석", key=f"sbtn_{tab_i}",
                                      use_container_width=True, type="primary")

            if do_search and query:
                with st.spinner(f"'{query}' 분석 중..."):
                    result = recommend(query)

                if "error" in result:
                    st.error(f"오류: {result['error']}")
                else:
                    st.markdown(f"**{result.get('item_label', query)}** — 등급별 추천")
                    t_cols = st.columns(3)
                    for ti, tier in enumerate(["최저가", "보통", "최고가"]):
                        mat = result.get(tier, {})
                        with t_cols[ti]:
                            badge_class = f"badge-{tier}"
                            imgs = search_image(mat.get("search_query", query), count=1)
                            img_url = imgs[0]["url"] if imgs else ""
                            if img_url:
                                st.image(img_url, use_container_width=True)
                            st.markdown(f'<span class="badge {badge_class}">{tier}</span>', unsafe_allow_html=True)
                            st.markdown(f"**{mat.get('product','')}**")
                            st.caption(f"{mat.get('brand','')}  |  {mat.get('spec','')}")
                            st.markdown(f'<span class="price-tag">{mat.get("price","")}</span>', unsafe_allow_html=True)
                            st.caption(mat.get("finish", ""))

                            if st.button(f"✚ {tier} 선택", key=f"add_{tab_i}_{tier}",
                                         use_container_width=True):
                                item_entry = {
                                    "item_label": result.get("item_label", query),
                                    "item_code":  result.get("item_code", "ITEM"),
                                    "tier":       tier,
                                    "product":    mat.get("product", ""),
                                    "brand":      mat.get("brand", ""),
                                    "spec":       mat.get("spec", ""),
                                    "finish":     mat.get("finish", ""),
                                    "price":      mat.get("price", ""),
                                    "vendor":     mat.get("vendor", ""),
                                    "note":       mat.get("note", ""),
                                    "image_url":  img_url,
                                    "source_url": imgs[0]["page"] if imgs else "",
                                    "search_query": mat.get("search_query", query),
                                }
                                st.session_state.rooms[tab_i]["items"].append(item_entry)
                                st.rerun()

        # ── 선택된 자재 목록 ─────────────────────────────────────────────────
        items = room["items"]
        if not items:
            st.caption("아직 선택된 자재가 없습니다. 위 검색창에서 추가하세요.")
        else:
            st.markdown(f'<p class="sec-label">선택된 자재 {len(items)}개</p>', unsafe_allow_html=True)
            for ii, item in enumerate(items):
                with st.container():
                    ic1, ic2, ic3 = st.columns([1, 5, 1])
                    with ic1:
                        if item.get("image_url"):
                            st.image(item["image_url"], use_container_width=True)
                    with ic2:
                        badge_c = f"badge-{item['tier']}"
                        st.markdown(f"""
                        <span class="badge {badge_c}">{item['tier']}</span>
                        <span class="item-label-sm"> {item['item_code']}</span><br>
                        <span class="item-product">{item['product']}</span><br>
                        <span class="item-spec">{item.get('spec','')}</span><br>
                        <span class="item-finish">{item.get('finish','')}</span>
                        <span class="price-tag"> &nbsp; {item.get('price','')}</span>
                        """, unsafe_allow_html=True)
                    with ic3:
                        if st.button("삭제", key=f"del_{tab_i}_{ii}"):
                            st.session_state.rooms[tab_i]["items"].pop(ii)
                            st.rerun()
                    st.markdown("<hr style='border:none;border-top:1px solid #EDE8E2;margin:6px 0;'>",
                                unsafe_allow_html=True)

# ── PPT 생성 탭 ─────────────────────────────────────────────────────────────────
with tabs[-1]:
    st.markdown('<p class="sec-label">Export Summary</p>', unsafe_allow_html=True)

    total_items = sum(len(r["items"]) for r in st.session_state.rooms)
    m1, m2 = st.columns(2)
    m1.metric("공간 수", len(st.session_state.rooms))
    m2.metric("자재 수", total_items)

    if st.session_state.rooms:
        for room in st.session_state.rooms:
            if room["items"]:
                st.markdown(f"**{room['name']}** ({len(room['items'])}개)")
                for item in room["items"]:
                    badge_c = f"badge-{item['tier']}"
                    st.markdown(
                        f'<span class="badge {badge_c}">{item["tier"]}</span> '
                        f'{item["item_code"]} · {item["product"]}',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("⚠️ ANTHROPIC_API_KEY 환경변수를 설정해야 AI 검색이 작동합니다.")

    gen_col, _ = st.columns([2, 3])
    with gen_col:
        if st.button("🎨  PPT 스펙북 생성", type="primary",
                     use_container_width=True, disabled=total_items == 0):
            with st.spinner("PPT 생성 중... 이미지 다운로드 포함"):
                pptx_bytes = generate_pptx(
                    st.session_state.project,
                    st.session_state.rooms,
                )

            proj_name = st.session_state.project.get("name", "스펙북")
            st.download_button(
                label="⬇️  PPT 다운로드",
                data=pptx_bytes,
                file_name=f"{proj_name}_스펙북.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
            st.success("생성 완료!")

    if total_items == 0:
        st.caption("각 공간 탭에서 자재를 검색 · 추가한 뒤 생성하세요.")
