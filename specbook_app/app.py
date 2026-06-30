"""
인테리어 스펙북 생성기 v8
- 세션스테이트 직접 참조로 추가 버튼 신뢰성 확보
- 즐겨찾기 검색결과에 추가
- 웹 표준 UI/UX, 명확한 버튼 색상 대비
"""
import re, uuid, json, copy as _copy
import streamlit as st
from datetime import datetime
from brands import BRAND_CATALOG, CATEGORY_META
from naver_shopping import search_products
from pptx_generator import generate_pptx

st.set_page_config(
    page_title="INTERIOR SPEC BOOK",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

CAT_KEYS = list(BRAND_CATALOG.keys())

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #F5F5F5 !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { display: none !important; }

/* ══ 사이드바 ══════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: #1E1E1E !important;
  min-width: 230px !important; max-width: 255px !important;
}
[data-testid="stSidebarContent"] { padding: 16px 14px 28px !important; }

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label { color: #BDBDBD !important; }

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
  background: #2C2C2C !important; border: 1px solid #424242 !important;
  color: #F5F5F5 !important; border-radius: 6px !important; font-size: .80rem !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
  border-color: #C9A87C !important;
  box-shadow: 0 0 0 2px rgba(201,168,124,.20) !important;
}

/* 사이드바 버튼 기본 */
[data-testid="stSidebar"] .stButton > button {
  width: 100% !important; background: #2C2C2C !important;
  color: #EEEEEE !important; border: 1px solid #424242 !important;
  border-radius: 7px !important; font-size: .78rem !important;
  font-weight: 500 !important; padding: 8px 12px !important;
  margin-bottom: 4px !important; transition: all .15s !important;
  text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: #383838 !important; border-color: #C9A87C !important;
  color: #FFFFFF !important;
}
/* 사이드바 primary (현재 공간, PPT) */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: #C9A87C !important; color: #1E1E1E !important;
  border-color: #C9A87C !important; font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
  background: #B8976B !important;
}
/* 사이드바 download */
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: #2C2C2C !important; color: #C9A87C !important;
  border: 1px solid #424242 !important; border-radius: 7px !important;
  width: 100% !important; font-size: .78rem !important; font-weight: 600 !important;
  padding: 8px 12px !important; margin-bottom: 4px !important;
}
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: #383838 !important; border-color: #C9A87C !important;
}
[data-testid="stSidebar"] hr { border-color: #333 !important; margin: 12px 0 !important; }

/* expander 사이드바 */
[data-testid="stSidebar"] details {
  background: #252525 !important; border: 1px solid #333 !important;
  border-radius: 8px !important; margin-bottom: 6px !important;
}
[data-testid="stSidebar"] summary { color: #EEEEEE !important; font-size: .80rem !important; }

/* file uploader 사이드바 */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
  background: #252525 !important; border: 1px dashed #424242 !important;
  border-radius: 8px !important; padding: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
  font-size: .72rem !important; color: #9E9E9E !important;
}

/* ══ 메인 버튼 ═══════════════════════════════════════════════ */
/* 기본 (선택 안 된 카테고리/브랜드) */
.stButton > button {
  border-radius: 6px !important; font-size: .78rem !important;
  font-weight: 500 !important; padding: 7px 14px !important;
  background: #FFFFFF !important; color: #424242 !important;
  border: 1.5px solid #BDBDBD !important;
  transition: all .15s !important; white-space: nowrap !important;
}
.stButton > button:hover {
  background: #FFF8F0 !important; border-color: #C9A87C !important;
  color: #1E1E1E !important;
}
/* primary — 선택된 카테고리/브랜드/제품군 */
div[data-testid="stButton"] > button[kind="primary"] {
  background: #1E1E1E !important; color: #C9A87C !important;
  border-color: #1E1E1E !important; font-weight: 700 !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background: #333 !important;
}

/* ══ 특수 버튼 클래스 (HTML 인라인) ═══════════════════════════ */
.btn-add {
  display: inline-block; padding: 6px 14px; border-radius: 6px;
  background: #2563EB; color: #FFFFFF !important; font-size: .75rem;
  font-weight: 700; border: none; cursor: pointer; text-decoration: none;
}
.btn-fav-on  { color: #F59E0B !important; font-size: 1rem; }
.btn-fav-off { color: #9E9E9E !important; font-size: 1rem; }

/* ══ 입력창 메인 ══════════════════════════════════════════════ */
.stTextInput input, .stTextArea textarea {
  background: #FFFFFF !important; border: 1.5px solid #BDBDBD !important;
  border-radius: 6px !important; color: #212121 !important; font-size: .82rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #2563EB !important; box-shadow: 0 0 0 2px rgba(37,99,235,.12) !important;
}
[data-testid="stTextInputRootElement"] input {
  background: #FFFFFF !important; color: #212121 !important;
}
.stSelectbox [data-baseweb="select"] > div {
  background: #FFFFFF !important; border: 1.5px solid #BDBDBD !important;
  border-radius: 6px !important; color: #212121 !important;
}

/* ══ 서브탭 ════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: #E0E0E0; padding: 4px; border-radius: 8px; gap: 3px;
  border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 6px; font-size: .76rem; font-weight: 600;
  padding: 7px 18px; color: #616161 !important;
  background: transparent !important; border: none !important;
}
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important; color: #212121 !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.10) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 14px !important; }

/* ══ 폼 ═══════════════════════════════════════════════════════ */
[data-testid="stForm"] {
  background: #FFFFFF; border: 1.5px solid #E0E0E0;
  border-radius: 10px; padding: 16px;
}

/* ══ expander 메인 ════════════════════════════════════════════ */
details { background: #FAFAFA !important; border: 1px solid #E0E0E0 !important; border-radius: 8px !important; }

/* ══ 자재 카드 구분선 ═════════════════════════════════════════ */
.mat-divider { border: none; border-top: 1px solid #EEEEEE; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def _new_room(name="거실"):
    return {
        "id": str(uuid.uuid4()), "name": name,
        "en_name": "Living Room", "materials": [], "modeling_images": []
    }

def _init():
    if "project" not in st.session_state:
        st.session_state.project = {
            "name": "프로젝트명", "client": "", "designer": "",
            "date": datetime.today().strftime("%Y-%m-%d"), "address": "",
        }
    if "rooms" not in st.session_state:
        st.session_state.rooms = [_new_room("거실")]
    if "current_room_idx" not in st.session_state:
        st.session_state.current_room_idx = 0
    if "logo_bytes" not in st.session_state:
        st.session_state.logo_bytes = None
    if "favorites" not in st.session_state:
        st.session_state.favorites = []
    for k, v in [
        ("sel_cat", None), ("sel_brand", None), ("sel_sub", None),
        ("search_results", []), ("search_done", False), ("search_keyword", ""),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── 항상 session_state에서 직접 읽기 ────────────────────────────────────────
def _cur_idx():
    idx = st.session_state.current_room_idx
    return min(idx, len(st.session_state.rooms) - 1)

def _cur_room():
    return st.session_state.rooms[_cur_idx()]

def _fmt_price(v):
    try: return f"{int(v):,}원"
    except: return str(v) if v else "-"

def _total_price():
    total = 0
    for r in st.session_state.rooms:
        for m in r["materials"]:
            try: total += int(m.get("price", 0)) * m.get("qty", 1)
            except: pass
    return total

def _total_items():
    return sum(len(r["materials"]) for r in st.session_state.rooms)

def _reset_search():
    st.session_state.sel_cat = None
    st.session_state.sel_brand = None
    st.session_state.sel_sub = None
    st.session_state.search_results = []
    st.session_state.search_done = False
    st.session_state.search_keyword = ""

def _add_material(item_dict):
    """세션스테이트 직접 접근으로 자재 추가"""
    idx = _cur_idx()
    pid = item_dict["product_id"]
    mats = st.session_state.rooms[idx]["materials"]
    existing = next((m for m in mats if m.get("product_id") == pid), None)
    if existing:
        existing["qty"] = existing.get("qty", 1) + 1
    else:
        mats.append(item_dict)

def _toggle_favorite(mat):
    pid = mat.get("product_id")
    favs = st.session_state.favorites
    if any(f.get("product_id") == pid for f in favs):
        st.session_state.favorites = [f for f in favs if f.get("product_id") != pid]
    else:
        st.session_state.favorites.append(_copy.deepcopy(mat))

# ── 사이드바 ──────────────────────────────────────────────────────────────────
p = st.session_state.project

with st.sidebar:
    with st.expander("📋 프로젝트 정보"):
        p["name"]     = st.text_input("프로젝트명", p["name"], key="p_name")
        p["client"]   = st.text_input("의뢰인",    p.get("client",""),   key="p_client")
        p["designer"] = st.text_input("디자이너",  p.get("designer",""), key="p_designer")
        p["date"]     = st.text_input("날짜",      p.get("date",""),     key="p_date")
        p["address"]  = st.text_input("현장주소",  p.get("address",""),  key="p_addr")

    with st.expander("🖼 표지 로고"):
        logo_file = st.file_uploader("로고 이미지", type=["png","jpg","jpeg"],
                                     key="logo_up", label_visibility="collapsed")
        if logo_file:
            st.session_state.logo_bytes = logo_file.read()
        if st.session_state.logo_bytes:
            st.image(st.session_state.logo_bytes, use_container_width=True)

    # SPACES
    st.markdown(
        '<p style="font-size:.62rem;font-weight:700;letter-spacing:.10em;'
        'color:#616161!important;text-transform:uppercase;margin:14px 0 7px 2px;">SPACES</p>',
        unsafe_allow_html=True)

    for i, r in enumerate(st.session_state.rooms):
        active = (i == _cur_idx())
        ca, cb = st.columns([76, 24])
        with ca:
            label = f"▶  {r['name']}" if active else f"   {r['name']}"
            if st.button(label, key=f"room_sel_{i}",
                         type="primary" if active else "secondary",
                         use_container_width=True):
                if not active:
                    st.session_state.current_room_idx = i
                    _reset_search()
                    st.rerun()
        with cb:
            if st.button("✕", key=f"room_del_{i}", use_container_width=True):
                if len(st.session_state.rooms) > 1:
                    st.session_state.rooms.pop(i)
                    st.session_state.current_room_idx = max(0, i - 1)
                    _reset_search()
                    st.rerun()

    if st.button("＋  공간 추가", use_container_width=True):
        st.session_state.rooms.append(_new_room(f"공간 {len(st.session_state.rooms)+1}"))
        st.session_state.current_room_idx = len(st.session_state.rooms) - 1
        _reset_search()
        st.rerun()

    st.markdown("---")

    # FILE
    st.markdown(
        '<p style="font-size:.62rem;font-weight:700;letter-spacing:.10em;'
        'color:#616161!important;text-transform:uppercase;margin:0 0 7px 2px;">FILE</p>',
        unsafe_allow_html=True)

    json_data = json.dumps(
        {"project": p, "rooms": st.session_state.rooms},
        ensure_ascii=False, indent=2)
    st.download_button("💾  JSON 저장", data=json_data,
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

    # EXPORT
    st.markdown(
        '<p style="font-size:.62rem;font-weight:700;letter-spacing:.10em;'
        'color:#616161!important;text-transform:uppercase;margin:0 0 7px 2px;">EXPORT</p>',
        unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:.72rem;color:#9E9E9E!important;margin:0 0 10px 2px;">'
        f'공간 {len(st.session_state.rooms)}개 &nbsp;·&nbsp; '
        f'자재 {_total_items()}개 &nbsp;·&nbsp; {_fmt_price(_total_price())}</p>',
        unsafe_allow_html=True)

    if st.button("✦  PPT 스펙북 생성", type="primary",
                 use_container_width=True, key="ppt_gen"):
        with st.spinner("PPT 생성 중..."):
            try:
                buf = generate_pptx(p, st.session_state.rooms,
                                    logo_bytes=st.session_state.logo_bytes)
                st.download_button(
                    "⬇  다운로드", data=buf,
                    file_name=f"specbook_{p['name']}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True, key="ppt_dl")
            except Exception as e:
                st.error(f"PPT 오류: {e}")

# ── 메인 ─────────────────────────────────────────────────────────────────────
room = _cur_room()

# 헤더
st.markdown(
    f'<div style="background:#1E1E1E;color:#C9A87C;padding:14px 22px;'
    f'font-size:.92rem;font-weight:700;letter-spacing:.05em;border-radius:8px;'
    f'margin-bottom:18px;">INTERIOR SPEC BOOK &nbsp;·&nbsp; {room["name"]}</div>',
    unsafe_allow_html=True)

# 공간명 + 자재 수
nm_col, cnt_col = st.columns([8, 2])
with nm_col:
    new_name = st.text_input("공간명", room["name"],
                             label_visibility="collapsed",
                             key=f"rname_{room['id']}",
                             placeholder="공간명")
    if new_name != room["name"]:
        st.session_state.rooms[_cur_idx()]["name"] = new_name
        st.rerun()
with cnt_col:
    st.markdown(
        f'<div style="text-align:right;padding-top:10px;font-size:.78rem;color:#9E9E9E;">'
        f'{len(room["materials"])}개 자재</div>',
        unsafe_allow_html=True)

st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

# ── 2열 레이아웃 ──────────────────────────────────────────────────────────────
left_col, right_col = st.columns([56, 44], gap="large")

# ════════════════════════════════════════════════════════════════════
# 왼쪽: 검색 영역
# ════════════════════════════════════════════════════════════════════
with left_col:
    s_cat   = st.session_state.sel_cat
    s_brand = st.session_state.sel_brand
    s_sub   = st.session_state.sel_sub

    # 스텝 진행바
    step_now = 1
    if s_cat:   step_now = 2
    if s_brand: step_now = 3
    if s_sub:   step_now = 4

    STEPS = [("① 카테고리", 1), ("② 업체", 2), ("③ 제품군", 3), ("④ 검색결과", 4)]
    step_html = ""
    for label, n in STEPS:
        if n < step_now:
            s = "background:#E8DDD0;color:#8A6840;border:1.5px solid #D4BC96;"
        elif n == step_now:
            s = "background:#1E1E1E;color:#C9A87C;border:1.5px solid #1E1E1E;font-weight:700;"
        else:
            s = "background:#F5F5F5;color:#BDBDBD;border:1.5px solid #E0E0E0;"
        step_html += (
            f'<div style="{s}flex:1;text-align:center;padding:8px 4px;'
            f'border-radius:6px;font-size:.72rem;">{label}</div>')
    st.markdown(
        f'<div style="display:flex;gap:6px;margin-bottom:16px;">{step_html}</div>',
        unsafe_allow_html=True)

    # 서브탭
    fav_count = len(st.session_state.favorites)
    tab_search, tab_fav, tab_manual = st.tabs([
        "🔍 카테고리 검색",
        f"⭐ 즐겨찾기 ({fav_count})",
        "✏ 직접 입력",
    ])

    # ── 카테고리 검색 ─────────────────────────────────────────────
    with tab_search:

        # ① 카테고리
        st.markdown(
            '<p style="font-size:.68rem;font-weight:700;color:#9E9E9E;'
            'letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px;">① 카테고리 선택</p>',
            unsafe_allow_html=True)
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
            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<p style="font-size:.68rem;font-weight:700;color:#9E9E9E;'
                'letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px;">② 업체 / 브랜드</p>',
                unsafe_allow_html=True)
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
        brand_entry = None
        if s_brand and s_cat in BRAND_CATALOG:
            brand_entry = next(
                (b for b in BRAND_CATALOG[s_cat] if b["name"] == s_brand), None)
        if brand_entry:
            subs = brand_entry["groups"]
            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<p style="font-size:.68rem;font-weight:700;color:#9E9E9E;'
                'letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px;">③ 제품군</p>',
                unsafe_allow_html=True)
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
            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
            st.markdown(
                '<p style="font-size:.68rem;font-weight:700;color:#9E9E9E;'
                'letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px;">④ 검색</p>',
                unsafe_allow_html=True)
            kc, bc = st.columns([7, 3])
            with kc:
                kw = st.text_input("kw", value=st.session_state.search_keyword,
                                   label_visibility="collapsed",
                                   key="kw_input",
                                   placeholder="검색어 입력 후 검색 버튼 클릭")
                st.session_state.search_keyword = kw
            with bc:
                do_search = st.button("검색", key="do_search", use_container_width=True)

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

            if st.session_state.search_done:
                results = st.session_state.search_results
                if not results:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.markdown(
                        f'<p style="font-size:.70rem;color:#9E9E9E;margin:6px 0 12px;">'
                        f'{len(results)}개 결과</p>', unsafe_allow_html=True)

                    for item in results:
                        img_url  = item.get("image", "")
                        name     = re.sub(r"<[^>]+>", "", item.get("title", ""))
                        brand_nm = item.get("brand", item.get("mallName", ""))
                        price    = item.get("lprice", "")
                        pid      = str(item.get("productId", item.get("id", ""))) or str(uuid.uuid4())

                        mat_dict = {
                            "product_id":   pid,
                            "name":         name,
                            "brand":        brand_nm,
                            "category":     s_cat or "",
                            "sub_category": s_sub or "",
                            "price":        price,
                            "image":        img_url,
                            "qty":          1,
                            "spec":         "",
                            "finish":       "",
                            "memo":         "",
                        }
                        is_fav = any(
                            f.get("product_id") == pid
                            for f in st.session_state.favorites)
                        is_added = any(
                            m.get("product_id") == pid
                            for m in _cur_room()["materials"])

                        # 결과 행
                        ic, tc, ac = st.columns([2, 6, 3])
                        with ic:
                            if img_url:
                                try: st.image(img_url, use_container_width=True)
                                except: st.markdown("🖼")
                            else:
                                st.markdown(
                                    '<div style="width:100%;aspect-ratio:1;'
                                    'background:#E0E0E0;border-radius:6px;'
                                    'display:flex;align-items:center;justify-content:center;">'
                                    '<span style="font-size:1.4rem;">🖼</span></div>',
                                    unsafe_allow_html=True)
                        with tc:
                            st.markdown(
                                f'<div style="font-size:.78rem;font-weight:600;'
                                f'color:#212121;line-height:1.4;">{name}</div>'
                                f'<div style="font-size:.68rem;color:#9E9E9E;margin-top:3px;">'
                                f'{brand_nm}{"  ·  " + (s_cat or "") if s_cat else ""}</div>'
                                f'<div style="font-size:.80rem;font-weight:700;'
                                f'color:#E65100;margin-top:4px;">{_fmt_price(price)}</div>',
                                unsafe_allow_html=True)
                        with ac:
                            # 추가 버튼 — 파란색, 명확히 구분
                            add_label = "✓ 추가됨" if is_added else "＋ 추가"
                            if st.button(add_label,
                                         key=f"add_{pid}",
                                         use_container_width=True):
                                _add_material(mat_dict)
                                st.rerun()
                            # 즐겨찾기 버튼 — 별 아이콘, 금색
                            fav_label = "★ 저장됨" if is_fav else "☆ 즐겨찾기"
                            if st.button(fav_label,
                                         key=f"fav_res_{pid}",
                                         use_container_width=True):
                                _toggle_favorite(mat_dict)
                                st.rerun()

                        st.markdown(
                            '<hr style="border:none;border-top:1px solid #EEEEEE;margin:8px 0;">',
                            unsafe_allow_html=True)

    # ── 즐겨찾기 탭 ───────────────────────────────────────────────
    with tab_fav:
        favs = st.session_state.favorites
        if not favs:
            st.markdown(
                '<div style="text-align:center;padding:32px 16px;color:#BDBDBD;'
                'font-size:.82rem;">검색 결과에서 ☆ 즐겨찾기 버튼으로 추가하세요.</div>',
                unsafe_allow_html=True)
        else:
            for fi, fav in enumerate(favs):
                pid_f = fav.get("product_id", "")
                ic, tc, ac = st.columns([2, 6, 3])
                with ic:
                    if fav.get("image"):
                        try: st.image(fav["image"], use_container_width=True)
                        except: st.markdown("🖼")
                    else:
                        st.markdown("🖼")
                with tc:
                    st.markdown(
                        f'<div style="font-size:.78rem;font-weight:600;color:#212121;">'
                        f'{fav["name"]}</div>'
                        f'<div style="font-size:.68rem;color:#9E9E9E;margin-top:3px;">'
                        f'{fav.get("brand","")}{" · " + fav.get("category","") if fav.get("category") else ""}</div>'
                        f'<div style="font-size:.80rem;font-weight:700;color:#E65100;margin-top:4px;">'
                        f'{_fmt_price(fav.get("price",""))}</div>',
                        unsafe_allow_html=True)
                with ac:
                    if st.button("＋ 추가", key=f"fav_add_{fi}", use_container_width=True):
                        _add_material(_copy.deepcopy(fav))
                        st.rerun()
                    if st.button("★ 삭제", key=f"fav_del_{fi}", use_container_width=True):
                        st.session_state.favorites.pop(fi)
                        st.rerun()
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #EEEEEE;margin:8px 0;">',
                    unsafe_allow_html=True)

    # ── 직접 입력 탭 ──────────────────────────────────────────────
    with tab_manual:
        with st.form("manual_form", clear_on_submit=True):
            m_name  = st.text_input("자재명 *", placeholder="예) LX 디아망 크림화이트 실크벽지")
            mc1, mc2 = st.columns(2)
            with mc1:
                m_brand = st.text_input("브랜드", placeholder="예) LX하우시스")
            with mc2:
                m_cat = st.selectbox("카테고리", CAT_KEYS)
            mc3, mc4 = st.columns(2)
            with mc3:
                m_spec  = st.text_input("규격", placeholder="예) 1,000mm × 10m")
            with mc4:
                m_price = st.text_input("단가 (원)", placeholder="예) 55000")
            m_memo = st.text_area("메모", height=64, placeholder="기타 참고 사항")
            if st.form_submit_button("＋  자재 추가", use_container_width=True):
                if m_name.strip():
                    _add_material({
                        "product_id":   str(uuid.uuid4()),
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
                    st.warning("자재명을 입력해주세요.")

# ════════════════════════════════════════════════════════════════════
# 오른쪽: 추가한 자재 패널
# ════════════════════════════════════════════════════════════════════
with right_col:
    mats = _cur_room()["materials"]  # 항상 최신 참조
    room_total = sum(
        int(m.get("price", 0)) * m.get("qty", 1)
        for m in mats if str(m.get("price", "")).isdigit()
    )

    # 패널 헤더
    ph1, ph2 = st.columns([6, 4])
    with ph1:
        st.markdown(
            '<p style="font-size:.86rem;font-weight:700;color:#212121;margin:2px 0 0;">추가한 자재</p>',
            unsafe_allow_html=True)
    with ph2:
        st.markdown(
            f'<p style="text-align:right;font-size:.84rem;font-weight:700;'
            f'color:#E65100;margin:2px 0 0;">{_fmt_price(room_total)}</p>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    if not mats:
        st.markdown(
            '<div style="text-align:center;padding:48px 20px;background:#FFFFFF;'
            'border:1.5px dashed #BDBDBD;border-radius:10px;">'
            '<div style="font-size:1.8rem;margin-bottom:10px;">📦</div>'
            '<div style="font-size:.82rem;color:#9E9E9E;">검색 후 자재를 추가하세요</div>'
            '</div>', unsafe_allow_html=True)
    else:
        cat_swatches = {
            "벽": "#F3E5D8", "바닥": "#E8E0D8", "천장": "#ECEBE8",
            "타일": "#D8E8F0", "조명": "#FFF8DC", "문/도어": "#EDE0C8",
            "창호": "#D8EDE0", "가구/목공": "#EDE8D8", "전기": "#E8F0D8",
            "설비": "#D8EDF0", "도장": "#F0E8E0", "필름": "#E0E8F0",
            "몰딩/걸레받이": "#EDE8DC",
        }

        for mi, mat in enumerate(mats):
            idx      = _cur_idx()
            img_url  = mat.get("image", "")
            name     = mat.get("name", "")
            brand_nm = mat.get("brand", "")
            cat      = mat.get("category", "")
            price    = mat.get("price", "")
            qty      = mat.get("qty", 1)
            pid      = mat.get("product_id", str(mi))
            swatch   = cat_swatches.get(cat, "#F0F0F0")
            is_fav   = any(f.get("product_id") == pid for f in st.session_state.favorites)

            # 카드
            with st.container():
                img_c, info_c = st.columns([3, 7])
                with img_c:
                    if img_url:
                        try: st.image(img_url, use_container_width=True)
                        except:
                            st.markdown(
                                f'<div style="background:{swatch};border-radius:6px;'
                                f'aspect-ratio:1;"></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'<div style="background:{swatch};border-radius:6px;'
                            f'aspect-ratio:1;min-height:56px;"></div>',
                            unsafe_allow_html=True)
                with info_c:
                    st.markdown(
                        f'<div style="font-size:.78rem;font-weight:700;color:#212121;'
                        f'line-height:1.35;">{name}</div>'
                        f'<div style="font-size:.72rem;font-weight:700;color:#E65100;'
                        f'margin-top:3px;">{_fmt_price(price)}</div>'
                        f'<div style="font-size:.66rem;color:#9E9E9E;margin-top:2px;">'
                        f'{brand_nm}{"  ·  " + cat if cat else ""}</div>',
                        unsafe_allow_html=True)

                # 수량 조절 + 즐겨찾기 + 삭제
                b_minus, b_qty, b_plus, b_fav, b_del = st.columns([1.2, 1, 1.2, 1.5, 1.2])
                with b_minus:
                    if st.button("−", key=f"qm_{pid}_{mi}", use_container_width=True):
                        if st.session_state.rooms[idx]["materials"][mi]["qty"] > 1:
                            st.session_state.rooms[idx]["materials"][mi]["qty"] -= 1
                        st.rerun()
                with b_qty:
                    st.markdown(
                        f'<div style="text-align:center;padding:7px 0;font-size:.84rem;'
                        f'font-weight:700;color:#212121;">{qty}</div>',
                        unsafe_allow_html=True)
                with b_plus:
                    if st.button("＋", key=f"qp_{pid}_{mi}", use_container_width=True):
                        st.session_state.rooms[idx]["materials"][mi]["qty"] += 1
                        st.rerun()
                with b_fav:
                    fav_lbl = "★" if is_fav else "☆"
                    if st.button(fav_lbl, key=f"fav_mat_{pid}_{mi}", use_container_width=True):
                        _toggle_favorite(mat)
                        st.rerun()
                with b_del:
                    if st.button("삭제", key=f"del_{pid}_{mi}", use_container_width=True):
                        st.session_state.rooms[idx]["materials"].pop(mi)
                        st.rerun()

                # 상세 정보
                with st.expander("상세 정보"):
                    new_spec = st.text_input(
                        "규격", mat.get("spec", ""), key=f"spec_{pid}_{mi}")
                    new_fin  = st.text_input(
                        "마감", mat.get("finish", ""), key=f"fin_{pid}_{mi}")
                    new_memo = st.text_area(
                        "메모", mat.get("memo", ""), key=f"memo_{pid}_{mi}", height=60)
                    # 변경 즉시 저장
                    st.session_state.rooms[idx]["materials"][mi]["spec"]   = new_spec
                    st.session_state.rooms[idx]["materials"][mi]["finish"] = new_fin
                    st.session_state.rooms[idx]["materials"][mi]["memo"]   = new_memo

            st.markdown(
                '<hr style="border:none;border-top:1px solid #EEEEEE;margin:10px 0;">',
                unsafe_allow_html=True)
