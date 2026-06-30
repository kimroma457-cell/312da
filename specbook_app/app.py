"""
인테리어 스펙북 생성기 v7
- 색상/대비 전면 개선
- 공간명 입력창 배경 수정
- 스텝바 가독성 개선
- 우측 자재 패널 구조 개선
"""
import re, uuid, json, copy as _copy, io
import streamlit as st
from datetime import datetime
from brands import BRAND_CATALOG, CATEGORY_META
from naver_shopping import search_products
from pptx_generator import generate_pptx

st.set_page_config(page_title="INTERIOR SPEC BOOK", page_icon="🏠",
                   layout="wide", initial_sidebar_state="expanded")

CAT_KEYS = list(BRAND_CATALOG.keys())

# ── 색상 팔레트 ──────────────────────────────────────────────────────────────
# Dark  : #1C1A17  (헤더바, 사이드바 배경)
# Gold  : #C9A87C  (강조, 활성 버튼 배경)
# Cream : #F7F4EF  (앱 배경)
# White : #FFFFFF  (카드, 입력창)
# Gray1 : #4A4540  (본문 텍스트)
# Gray2 : #8A8480  (보조 텍스트)
# Gray3 : #D4D0CA  (테두리)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
  font-family: 'Noto Sans KR', sans-serif;
}

/* ── 앱 배경 ── */
.stApp { background: #F7F4EF !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { display: none !important; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
  background: #1C1A17 !important;
  min-width: 220px !important;
  max-width: 250px !important;
}
[data-testid="stSidebarContent"] { padding: 14px 14px 24px !important; }

/* 사이드바 기본 텍스트 */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {
  color: #C8C0B4 !important;
}

/* 사이드바 입력창 */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
  background: #2A2724 !important;
  border: 1px solid #3C3830 !important;
  color: #F0EAE0 !important;
  border-radius: 7px !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
  border-color: #C9A87C !important;
  box-shadow: 0 0 0 2px rgba(201,168,124,0.15) !important;
}

/* 사이드바 일반 버튼 */
[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  background: #2A2724 !important;
  color: #C8C0B4 !important;
  border: 1px solid #3C3830 !important;
  border-radius: 8px !important;
  font-size: .76rem !important;
  font-weight: 600 !important;
  padding: 7px 10px !important;
  margin-bottom: 3px !important;
  transition: all .15s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: #3C3830 !important;
  border-color: #C9A87C !important;
  color: #F0EAE0 !important;
}

/* 사이드바 primary 버튼 (공간 활성, PPT) */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: #C9A87C !important;
  color: #1C1A17 !important;
  border-color: #C9A87C !important;
  font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
  background: #B8976B !important;
  border-color: #B8976B !important;
}

/* 사이드바 download 버튼 */
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: #2A2724 !important;
  color: #C9A87C !important;
  border: 1px solid #3C3830 !important;
  border-radius: 8px !important;
  width: 100% !important;
  font-size: .76rem !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: #3C3830 !important;
  border-color: #C9A87C !important;
}

/* 사이드바 expander */
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: #242120 !important;
  border: 1px solid #3C3830 !important;
  border-radius: 8px !important;
  margin-bottom: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
  color: #C8C0B4 !important;
  font-size: .78rem !important;
  font-weight: 600 !important;
}

/* 사이드바 file uploader */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
  background: #242120 !important;
  border: 1px dashed #3C3830 !important;
  border-radius: 8px !important;
  padding: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] * {
  font-size: .72rem !important;
}

/* 사이드바 hr */
[data-testid="stSidebar"] hr {
  border-color: #3C3830 !important;
  margin: 10px 0 !important;
}

/* ── 메인 영역 버튼 ── */
.stButton > button {
  border-radius: 8px !important;
  font-size: .76rem !important;
  font-weight: 600 !important;
  background: #FFFFFF !important;
  color: #4A4540 !important;
  border: 1.5px solid #D4D0CA !important;
  padding: 6px 12px !important;
  transition: all .15s !important;
}
.stButton > button:hover {
  background: #FDF9F4 !important;
  border-color: #C9A87C !important;
  color: #1C1A17 !important;
}

/* 메인 primary 버튼 (카테고리/브랜드 선택됨) */
div[data-testid="stButton"] > button[kind="primary"] {
  background: #1C1A17 !important;
  color: #C9A87C !important;
  border-color: #1C1A17 !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background: #C9A87C !important;
  color: #1C1A17 !important;
}

/* ── 입력창 (메인) ── */
.stTextInput input, .stTextArea textarea {
  background: #FFFFFF !important;
  border: 1.5px solid #D4D0CA !important;
  border-radius: 8px !important;
  color: #1C1A17 !important;
  font-size: .80rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #C9A87C !important;
  box-shadow: 0 0 0 2px rgba(201,168,124,0.12) !important;
}
/* 레이블 제거된 입력창 배경 강제 흰색 */
[data-testid="stTextInputRootElement"] input {
  background: #FFFFFF !important;
  color: #1C1A17 !important;
}

/* selectbox */
.stSelectbox select, [data-baseweb="select"] {
  background: #FFFFFF !important;
  border: 1.5px solid #D4D0CA !important;
  border-radius: 8px !important;
  color: #1C1A17 !important;
}

/* ── 탭 (서브탭) ── */
.stTabs [data-baseweb="tab-list"] {
  background: #EDE9E3;
  padding: 4px;
  border-radius: 10px;
  gap: 3px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 7px;
  font-size: .74rem;
  font-weight: 600;
  padding: 6px 16px;
  color: #6B6059 !important;
  background: transparent !important;
  border: none !important;
}
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important;
  color: #1C1A17 !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  padding-top: 12px !important;
}

/* ── form ── */
[data-testid="stForm"] {
  background: #FFFFFF;
  border: 1.5px solid #E8E4DE;
  border-radius: 12px;
  padding: 16px;
}

/* ── expander (메인) ── */
[data-testid="stExpander"] {
  background: #FFFFFF;
  border: 1px solid #E8E4DE !important;
  border-radius: 8px;
}

/* ── 스피너 ── */
.stSpinner > div { border-top-color: #C9A87C !important; }
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def _new_room(name="거실"):
    return {"id": str(uuid.uuid4()), "name": name, "en_name": "Living Room",
            "materials": [], "modeling_images": []}

def _init():
    if "project" not in st.session_state:
        st.session_state.project = {
            "name": "프로젝트명", "client": "", "designer": "",
            "date": datetime.today().strftime("%Y-%m-%d"), "address": ""}
    if "rooms" not in st.session_state:
        st.session_state.rooms = [_new_room("거실")]
    if "current_room_idx" not in st.session_state:
        st.session_state.current_room_idx = 0
    if "logo_bytes" not in st.session_state:
        st.session_state.logo_bytes = None
    if "favorites" not in st.session_state:
        st.session_state.favorites = []
    for k, v in [("sel_cat", None), ("sel_brand", None), ("sel_sub", None),
                 ("search_results", []), ("search_done", False),
                 ("search_keyword", "")]:
        if k not in st.session_state:
            st.session_state[k] = v

_init()

p     = st.session_state.project
rooms = st.session_state.rooms
cur_idx = min(st.session_state.current_room_idx, len(rooms) - 1)
st.session_state.current_room_idx = cur_idx
room  = rooms[cur_idx]

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def _fmt_price(v):
    try: return f"{int(v):,}원"
    except: return str(v) if v else "-"

def _total_price():
    total = 0
    for r in rooms:
        for m in r["materials"]:
            try: total += int(m.get("price", 0)) * m.get("qty", 1)
            except: pass
    return total

def _total_items():
    return sum(len(r["materials"]) for r in rooms)

def _reset_search():
    for k in ("sel_cat", "sel_brand", "sel_sub"):
        st.session_state[k] = None
    st.session_state.search_results = []
    st.session_state.search_done = False
    st.session_state.search_keyword = ""

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # 프로젝트 정보
    with st.expander("📋 프로젝트 정보"):
        p["name"]     = st.text_input("프로젝트명", p["name"], key="p_name")
        p["client"]   = st.text_input("의뢰인", p.get("client", ""), key="p_client")
        p["designer"] = st.text_input("디자이너", p.get("designer", ""), key="p_designer")
        p["date"]     = st.text_input("날짜", p.get("date", ""), key="p_date")
        p["address"]  = st.text_input("현장주소", p.get("address", ""), key="p_addr")

    # 표지 로고
    with st.expander("🖼 표지 로고"):
        logo_file = st.file_uploader("로고 이미지", type=["png","jpg","jpeg"],
                                     key="logo_up", label_visibility="collapsed")
        if logo_file:
            st.session_state.logo_bytes = logo_file.read()
        if st.session_state.logo_bytes:
            st.image(st.session_state.logo_bytes, use_container_width=True)

    # SPACES 레이블
    st.markdown(
        '<p style="font-size:.60rem;font-weight:700;letter-spacing:.12em;'
        'color:#6A6258!important;text-transform:uppercase;margin:12px 0 6px;">SPACES</p>',
        unsafe_allow_html=True)

    # 공간 목록
    for i, r in enumerate(rooms):
        active = (i == cur_idx)
        ca, cb = st.columns([76, 24])
        with ca:
            label = f"▶ {r['name']}" if active else r["name"]
            if st.button(label, key=f"room_sel_{i}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                if not active:
                    st.session_state.current_room_idx = i
                    _reset_search()
                    st.rerun()
        with cb:
            if st.button("×", key=f"room_del_{i}", use_container_width=True):
                if len(rooms) > 1:
                    rooms.pop(i)
                    st.session_state.current_room_idx = max(0, i - 1)
                    _reset_search()
                    st.rerun()

    if st.button("＋ 공간 추가", use_container_width=True):
        rooms.append(_new_room(f"공간{len(rooms)+1}"))
        st.session_state.current_room_idx = len(rooms) - 1
        _reset_search()
        st.rerun()

    st.markdown("---")

    # FILE 레이블
    st.markdown(
        '<p style="font-size:.60rem;font-weight:700;letter-spacing:.12em;'
        'color:#6A6258!important;text-transform:uppercase;margin:0 0 6px;">FILE</p>',
        unsafe_allow_html=True)

    json_data = json.dumps({"project": p, "rooms": rooms}, ensure_ascii=False, indent=2)
    st.download_button("💾 JSON 저장", data=json_data,
                       file_name="specbook.json", mime="application/json",
                       use_container_width=True)

    uploaded = st.file_uploader("JSON 불러오기", type=["json"],
                                key="json_up", label_visibility="visible")
    if uploaded and st.session_state.get("_last_json") != uploaded.name:
        st.session_state._last_json = uploaded.name
        try:
            d = json.loads(uploaded.read())
            if "project" in d:
                st.session_state.project.update(d["project"])
            if "rooms" in d:
                st.session_state.rooms = d["rooms"]
                st.session_state.current_room_idx = 0
            st.rerun()
        except Exception as e:
            st.error(f"JSON 오류: {e}")

    st.markdown("---")

    # EXPORT 레이블
    st.markdown(
        '<p style="font-size:.60rem;font-weight:700;letter-spacing:.12em;'
        'color:#6A6258!important;text-transform:uppercase;margin:0 0 6px;">EXPORT</p>',
        unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:.70rem;color:#8A8480!important;margin-bottom:8px;">'
        f'공간 {len(rooms)}개 &nbsp;·&nbsp; 자재 {_total_items()}개 &nbsp;·&nbsp; '
        f'{_fmt_price(_total_price())}</p>',
        unsafe_allow_html=True)

    if st.button("✦ PPT 스펙북 생성", type="primary", use_container_width=True,
                 key="ppt_gen"):
        with st.spinner("PPT 생성 중..."):
            try:
                buf = generate_pptx(p, rooms, logo_bytes=st.session_state.logo_bytes)
                st.download_button(
                    "⬇ 다운로드", data=buf,
                    file_name=f"specbook_{p['name']}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True, key="ppt_dl")
            except Exception as e:
                st.error(f"PPT 오류: {e}")

# ── 메인 콘텐츠 ───────────────────────────────────────────────────────────────

# 헤더바
st.markdown(
    f'<div style="background:#1C1A17;color:#C9A87C;padding:13px 20px;'
    f'font-size:.90rem;font-weight:700;letter-spacing:.05em;border-radius:10px;'
    f'margin-bottom:16px;">INTERIOR SPEC BOOK &nbsp;·&nbsp; {room["name"]}</div>',
    unsafe_allow_html=True)

# 공간명 + 자재 수
nm_col, cnt_col = st.columns([8, 2])
with nm_col:
    new_name = st.text_input("공간명", room["name"],
                             label_visibility="collapsed",
                             key=f"rname_{room['id']}",
                             placeholder="공간명을 입력하세요")
    if new_name != room["name"]:
        room["name"] = new_name
with cnt_col:
    mat_cnt = len(room["materials"])
    st.markdown(
        f'<div style="text-align:right;padding-top:10px;'
        f'font-size:.78rem;color:#8A8480;">{mat_cnt}개 자재</div>',
        unsafe_allow_html=True)

st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

# ── 2열 레이아웃 ──────────────────────────────────────────────────────────────
left_col, right_col = st.columns([57, 43], gap="large")

# ════════════════════════════════════════════════════════════════════
# 왼쪽: 검색 영역
# ════════════════════════════════════════════════════════════════════
with left_col:
    s_cat   = st.session_state.sel_cat
    s_brand = st.session_state.sel_brand
    s_sub   = st.session_state.sel_sub

    # 스텝바 — 현재 단계 강조
    step_now = 1
    if s_cat:   step_now = 2
    if s_brand: step_now = 3
    if s_sub:   step_now = 4

    steps = [("① 카테고리", 1), ("② 업체", 2), ("③ 제품군", 3), ("④ 검색결과", 4)]
    html_steps = ""
    for label, n in steps:
        if n < step_now:   # 완료
            style = ("background:#EDE1CE;color:#8A6840;border:1.5px solid #D4BC96;"
                     "border-radius:8px;padding:7px 0;text-align:center;"
                     "font-size:.72rem;font-weight:600;flex:1;")
        elif n == step_now:  # 현재
            style = ("background:#1C1A17;color:#C9A87C;border:1.5px solid #1C1A17;"
                     "border-radius:8px;padding:7px 0;text-align:center;"
                     "font-size:.72rem;font-weight:700;flex:1;")
        else:  # 미완
            style = ("background:#F0EDE8;color:#B0A898;border:1.5px solid #E0DCD6;"
                     "border-radius:8px;padding:7px 0;text-align:center;"
                     "font-size:.72rem;font-weight:500;flex:1;")
        html_steps += f'<div style="{style}">{label}</div>'
    st.markdown(
        f'<div style="display:flex;gap:5px;margin-bottom:14px;">{html_steps}</div>',
        unsafe_allow_html=True)

    # 서브탭
    tab_search, tab_fav, tab_manual = st.tabs([
        "🔍 카테고리 검색",
        f"⭐ 즐겨찾기 ({len(st.session_state.favorites)})",
        "✏ 직접 입력"])

    # ── 카테고리 검색 탭 ─────────────────────────────────────────────
    with tab_search:

        # ① 카테고리
        st.markdown(
            '<div style="font-size:.68rem;font-weight:700;color:#8A8480;'
            'letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px;">'
            '① 카테고리 선택</div>', unsafe_allow_html=True)

        rows_cat = [CAT_KEYS[i:i+4] for i in range(0, len(CAT_KEYS), 4)]
        for row in rows_cat:
            cols = st.columns(len(row))
            for col, ck in zip(cols, row):
                meta  = CATEGORY_META.get(ck, {})
                icon  = meta.get("icon", "")
                label = f"{icon} {ck}" if icon else ck
                with col:
                    if st.button(label, key=f"cat_{ck}",
                                 type="primary" if s_cat == ck else "secondary",
                                 use_container_width=True):
                        st.session_state.sel_cat   = ck
                        st.session_state.sel_brand = None
                        st.session_state.sel_sub   = None
                        st.session_state.search_results = []
                        st.session_state.search_done    = False
                        st.rerun()

        # ② 업체
        if s_cat and s_cat in BRAND_CATALOG:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.68rem;font-weight:700;color:#8A8480;'
                'letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px;">'
                '② 업체 / 브랜드</div>', unsafe_allow_html=True)
            brands = [b["name"] for b in BRAND_CATALOG[s_cat]]
            rows_br = [brands[i:i+3] for i in range(0, len(brands), 3)]
            for row in rows_br:
                cols = st.columns(len(row))
                for col, bk in zip(cols, row):
                    with col:
                        if st.button(bk, key=f"br_{bk}",
                                     type="primary" if s_brand == bk else "secondary",
                                     use_container_width=True):
                            st.session_state.sel_brand = bk
                            st.session_state.sel_sub   = None
                            st.session_state.search_results = []
                            st.session_state.search_done    = False
                            st.rerun()

        # ③ 제품군
        brand_entry = next((b for b in BRAND_CATALOG.get(s_cat, [])
                            if b["name"] == s_brand), None) if s_brand else None
        if brand_entry:
            subs = brand_entry["groups"]
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.68rem;font-weight:700;color:#8A8480;'
                'letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px;">'
                '③ 제품군</div>', unsafe_allow_html=True)
            rows_sub = [subs[i:i+4] for i in range(0, len(subs), 4)]
            for row in rows_sub:
                cols = st.columns(len(row))
                for col, sk in zip(cols, row):
                    with col:
                        if st.button(sk, key=f"sub_{sk}",
                                     type="primary" if s_sub == sk else "secondary",
                                     use_container_width=True):
                            st.session_state.sel_sub = sk
                            st.session_state.search_results = []
                            st.session_state.search_done    = False
                            st.session_state.search_keyword = f"{s_brand} {sk}"
                            st.rerun()

        # ④ 검색
        if s_sub:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.68rem;font-weight:700;color:#8A8480;'
                'letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px;">'
                '④ 검색</div>', unsafe_allow_html=True)

            kc, bc = st.columns([7, 3])
            with kc:
                kw = st.text_input("검색어", value=st.session_state.search_keyword,
                                   label_visibility="collapsed",
                                   key="kw_input", placeholder="검색어를 입력하세요")
                st.session_state.search_keyword = kw
            with bc:
                do_search = st.button("🔍 검색", key="do_search", use_container_width=True)

            if do_search and kw.strip():
                with st.spinner("검색 중..."):
                    try:
                        results = search_products(
                        brand=s_brand or "",
                        category=s_cat or "",
                        product_group=s_sub or "",
                        keyword=kw.strip(),
                        count=20,
                    )
                        st.session_state.search_results = results
                        st.session_state.search_done    = True
                    except Exception as e:
                        st.error(f"검색 오류: {e}")
                        st.session_state.search_results = []
                        st.session_state.search_done    = True

            results = st.session_state.search_results
            if st.session_state.search_done:
                if not results:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.markdown(
                        f'<div style="font-size:.68rem;color:#8A8480;margin:4px 0 10px;">'
                        f'{len(results)}개 결과</div>', unsafe_allow_html=True)

                    for item in results:
                        img_url = item.get("image", "")
                        name    = re.sub(r"<[^>]+>", "", item.get("title", ""))
                        brand   = item.get("brand", item.get("mallName", ""))
                        price   = item.get("lprice", "")
                        pid     = item.get("productId", item.get("id", str(uuid.uuid4())))

                        with st.container():
                            rc1, rc2, rc3 = st.columns([2, 6, 2])
                            with rc1:
                                if img_url:
                                    try: st.image(img_url, use_container_width=True)
                                    except: st.markdown("🖼")
                                else:
                                    st.markdown("🖼")
                            with rc2:
                                st.markdown(
                                    f'<div style="font-size:.78rem;font-weight:600;'
                                    f'color:#1C1A17;line-height:1.4;">{name}</div>'
                                    f'<div style="font-size:.68rem;color:#8A8480;margin-top:2px;">'
                                    f'{brand}{"  ·  " + s_cat if s_cat else ""}</div>'
                                    f'<div style="font-size:.76rem;font-weight:700;'
                                    f'color:#C9A87C;margin-top:3px;">{_fmt_price(price)}</div>',
                                    unsafe_allow_html=True)
                            with rc3:
                                if st.button("＋ 추가", key=f"add_{pid}_{room['id']}",
                                             use_container_width=True):
                                    existing = next(
                                        (m for m in room["materials"]
                                         if m.get("product_id") == pid), None)
                                    if existing:
                                        existing["qty"] = existing.get("qty", 1) + 1
                                    else:
                                        room["materials"].append({
                                            "product_id": pid,
                                            "name": name,
                                            "brand": brand,
                                            "category": s_cat or "",
                                            "sub_category": s_sub or "",
                                            "price": price,
                                            "image": img_url,
                                            "qty": 1,
                                            "spec": "",
                                            "finish": "",
                                            "memo": "",
                                        })
                                    st.rerun()
                        st.markdown(
                            '<div style="border-bottom:1px solid #EDE9E3;margin:6px 0;"></div>',
                            unsafe_allow_html=True)

    # ── 즐겨찾기 탭 ───────────────────────────────────────────────
    with tab_fav:
        favs = st.session_state.favorites
        if not favs:
            st.info("즐겨찾기 항목이 없습니다. 자재 카드의 ☆ 버튼으로 추가하세요.")
        else:
            for fi, fav in enumerate(favs):
                fc1, fc2, fc3 = st.columns([2, 6, 2])
                with fc1:
                    if fav.get("image"):
                        try: st.image(fav["image"], use_container_width=True)
                        except: st.markdown("🖼")
                    else:
                        st.markdown("🖼")
                with fc2:
                    st.markdown(
                        f'<div style="font-size:.78rem;font-weight:600;color:#1C1A17;">'
                        f'{fav["name"]}</div>'
                        f'<div style="font-size:.68rem;color:#8A8480;margin-top:2px;">'
                        f'{fav.get("brand","")} · {fav.get("category","")}</div>'
                        f'<div style="font-size:.76rem;font-weight:700;color:#C9A87C;margin-top:3px;">'
                        f'{_fmt_price(fav.get("price",""))}</div>',
                        unsafe_allow_html=True)
                with fc3:
                    if st.button("＋ 추가", key=f"fav_add_{fi}", use_container_width=True):
                        pid = fav.get("product_id", str(uuid.uuid4()))
                        ex  = next((m for m in room["materials"]
                                    if m.get("product_id") == pid), None)
                        if ex:
                            ex["qty"] = ex.get("qty", 1) + 1
                        else:
                            room["materials"].append(_copy.deepcopy(fav))
                        st.rerun()
                st.markdown(
                    '<div style="border-bottom:1px solid #EDE9E3;margin:6px 0;"></div>',
                    unsafe_allow_html=True)

    # ── 직접 입력 탭 ──────────────────────────────────────────────
    with tab_manual:
        with st.form("manual_form", clear_on_submit=True):
            st.markdown(
                '<div style="font-size:.76rem;font-weight:700;color:#1C1A17;'
                'margin-bottom:10px;">자재 직접 입력</div>', unsafe_allow_html=True)
            m_name  = st.text_input("자재명 *", placeholder="예) LX 디아망 실크벽지")
            m_brand = st.text_input("브랜드", placeholder="예) LX하우시스")
            m_cat   = st.selectbox("카테고리", CAT_KEYS)
            m_spec  = st.text_input("규격", placeholder="예) 1,000mm × 10m")
            m_price = st.text_input("단가 (원)", placeholder="예) 55000")
            m_memo  = st.text_area("메모", height=68)
            if st.form_submit_button("＋ 자재 추가", use_container_width=True):
                if m_name.strip():
                    room["materials"].append({
                        "product_id": str(uuid.uuid4()),
                        "name":         m_name.strip(),
                        "brand":        m_brand.strip(),
                        "category":     m_cat,
                        "sub_category": "",
                        "price":        m_price.strip(),
                        "image":        "",
                        "qty":          1,
                        "spec":         m_spec.strip(),
                        "finish":       "",
                        "memo":         m_memo.strip(),
                    })
                    st.rerun()
                else:
                    st.warning("자재명을 입력하세요.")

# ════════════════════════════════════════════════════════════════════
# 오른쪽: 추가한 자재
# ════════════════════════════════════════════════════════════════════
with right_col:
    mats = room["materials"]
    room_total = sum(
        int(m.get("price", 0)) * m.get("qty", 1)
        for m in mats
        if str(m.get("price", "")).isdigit()
    )

    # 패널 헤더
    rh1, rh2 = st.columns([6, 4])
    with rh1:
        st.markdown(
            '<div style="font-size:.82rem;font-weight:700;color:#1C1A17;'
            'padding-top:2px;">추가한 자재</div>',
            unsafe_allow_html=True)
    with rh2:
        st.markdown(
            f'<div style="text-align:right;font-size:.80rem;font-weight:700;'
            f'color:#C9A87C;padding-top:2px;">{_fmt_price(room_total)}</div>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    if not mats:
        st.markdown(
            '<div style="text-align:center;padding:40px 16px;background:#FFFFFF;'
            'border:1.5px dashed #D4D0CA;border-radius:12px;color:#B0A898;font-size:.78rem;">'
            '자재를 검색하여<br>추가해보세요.</div>',
            unsafe_allow_html=True)
    else:
        # 카테고리 색상 매핑 (이미지 없을 때 스와치)
        cat_colors = {
            "벽": "#E8C4A0", "바닥": "#B8A898", "천장": "#D8D4CE",
            "타일": "#A8B8C8", "조명": "#F0D878", "문/도어": "#C8A870",
            "창호": "#98B8A0", "가구/목공": "#C8B080", "전기": "#E8D4A0",
            "설비": "#A8C8D8", "도장": "#D8C4B8", "필름": "#C8D4E8",
            "몰딩/걸레받이": "#D4C8B4",
        }

        for mi, mat in enumerate(mats):
            img_url  = mat.get("image", "")
            name     = mat.get("name", "")
            brand    = mat.get("brand", "")
            cat      = mat.get("category", "")
            price    = mat.get("price", "")
            qty      = mat.get("qty", 1)
            pid      = mat.get("product_id", str(mi))
            swatch   = cat_colors.get(cat, "#C8C0B0")
            is_fav   = any(f.get("product_id") == pid for f in st.session_state.favorites)

            with st.container():
                # 카드 상단: 이미지 + 정보
                ic, tc = st.columns([3, 7])
                with ic:
                    if img_url:
                        try:
                            st.image(img_url, use_container_width=True)
                        except:
                            st.markdown(
                                f'<div style="background:{swatch};border-radius:8px;'
                                f'aspect-ratio:1;min-height:60px;"></div>',
                                unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'<div style="background:{swatch};border-radius:8px;'
                            f'aspect-ratio:1;min-height:60px;"></div>',
                            unsafe_allow_html=True)
                with tc:
                    st.markdown(
                        f'<div style="font-size:.78rem;font-weight:700;color:#1C1A17;'
                        f'line-height:1.35;">{name}</div>'
                        f'<div style="font-size:.72rem;font-weight:700;color:#C9A87C;'
                        f'margin-top:3px;">{_fmt_price(price)}</div>'
                        f'<div style="font-size:.66rem;color:#8A8480;margin-top:2px;">'
                        f'{brand}{"  ·  " + cat if cat else ""}</div>',
                        unsafe_allow_html=True)

                # 버튼 행: − qty + | ☆ | ×
                b1, b2, b3, b4, b5 = st.columns([1, 1.2, 1, 1, 1])
                with b1:
                    if st.button("−", key=f"qm_{pid}_{mi}", use_container_width=True):
                        if mat["qty"] > 1:
                            mat["qty"] -= 1
                        st.rerun()
                with b2:
                    st.markdown(
                        f'<div style="text-align:center;padding:6px 0;font-size:.82rem;'
                        f'font-weight:700;color:#1C1A17;">{qty}</div>',
                        unsafe_allow_html=True)
                with b3:
                    if st.button("＋", key=f"qp_{pid}_{mi}", use_container_width=True):
                        mat["qty"] = mat.get("qty", 1) + 1
                        st.rerun()
                with b4:
                    fav_lbl = "★" if is_fav else "☆"
                    if st.button(fav_lbl, key=f"fav_{pid}_{mi}", use_container_width=True):
                        if is_fav:
                            st.session_state.favorites = [
                                f for f in st.session_state.favorites
                                if f.get("product_id") != pid]
                        else:
                            st.session_state.favorites.append(_copy.deepcopy(mat))
                        st.rerun()
                with b5:
                    if st.button("×", key=f"del_{pid}_{mi}", use_container_width=True):
                        room["materials"].pop(mi)
                        st.rerun()

                # 상세 정보 (접기)
                with st.expander("상세 정보"):
                    mat["spec"]   = st.text_input("규격", mat.get("spec", ""),
                                                  key=f"spec_{pid}_{mi}")
                    mat["finish"] = st.text_input("마감", mat.get("finish", ""),
                                                  key=f"fin_{pid}_{mi}")
                    mat["memo"]   = st.text_area("메모", mat.get("memo", ""),
                                                 key=f"memo_{pid}_{mi}", height=60)

            st.markdown(
                '<div style="border-bottom:1.5px solid #EDE9E3;margin:10px 0;"></div>',
                unsafe_allow_html=True)
