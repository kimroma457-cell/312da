"""
인테리어 스펙북 v10 — Clean / Spacious Design
"""
import re, uuid, json, copy as _copy, base64
import streamlit as st
from datetime import datetime, date
from brands import BRAND_CATALOG, CATEGORY_META
from naver_shopping import search_products
from pptx_generator import generate_pptx

st.set_page_config(
    page_title="Interior Spec Book",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CAT_KEYS = list(BRAND_CATALOG.keys())

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=Inter:wght@300;400;500;600;700;900&family=DM+Serif+Display:ital@0;1&display=swap');

/* ══ Reset & Base ══ */
*, *::before, *::after { box-sizing: border-box; margin: 0; }
html, body, [class*="css"] {
  font-family: 'Noto Sans KR', 'Inter', sans-serif;
}
#MainMenu, footer, [data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }

/* ══ App Background ══ */
.stApp {
  background: #F7F4EF !important;
  min-height: 100vh;
  position: relative;
}

/* ══ 배경 장식 — 큰 원형 그레인 ══ */
.stApp::before {
  content: '';
  position: fixed;
  top: -30vw; right: -20vw;
  width: 70vw; height: 70vw;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(201,168,124,.13) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}
.stApp::after {
  content: '';
  position: fixed;
  bottom: -25vw; left: -15vw;
  width: 55vw; height: 55vw;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(232,201,122,.09) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}

/* ══ 버튼 ══ */
.stButton > button {
  font-family: 'Noto Sans KR', sans-serif !important;
  border-radius: 12px !important;
  font-size: .80rem !important;
  font-weight: 600 !important;
  padding: 10px 20px !important;
  background: #FFFFFF !important;
  color: #374151 !important;
  border: 1.5px solid #E8E3DC !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.05), 0 1px 2px rgba(0,0,0,.04) !important;
  transition: all .20s cubic-bezier(.25,.8,.25,1) !important;
  white-space: nowrap !important;
  letter-spacing: .01em !important;
}
.stButton > button:hover {
  background: #FDFBF8 !important;
  border-color: #C9A87C !important;
  color: #1C1C1E !important;
  box-shadow: 0 4px 16px rgba(201,168,124,.22) !important;
  transform: translateY(-1px) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
  background: #1C1C1E !important;
  color: #E8C97A !important;
  border-color: transparent !important;
  box-shadow: 0 4px 20px rgba(28,28,30,.30) !important;
  font-weight: 700 !important;
  letter-spacing: .02em !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background: #2C2C2E !important;
  box-shadow: 0 8px 28px rgba(28,28,30,.35) !important;
  transform: translateY(-2px) !important;
}

/* ══ 입력창 ══ */
.stTextInput input, .stTextArea textarea, .stDateInput input {
  font-family: 'Noto Sans KR', sans-serif !important;
  background: #FFFFFF !important;
  border: 1.5px solid #E8E3DC !important;
  border-radius: 14px !important;
  color: #1C1C1E !important;
  font-size: .88rem !important;
  padding: 14px 18px !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.04) !important;
  transition: border-color .20s, box-shadow .20s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #C9A87C !important;
  box-shadow: 0 0 0 3px rgba(201,168,124,.14) !important;
  outline: none !important;
}
[data-testid="stTextInputRootElement"] input {
  background: #FFFFFF !important; color: #1C1C1E !important;
}

/* ══ 탭 ══ */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(28,28,30,.06);
  padding: 4px; border-radius: 14px; gap: 3px; border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px; font-size: .76rem; font-weight: 600;
  padding: 8px 22px; color: #9CA3AF !important;
  background: transparent !important; border: none !important;
  transition: all .20s !important; letter-spacing: .01em !important;
}
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important; color: #1C1C1E !important;
  box-shadow: 0 2px 10px rgba(0,0,0,.09) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 20px !important; }

/* ══ 폼 ══ */
[data-testid="stForm"] {
  background: #FFFFFF;
  border: 1.5px solid #EDE9E3;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 2px 16px rgba(0,0,0,.05);
}

/* ══ selectbox ══ */
[data-baseweb="select"] > div {
  background: #FFFFFF !important; border: 1.5px solid #E8E3DC !important;
  border-radius: 14px !important; color: #1C1C1E !important;
}

/* ══ download 버튼 ══ */
[data-testid="stDownloadButton"] > button {
  font-family: 'Noto Sans KR', sans-serif !important;
  border-radius: 12px !important; font-size: .78rem !important;
  font-weight: 600 !important; padding: 9px 16px !important;
  background: #FFFFFF !important; color: #374151 !important;
  border: 1.5px solid #E8E3DC !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.05) !important;
}

/* ══ expander ══ */
details {
  background: #FFFFFF !important;
  border: 1.5px solid #EDE9E3 !important;
  border-radius: 14px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.04) !important;
}
details summary { font-size: .78rem !important; color: #9CA3AF !important; font-weight: 500 !important; }

/* ══ 카드 컴포넌트 ══ */
.spec-card {
  background: #FFFFFF;
  border-radius: 18px;
  border: 1.5px solid #EDE9E3;
  box-shadow: 0 2px 14px rgba(0,0,0,.06);
  padding: 20px;
  margin-bottom: 12px;
}
.spec-card:hover { box-shadow: 0 8px 28px rgba(0,0,0,.10); }

/* ══ 스텝 검색 인디케이터 ══ */
.step-pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 13px; border-radius: 99px; font-size: .70rem; font-weight: 700;
  letter-spacing: .02em;
}
.step-done  { background: rgba(201,168,124,.15); color: #92510E; }
.step-now   { background: #1C1C1E; color: #E8C97A; }
.step-next  { background: #F3F4F6; color: #C9D1DC; }

/* ══ 가격·섹션 레이블 ══ */
.price-text { color: #B45309; font-weight: 700; }
.sec-label {
  font-size: .62rem; font-weight: 700; color: #B0B7C3;
  letter-spacing: .12em; text-transform: uppercase; margin: 0 0 10px;
}

/* ══ 프로그레스바 ══ */
[data-testid="stProgressBar"] { height: 3px !important; border-radius: 99px !important; background: rgba(0,0,0,.06) !important; }
[data-testid="stProgressBar"] > div {
  background: linear-gradient(90deg, #C9A87C 0%, #E8C97A 100%) !important;
  border-radius: 99px !important;
}

/* ══ Spinner ══ */
.stSpinner > div { border-top-color: #C9A87C !important; }

/* ══ File uploader ══ */
[data-testid="stFileUploader"] {
  background: #FDFBF8 !important;
  border: 1.5px dashed #DDD7CE !important;
  border-radius: 14px !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: #C9A87C !important;
}

/* ══ Alert ══ */
[data-testid="stAlert"] { border-radius: 14px !important; }

/* ══ 위자드 전용 — 대형 스텝 번호 데코 ══ */
.wiz-step-num {
  font-family: 'Inter', sans-serif;
  font-size: 7rem;
  font-weight: 900;
  color: rgba(201,168,124,.10);
  line-height: 1;
  letter-spacing: -.04em;
  position: absolute;
  top: -18px; right: 20px;
  pointer-events: none;
  user-select: none;
}

/* ══ 골드 밑줄 강조 ══ */
.gold-underline {
  display: inline-block;
  position: relative;
}
.gold-underline::after {
  content: '';
  position: absolute;
  bottom: -3px; left: 0;
  width: 100%; height: 2px;
  background: linear-gradient(90deg, #C9A87C, #E8C97A);
  border-radius: 2px;
}

/* ══ 위자드 카드 ══ */
.wiz-card {
  background: #FFFFFF;
  border-radius: 28px;
  padding: 48px 44px 40px;
  box-shadow: 0 12px 60px rgba(0,0,0,.09), 0 2px 8px rgba(0,0,0,.05);
  border: 1px solid rgba(255,255,255,.9);
  position: relative;
  overflow: hidden;
}
.wiz-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #C9A87C 0%, #E8C97A 50%, #C9A87C 100%);
}

/* ══ 닷 스텝 인디케이터 ══ */
.dot-steps {
  display: flex; align-items: center; gap: 6px; margin-bottom: 36px;
}
.dot-done {
  width: 24px; height: 5px; border-radius: 99px;
  background: linear-gradient(90deg, #C9A87C, #E8C97A);
}
.dot-now {
  width: 32px; height: 5px; border-radius: 99px;
  background: #1C1C1E;
}
.dot-next {
  width: 8px; height: 5px; border-radius: 99px;
  background: #E8E3DC;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION INIT
# ══════════════════════════════════════════════════════════════════════════════
def _new_room(name="거실"):
    return {"id": str(uuid.uuid4()), "name": name, "materials": [],
            "modeling_views": [{}, {}, {}, {}]}

def _init():
    ss = st.session_state
    if "page"       not in ss: ss.page       = "setup"
    if "setup_step" not in ss: ss.setup_step = 0
    if "project"    not in ss:
        ss.project = {
            "name": "", "address": "", "start_date": "", "end_date": "",
            "company": "", "primary_color": "#C9A87C",
            "secondary_color": "#1C1C1E", "accent_color": "#E8C97A",
        }
    if "logo_bytes"        not in ss: ss.logo_bytes        = None
    if "rooms"             not in ss: ss.rooms             = [_new_room("거실")]
    if "cur_room"          not in ss: ss.cur_room          = 0
    if "favorites"         not in ss: ss.favorites         = []
    if "sel_cat"           not in ss: ss.sel_cat           = None
    if "sel_brand"         not in ss: ss.sel_brand         = None
    if "sel_sub"           not in ss: ss.sel_sub           = None
    if "search_mat_dicts"  not in ss: ss.search_mat_dicts  = []
    if "search_done"       not in ss: ss.search_done       = False
    if "search_keyword"    not in ss: ss.search_keyword    = ""

_init()
ss = st.session_state


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _fmt(v):
    try: return f"{int(v):,}원"
    except: return str(v) if v else "-"

def _rooms():  return ss.rooms
def _cur_i():  return min(ss.cur_room, len(_rooms()) - 1)
def _room():   return _rooms()[_cur_i()]

def _add_mat(mat):
    idx  = _cur_i()
    pid  = mat["product_id"]
    mats = ss.rooms[idx]["materials"]
    ex   = next((m for m in mats if m["product_id"] == pid), None)
    if ex: ex["qty"] = ex.get("qty", 1) + 1
    else:  mats.append(mat)

def _toggle_fav(mat):
    pid = mat["product_id"]
    if any(f["product_id"] == pid for f in ss.favorites):
        ss.favorites = [f for f in ss.favorites if f["product_id"] != pid]
    else:
        ss.favorites.append(_copy.deepcopy(mat))

def _reset_search():
    ss.sel_cat = None; ss.sel_brand = None; ss.sel_sub = None
    ss.search_mat_dicts = []; ss.search_done = False; ss.search_keyword = ""

def _total_items():
    return sum(len(r["materials"]) for r in _rooms())

def _total_price():
    return sum(
        int(m.get("price",0)) * m.get("qty",1)
        for r in _rooms() for m in r["materials"]
        if str(m.get("price","")).isdigit())

def _sec(title):
    st.markdown(f'<p class="sec-label">{title}</p>', unsafe_allow_html=True)

def _to_json_safe(obj):
    """Encode bytes → base64 string so json.dumps won't fail."""
    if isinstance(obj, bytes):
        return "__b64__:" + base64.b64encode(obj).decode("ascii")
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_safe(v) for v in obj]
    return obj

def _from_json_safe(obj):
    """Decode base64 strings back to bytes after json.loads."""
    if isinstance(obj, str) and obj.startswith("__b64__:"):
        return base64.b64decode(obj[8:])
    if isinstance(obj, dict):
        return {k: _from_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_from_json_safe(v) for v in obj]
    return obj


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — SETUP WIZARD
# ══════════════════════════════════════════════════════════════════════════════
WIZARD = [
    {"q": "현장명이 무엇인가요?",
     "sub": "프로젝트를 식별할 현장명을 입력해주세요.",
     "key": "name",    "type": "text",    "ph": "예) 강남 오피스 리노베이션"},
    {"q": "현장 주소를 알려주세요.",
     "sub": "정확한 주소를 입력하면 PPT에 자동으로 포함됩니다.",
     "key": "address", "type": "text",    "ph": "예) 서울시 강남구 테헤란로 123"},
    {"q": "공사 일정을 선택해주세요.",
     "sub": "착공일과 준공일을 선택하세요.",
     "key": "dates",   "type": "dates",   "ph": ""},
    {"q": "회사 정보를 입력해주세요.",
     "sub": "회사명 또는 로고 이미지를 등록하세요.",
     "key": "company", "type": "logo",    "ph": "예) (주)인테리어디자인"},
    {"q": "색상 테마를 선택해주세요.",
     "sub": "스펙북 전반에 적용될 브랜드 컬러 팔레트를 선택하세요.",
     "key": "colors",  "type": "colors",  "ph": ""},
    {"q": "입력 정보를 확인해주세요.",
     "sub": "모든 정보가 정확한지 확인 후 시작하세요.",
     "key": "confirm", "type": "confirm", "ph": ""},
]

# 인테리어 큐레이션 컬러 팔레트
COLOR_PALETTES = [
    {"name": "모던 클래식",   "desc": "따뜻한 골드와 깊은 블랙",
     "primary": "#C9A87C", "secondary": "#1C1C1E", "accent": "#E8C97A",
     "preview": ["#C9A87C", "#1C1C1E", "#E8C97A"]},
    {"name": "스칸디나비안",  "desc": "자연에서 온 세이지 그린",
     "primary": "#8FA68E", "secondary": "#2C3E35", "accent": "#D4C5B0",
     "preview": ["#8FA68E", "#2C3E35", "#D4C5B0"]},
    {"name": "미니멀 화이트", "desc": "순수한 흰색과 차콜",
     "primary": "#9E9E9E", "secondary": "#212121", "accent": "#F0F0F0",
     "preview": ["#9E9E9E", "#212121", "#F0F0F0"]},
    {"name": "딥 네이비",    "desc": "고급스러운 네이비 블루",
     "primary": "#4A6FA5", "secondary": "#1B2A4A", "accent": "#C9A87C",
     "preview": ["#4A6FA5", "#1B2A4A", "#C9A87C"]},
    {"name": "어반 테라코타", "desc": "따뜻한 흙빛 테라코타",
     "primary": "#C17A5A", "secondary": "#3E2723", "accent": "#F0C4A0",
     "preview": ["#C17A5A", "#3E2723", "#F0C4A0"]},
    {"name": "직접 입력",    "desc": "원하는 색상을 직접 지정하세요",
     "primary": "", "secondary": "", "accent": "",
     "preview": ["#E5E7EB", "#D1D5DB", "#F3F4F6"], "custom": True},
]


def _render_setup():
    proj = ss.project
    step = ss.setup_step
    info = WIZARD[step]
    TOTAL = len(WIZARD)

    # ── 상단 여백 + 브랜드 헤더 ──────────────────────────────────────────────
    st.markdown('<div style="height:40px;"></div>', unsafe_allow_html=True)
    _, hdr, _ = st.columns([1, 3, 1])
    with hdr:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'margin-bottom:40px;">'
            '<div style="display:flex;align-items:center;gap:12px;">'
            '<div style="width:38px;height:38px;background:#1C1C1E;border-radius:12px;'
            'display:flex;align-items:center;justify-content:center;font-size:1rem;'
            'box-shadow:0 4px 12px rgba(0,0,0,.20);">🏠</div>'
            '<div>'
            '<div style="font-size:.60rem;font-weight:700;color:#C9A87C;'
            'letter-spacing:.14em;text-transform:uppercase;">Interior</div>'
            '<div style="font-size:.88rem;font-weight:800;color:#1C1C1E;'
            'letter-spacing:.06em;margin-top:-1px;">SPEC BOOK</div>'
            '</div></div>'
            '<div style="font-size:.70rem;color:#B0B7C3;font-weight:500;">'
            '스펙북 자동화 시스템</div>'
            '</div>',
            unsafe_allow_html=True)

    # ── 메인 카드 ─────────────────────────────────────────────────────────────
    _, C, _ = st.columns([1, 3, 1])
    with C:
        # 닷 스텝 인디케이터
        dots = ""
        for i in range(TOTAL):
            if i < step:
                dots += '<div class="dot-done"></div>'
            elif i == step:
                dots += '<div class="dot-now"></div>'
            else:
                dots += '<div class="dot-next"></div>'

        st.markdown(f'<div class="wiz-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="dot-steps">{dots}</div>'
            f'<div style="font-size:.62rem;font-weight:700;color:#C9A87C;'
            f'letter-spacing:.14em;text-transform:uppercase;margin-bottom:14px;">'
            f'STEP {step+1} &nbsp;/&nbsp; {TOTAL}</div>'
            f'<div class="wiz-step-num">0{step+1}</div>',
            unsafe_allow_html=True)

        # 질문 헤딩
        st.markdown(
            f'<h2 style="font-size:1.70rem;font-weight:800;color:#1C1C1E;'
            f'line-height:1.25;margin-bottom:8px;letter-spacing:-.02em;">'
            f'{info["q"]}</h2>'
            f'<p style="font-size:.82rem;color:#A8ADB8;margin-bottom:30px;'
            f'font-weight:400;line-height:1.5;">{info["sub"]}</p>',
            unsafe_allow_html=True)

        # ── 입력 위젯 ────────────────────────────────────────────────
        if info["type"] == "text":
            val = st.text_input("답변", value=proj.get(info["key"],""),
                                label_visibility="collapsed",
                                placeholder=info["ph"],
                                key=f"wiz_{info['key']}")
            proj[info["key"]] = val

        elif info["type"] == "dates":
            dc1, dc2 = st.columns(2)
            with dc1:
                st.caption("착공일")
                s_str = proj.get("start_date","")
                s_def = date.fromisoformat(s_str) if s_str else date.today()
                sd = st.date_input("착공일", value=s_def,
                                   label_visibility="collapsed", key="wiz_s")
                proj["start_date"] = sd.isoformat()
            with dc2:
                st.caption("준공일")
                e_str = proj.get("end_date","")
                e_def = date.fromisoformat(e_str) if e_str else date.today()
                ed = st.date_input("준공일", value=e_def,
                                   label_visibility="collapsed", key="wiz_e")
                proj["end_date"] = ed.isoformat()

        elif info["type"] == "logo":
            val = st.text_input("회사명", value=proj.get("company",""),
                                label_visibility="collapsed",
                                placeholder=info["ph"], key="wiz_company")
            proj["company"] = val
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            logo_file = st.file_uploader("로고 이미지 업로드 (선택)",
                                         type=["png","jpg","jpeg"], key="wiz_logo")
            if logo_file:
                ss.logo_bytes = logo_file.read()
            if ss.logo_bytes:
                lc, _ = st.columns([1, 3])
                with lc:
                    st.image(ss.logo_bytes, use_container_width=True)

        elif info["type"] == "colors":
            # 팔레트 카드 선택 UI
            sel_pal = ss.get("sel_palette", None)

            for row_palettes in [COLOR_PALETTES[:3], COLOR_PALETTES[3:]]:
                cols = st.columns(3)
                for col, pal in zip(cols, row_palettes):
                    with col:
                        is_sel = (sel_pal == pal["name"])
                        is_custom = pal.get("custom", False)
                        border = "#1C1C1E" if is_sel else "transparent"
                        bg = "#FEFEFE" if is_sel else "#F8F5F0"
                        shadow = "0 6px 24px rgba(0,0,0,.14)" if is_sel else "none"
                        bars = "".join(
                            f'<div style="flex:1;height:52px;background:{c};"></div>'
                            for c in pal["preview"])
                        dot = "●" if is_sel else ""
                        st.markdown(
                            f'<div style="border:2px solid {border};border-radius:18px;'
                            f'background:{bg};box-shadow:{shadow};'
                            f'overflow:hidden;margin-bottom:8px;">'
                            f'<div style="display:flex;">{bars}</div>'
                            f'<div style="padding:12px 14px 10px;">'
                            f'<div style="display:flex;align-items:center;justify-content:space-between;">'
                            f'<div style="font-size:.76rem;font-weight:800;color:#1C1C1E;">{pal["name"]}</div>'
                            f'<div style="font-size:.64rem;color:#C9A87C;font-weight:700;">{dot}</div>'
                            f'</div>'
                            f'<div style="font-size:.62rem;color:#A8ADB8;margin-top:2px;">{pal["desc"]}</div>'
                            f'</div></div>',
                            unsafe_allow_html=True)
                        btn_lbl = "✓ 선택됨" if is_sel else ("✏ 직접 입력" if is_custom else "선택")
                        if st.button(btn_lbl, key=f"pal_{pal['name']}",
                                     type="primary" if is_sel else "secondary",
                                     use_container_width=True):
                            ss.sel_palette = pal["name"]
                            if not is_custom:
                                proj["primary_color"]   = pal["primary"]
                                proj["secondary_color"] = pal["secondary"]
                                proj["accent_color"]    = pal["accent"]
                            else:
                                if not proj.get("primary_color"):
                                    proj["primary_color"]   = "#C9A87C"
                                    proj["secondary_color"] = "#1C1C1E"
                                    proj["accent_color"]    = "#E8C97A"
                            st.rerun()

            if sel_pal:
                pal = next(p for p in COLOR_PALETTES if p["name"] == sel_pal)
                st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

                if pal.get("custom"):
                    st.markdown(
                        '<div style="padding:18px;background:#F8F5F0;border-radius:16px;'
                        'border:1.5px solid #EDE9E3;">'
                        '<div style="font-size:.62rem;font-weight:700;color:#B0B7C3;'
                        'letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px;">'
                        '색상 직접 지정</div>',
                        unsafe_allow_html=True)
                    ca, cb, cc = st.columns(3)
                    with ca:
                        st.caption("🟤 주 색상")
                        c1 = st.color_picker("주색", value=proj.get("primary_color","#C9A87C"),
                                             label_visibility="collapsed", key="cp1")
                        proj["primary_color"] = c1
                        st.markdown(
                            f'<div style="height:4px;background:{c1};border-radius:4px;margin-top:4px;"></div>'
                            f'<div style="font-size:.68rem;font-weight:700;color:#374151;'
                            f'font-family:monospace;margin-top:5px;text-align:center;">{c1.upper()}</div>',
                            unsafe_allow_html=True)
                    with cb:
                        st.caption("⚫ 보조 색상")
                        c2 = st.color_picker("보조", value=proj.get("secondary_color","#1C1C1E"),
                                             label_visibility="collapsed", key="cp2")
                        proj["secondary_color"] = c2
                        st.markdown(
                            f'<div style="height:4px;background:{c2};border-radius:4px;margin-top:4px;"></div>'
                            f'<div style="font-size:.68rem;font-weight:700;color:#374151;'
                            f'font-family:monospace;margin-top:5px;text-align:center;">{c2.upper()}</div>',
                            unsafe_allow_html=True)
                    with cc:
                        st.caption("🟡 강조 색상")
                        c3 = st.color_picker("강조", value=proj.get("accent_color","#E8C97A"),
                                             label_visibility="collapsed", key="cp3")
                        proj["accent_color"] = c3
                        st.markdown(
                            f'<div style="height:4px;background:{c3};border-radius:4px;margin-top:4px;"></div>'
                            f'<div style="font-size:.68rem;font-weight:700;color:#374151;'
                            f'font-family:monospace;margin-top:5px;text-align:center;">{c3.upper()}</div>',
                            unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                else:
                    p1 = proj.get("primary_color","#C9A87C")
                    p2 = proj.get("secondary_color","#1C1C1E")
                    p3 = proj.get("accent_color","#E8C97A")
                    st.markdown(
                        f'<div style="display:flex;gap:12px;align-items:center;'
                        f'padding:14px 18px;background:#F8F5F0;border-radius:16px;'
                        f'border:1.5px solid #EDE9E3;">'
                        f'<div style="display:flex;gap:8px;">'
                        + "".join(
                            f'<div style="display:flex;flex-direction:column;gap:4px;align-items:center;">'
                            f'<div style="width:36px;height:36px;background:{c};border-radius:10px;'
                            f'box-shadow:0 2px 8px rgba(0,0,0,.18);"></div>'
                            f'<span style="font-size:.56rem;color:#A8ADB8;">{lbl}</span>'
                            f'<span style="font-size:.54rem;color:#C4C9D4;font-family:monospace;">{c.upper()}</span>'
                            f'</div>'
                            for c, lbl in [(p1,"주색"),(p2,"보조"),(p3,"강조")]
                        ) +
                        f'</div><div style="flex:1;">'
                        f'<div style="font-size:.80rem;font-weight:800;color:#1C1C1E;">{pal["name"]} 선택됨</div>'
                        f'<div style="font-size:.66rem;color:#A8ADB8;margin-top:3px;">{pal["desc"]}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True)

                    with st.expander("🎨 색상 미세 조정"):
                        ca, cb, cc = st.columns(3)
                        with ca:
                            st.caption("주 색상")
                            c1 = st.color_picker("주색", value=p1, label_visibility="collapsed", key="cp1")
                            proj["primary_color"] = c1
                            st.markdown(f'<div style="font-size:.68rem;font-weight:700;color:#374151;font-family:monospace;margin-top:3px;">{c1.upper()}</div>', unsafe_allow_html=True)
                        with cb:
                            st.caption("보조 색상")
                            c2 = st.color_picker("보조", value=p2, label_visibility="collapsed", key="cp2")
                            proj["secondary_color"] = c2
                            st.markdown(f'<div style="font-size:.68rem;font-weight:700;color:#374151;font-family:monospace;margin-top:3px;">{c2.upper()}</div>', unsafe_allow_html=True)
                        with cc:
                            st.caption("강조 색상")
                            c3 = st.color_picker("강조", value=p3, label_visibility="collapsed", key="cp3")
                            proj["accent_color"] = c3
                            st.markdown(f'<div style="font-size:.68rem;font-weight:700;color:#374151;font-family:monospace;margin-top:3px;">{c3.upper()}</div>', unsafe_allow_html=True)

        elif info["type"] == "confirm":
            def _row(icon, label, value, empty_msg="미입력"):
                v = value or f'<span style="color:#D4D4D8;">{empty_msg}</span>'
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:16px;'
                    f'padding:16px 18px;background:#F8F5F0;border-radius:16px;'
                    f'margin-bottom:8px;border-left:3px solid #E8C97A;">'
                    f'<div style="font-size:1.1rem;margin-top:2px;opacity:.8;">{icon}</div>'
                    f'<div style="flex:1;">'
                    f'<div style="font-size:.60rem;font-weight:700;color:#B0B7C3;'
                    f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px;">{label}</div>'
                    f'<div style="font-size:.90rem;font-weight:600;color:#1C1C1E;line-height:1.4;">{v}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True)

            _row("🏗", "현장명",  proj.get("name",""))
            _row("📍", "주소",    proj.get("address",""))
            s = proj.get("start_date",""); e = proj.get("end_date","")
            _row("📅", "공사 기간", f"{s} ~ {e}" if s or e else "")
            _row("🏢", "회사명",  proj.get("company",""))

            p1 = proj.get("primary_color","#C9A87C")
            p2 = proj.get("secondary_color","#1C1C1E")
            p3 = proj.get("accent_color","#E8C97A")
            pal_name = ss.get("sel_palette","커스텀")
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:14px;'
                f'padding:16px 18px;background:#F8F5F0;border-radius:16px;'
                f'margin-bottom:8px;border-left:3px solid #E8C97A;">'
                f'<div style="font-size:1.1rem;opacity:.8;">🎨</div>'
                f'<div style="flex:1;">'
                f'<div style="font-size:.60rem;font-weight:700;color:#B0B7C3;'
                f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px;">색상 테마</div>'
                f'<div style="display:flex;gap:14px;align-items:flex-start;">'
                + "".join(
                    f'<div style="display:flex;align-items:center;gap:8px;">'
                    f'<div style="width:28px;height:28px;background:{c};border-radius:8px;'
                    f'box-shadow:0 2px 6px rgba(0,0,0,.18);flex-shrink:0;"></div>'
                    f'<div>'
                    f'<div style="font-size:.60rem;color:#A8ADB8;margin-bottom:1px;">{lbl}</div>'
                    f'<div style="font-size:.68rem;font-weight:700;color:#374151;font-family:monospace;">{c.upper()}</div>'
                    f'</div></div>'
                    for c, lbl in [(p1,"주조색"),(p2,"보조색"),(p3,"강조색")]
                ) +
                f'</div></div></div>',
                unsafe_allow_html=True)

            # 로고 미리보기
            if ss.logo_bytes:
                lc, _ = st.columns([1, 4])
                with lc:
                    st.image(ss.logo_bytes, use_container_width=True)

            st.markdown(
                '<div style="background:linear-gradient(135deg,#1C1C1E 0%,#2C2C2E 100%);'
                'border-radius:18px;padding:20px 22px;margin-top:12px;'
                'display:flex;align-items:center;gap:14px;">'
                '<div style="width:36px;height:36px;background:rgba(232,201,122,.15);'
                'border-radius:10px;display:flex;align-items:center;justify-content:center;'
                'font-size:.9rem;flex-shrink:0;">✦</div>'
                '<div>'
                '<div style="font-size:.76rem;color:#E8C97A;font-weight:700;'
                'letter-spacing:.02em;">모든 정보가 확인되셨나요?</div>'
                '<div style="font-size:.70rem;color:rgba(255,255,255,.45);margin-top:3px;">'
                '아래 시작하기 버튼을 눌러 워크스페이스로 이동하세요</div>'
                '</div></div>',
                unsafe_allow_html=True)

            # ── 버튼 행 ──────────────────────────────────────────────────
            st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
            is_last = (step == TOTAL - 1)

            if step > 0:
                n1, n2 = st.columns([1, 2])
                with n1:
                    if st.button("← 이전", use_container_width=True, key="wiz_prev"):
                        ss.setup_step -= 1; st.rerun()
                with n2:
                    next_lbl = "🚀  워크스페이스 시작하기" if is_last else "다음 단계 →"
                    if st.button(next_lbl, type="primary", use_container_width=True, key="wiz_next"):
                        if is_last: ss.page = "workspace"; ss.setup_step = 0
                        else: ss.setup_step += 1
                        st.rerun()
            else:
                if st.button("다음 단계 →", type="primary", use_container_width=True, key="wiz_next"):
                    ss.setup_step += 1; st.rerun()

            # 건너뛰기 링크 스타일
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
            sk_c1, sk_c2, sk_c3 = st.columns([2, 1, 2])
            with sk_c2:
                if st.button("건너뛰기", key="wiz_skip", use_container_width=True):
                    if is_last: ss.page = "workspace"
                    else: ss.setup_step += 1
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)  # wiz-card 닫기

        st.markdown('<div style="height:60px;"></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════
def _render_workspace():
    proj = ss.project

    # ── 네비게이션 바 ─────────────────────────────────────────────────────────
    nav_l, nav_m, nav_r = st.columns([4, 4, 2])
    with nav_l:
        pname = proj.get("name") or "프로젝트"
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0;">'
            f'<div style="width:32px;height:32px;background:#1C1C1E;border-radius:8px;'
            f'display:flex;align-items:center;justify-content:center;font-size:.9rem;">🏠</div>'
            f'<div>'
            f'<div style="font-size:.70rem;color:#9CA3AF;font-weight:500;">INTERIOR SPEC BOOK</div>'
            f'<div style="font-size:.92rem;font-weight:700;color:#1C1C1E;">{pname}</div>'
            f'</div></div>',
            unsafe_allow_html=True)
    with nav_m:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:20px;padding:10px 0;">'
            f'<span style="font-size:.78rem;color:#9CA3AF;">공간 <b style="color:#1C1C1E;">{len(_rooms())}</b>개</span>'
            f'<span style="font-size:.78rem;color:#9CA3AF;">자재 <b style="color:#1C1C1E;">{_total_items()}</b>개</span>'
            f'<span style="font-size:.78rem;color:#B45309;font-weight:700;">{_fmt(_total_price())}</span>'
            f'</div>',
            unsafe_allow_html=True)
    with nav_r:
        st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
        nc1, nc2 = st.columns(2)
        with nc1:
            if st.button("설정 수정", use_container_width=True, key="back_setup"):
                ss.page = "setup"; st.rerun()
        with nc2:
            if st.button("PPT 생성", type="primary", use_container_width=True, key="ppt_nav"):
                ss._ppt_req = True

    # PPT 처리
    if ss.get("_ppt_req"):
        ss._ppt_req = False
        with st.spinner("PPT 생성 중..."):
            try:
                buf = generate_pptx(proj, ss.rooms, logo_bytes=ss.logo_bytes)
                fname = f"specbook_{proj.get('name','프로젝트')}.pptx"
                st.download_button("⬇ PPTX 다운로드", data=buf,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    key="ppt_dl")
            except Exception as e:
                st.error(f"PPT 오류: {e}")

    st.markdown(
        '<hr style="border:none;border-top:1px solid rgba(0,0,0,.06);margin:0 0 24px;">',
        unsafe_allow_html=True)

    # ── 공간 탭 ───────────────────────────────────────────────────────────────
    room_labels = [r["name"] for r in _rooms()] + ["＋ 공간 추가"]
    tabs = st.tabs(room_labels)

    for ti, tab in enumerate(tabs):
        with tab:
            # 공간 추가 탭
            if ti == len(_rooms()):
                st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
                _, ac, _ = st.columns([1, 1.6, 1])
                with ac:
                    st.markdown(
                        '<div style="background:#FFFFFF;border-radius:16px;padding:32px;'
                        'box-shadow:0 4px 20px rgba(0,0,0,.08);text-align:center;'
                        'border:1.5px solid #EDE9E3;">'
                        '<div style="font-size:1.8rem;margin-bottom:12px;">🏡</div>'
                        '<div style="font-weight:700;font-size:1rem;color:#1C1C1E;'
                        'margin-bottom:8px;">새 공간 추가</div>'
                        '<div style="font-size:.80rem;color:#9CA3AF;margin-bottom:20px;">'
                        '거실, 안방, 주방 등 공간을 추가하세요</div>'
                        '</div>', unsafe_allow_html=True)
                    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
                    new_n = st.text_input("공간명", placeholder="예) 안방, 주방",
                                         label_visibility="collapsed", key="new_room_name")
                    if st.button("공간 추가하기", type="primary", use_container_width=True):
                        name = new_n.strip() or f"공간 {len(ss.rooms)+1}"
                        ss.rooms.append(_new_room(name))
                        st.rerun()
                continue

            # cur_room 동기화
            if ss.cur_room != ti:
                ss.cur_room = ti
                _reset_search()

            room = _rooms()[ti]

            # 공간 헤더
            rn_c, rn_stats, rn_del = st.columns([5, 4, 1])
            with rn_c:
                new_name = st.text_input("공간명", room["name"],
                                         label_visibility="collapsed",
                                         key=f"rname_{ti}",
                                         placeholder="공간명")
                if new_name != room["name"]:
                    ss.rooms[ti]["name"] = new_name
            with rn_stats:
                room_price = sum(
                    int(m.get("price",0)) * m.get("qty",1)
                    for m in room["materials"]
                    if str(m.get("price","")).isdigit())
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:16px;padding-top:10px;">'
                    f'<span style="font-size:.76rem;color:#9CA3AF;">'
                    f'자재 <b style="color:#1C1C1E;">{len(room["materials"])}</b>개</span>'
                    f'<span style="font-size:.78rem;font-weight:700;color:#B45309;">{_fmt(room_price)}</span>'
                    f'</div>', unsafe_allow_html=True)
            with rn_del:
                if len(_rooms()) > 1:
                    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                    if st.button("✕", key=f"del_room_{ti}", use_container_width=True):
                        ss.rooms.pop(ti)
                        ss.cur_room = max(0, ti - 1)
                        _reset_search(); st.rerun()

            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

            # 2열 레이아웃
            L, R = st.columns([56, 44], gap="large")
            with L: _render_search(ti)
            with R: _render_materials(ti)

            # 모델링 이미지 (PPT 5p VIEW 01~04)
            _render_modeling_views(ti)


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH PANEL
# ══════════════════════════════════════════════════════════════════════════════
def _render_search(ti: int):
    s_cat   = ss.sel_cat
    s_brand = ss.sel_brand
    s_sub   = ss.sel_sub

    # 스텝 인디케이터
    step_now = 1
    if s_cat:   step_now = 2
    if s_brand: step_now = 3
    if s_sub:   step_now = 4

    STEPS = [("① 카테고리", 1), ("② 업체", 2), ("③ 제품군", 3), ("④ 검색", 4)]
    pills = ""
    for lbl, n in STEPS:
        if n < step_now:
            pills += f'<span class="step-pill step-done">{lbl}</span>'
        elif n == step_now:
            pills += f'<span class="step-pill step-now">{lbl}</span>'
        else:
            pills += f'<span class="step-pill step-next">{lbl}</span>'
    st.markdown(
        f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;">{pills}</div>',
        unsafe_allow_html=True)

    fav_n = len(ss.favorites)
    t_cat, t_fav, t_manual = st.tabs([
        "🔍 카테고리 검색", f"⭐ 즐겨찾기 ({fav_n})", "✏ 직접 입력"])

    # ── 카테고리 검색 ─────────────────────────────────────────────────────────
    with t_cat:
        _sec("① 카테고리 선택")
        rows = [CAT_KEYS[i:i+4] for i in range(0, len(CAT_KEYS), 4)]
        for row in rows:
            cols = st.columns(len(row))
            for col, ck in zip(cols, row):
                icon = CATEGORY_META.get(ck, {}).get("icon", "")
                with col:
                    if st.button(f"{icon} {ck}" if icon else ck,
                                 key=f"cat_{ck}_{ti}",
                                 type="primary" if s_cat == ck else "secondary",
                                 use_container_width=True):
                        ss.sel_cat=ck; ss.sel_brand=None; ss.sel_sub=None
                        ss.search_mat_dicts=[]; ss.search_done=False; st.rerun()

        if s_cat and s_cat in BRAND_CATALOG:
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
            _sec("② 업체 / 브랜드")
            brands = [b["name"] for b in BRAND_CATALOG[s_cat]]
            for row in [brands[i:i+3] for i in range(0, len(brands), 3)]:
                cols = st.columns(len(row))
                for col, bk in zip(cols, row):
                    with col:
                        if st.button(bk, key=f"br_{bk}_{ti}",
                                     type="primary" if s_brand == bk else "secondary",
                                     use_container_width=True):
                            ss.sel_brand=bk; ss.sel_sub=None
                            ss.search_mat_dicts=[]; ss.search_done=False; st.rerun()

        brand_entry = None
        if s_brand and s_cat in BRAND_CATALOG:
            brand_entry = next(
                (b for b in BRAND_CATALOG[s_cat] if b["name"] == s_brand), None)
        if brand_entry:
            subs = brand_entry["groups"]
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
            _sec("③ 제품군")
            for row in [subs[i:i+4] for i in range(0, len(subs), 4)]:
                cols = st.columns(len(row))
                for col, sk in zip(cols, row):
                    with col:
                        if st.button(sk, key=f"sub_{sk}_{ti}",
                                     type="primary" if s_sub == sk else "secondary",
                                     use_container_width=True):
                            ss.sel_sub=sk; ss.search_mat_dicts=[]; ss.search_done=False
                            ss.search_keyword=f"{s_brand} {sk}"; st.rerun()

        if s_sub:
            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
            _sec("④ 검색어 입력 후 검색")
            kc, bc = st.columns([7, 3])
            with kc:
                kw = st.text_input("kw", value=ss.search_keyword,
                                   label_visibility="collapsed",
                                   key=f"kw_{ti}", placeholder="검색어 입력")
                ss.search_keyword = kw
            with bc:
                do_search = st.button("검색", key=f"do_search_{ti}",
                                      use_container_width=True, type="primary")
            if do_search and kw.strip():
                with st.spinner("검색 중..."):
                    try:
                        raw = search_products(
                            brand=s_brand or "", category=s_cat or "",
                            product_group=s_sub or "", keyword=kw.strip(), count=20)
                        mat_dicts = []
                        for item in raw:
                            name  = re.sub(r"<[^>]+>", "", item.get("title",""))
                            brand = item.get("brand", item.get("mallName",""))
                            price = item.get("lprice","")
                            img   = item.get("image","")
                            pid   = str(item.get("productId") or item.get("id") or uuid.uuid4())
                            mat_dicts.append({
                                "product_id": pid, "name": name, "brand": brand,
                                "category": s_cat or "", "sub_category": s_sub or "",
                                "price": price, "image": img, "qty": 1,
                                "spec": "", "finish": "", "memo": "",
                            })
                        ss.search_mat_dicts = mat_dicts
                        ss.search_done      = True
                    except Exception as e:
                        st.error(f"검색 오류: {e}")
                        ss.search_mat_dicts = []; ss.search_done = True

            if ss.search_done:
                mds = ss.search_mat_dicts
                if not mds:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.markdown(
                        f'<p style="font-size:.72rem;color:#9CA3AF;margin:8px 0 14px;">'
                        f'{len(mds)}개 결과</p>', unsafe_allow_html=True)

                    added_pids = {m["product_id"] for m in _rooms()[ti]["materials"]}
                    fav_pids   = {f["product_id"] for f in ss.favorites}

                    for i, mat in enumerate(mds):
                        is_added = mat["product_id"] in added_pids
                        is_fav   = mat["product_id"] in fav_pids

                        with st.container():
                            ic, tc, ac = st.columns([2, 5, 3])
                            with ic:
                                if mat["image"]:
                                    try: st.image(mat["image"], use_container_width=True)
                                    except: _img_placeholder()
                                else: _img_placeholder()
                            with tc:
                                st.markdown(
                                    f'<div style="font-size:.78rem;font-weight:600;'
                                    f'color:#1C1C1E;line-height:1.4;">{mat["name"]}</div>'
                                    f'<div style="font-size:.68rem;color:#9CA3AF;margin-top:3px;">'
                                    f'{mat["brand"]}{" · "+mat["category"] if mat["category"] else ""}</div>'
                                    f'<div style="font-size:.80rem;font-weight:700;'
                                    f'color:#B45309;margin-top:5px;">{_fmt(mat["price"])}</div>',
                                    unsafe_allow_html=True)
                            with ac:
                                add_lbl = "✓ 추가됨" if is_added else "＋ 추가"
                                if st.button(add_lbl, key=f"add_{ti}_{i}",
                                             type="primary" if not is_added else "secondary",
                                             use_container_width=True):
                                    _add_mat(mat); st.rerun()
                                fav_lbl = "★" if is_fav else "☆ 저장"
                                if st.button(fav_lbl, key=f"fres_{ti}_{i}",
                                             use_container_width=True):
                                    _toggle_fav(mat); st.rerun()
                        st.markdown(
                            '<hr style="border:none;border-top:1px solid #F3F4F6;margin:6px 0;">',
                            unsafe_allow_html=True)

    # ── 즐겨찾기 ─────────────────────────────────────────────────────────────
    with t_fav:
        favs = ss.favorites
        if not favs:
            _empty_state("⭐", "즐겨찾기 항목이 없습니다", "검색 결과에서 ☆ 버튼으로 저장하세요")
        else:
            added_pids = {m["product_id"] for m in _rooms()[ti]["materials"]}
            for fi, fav in enumerate(favs):
                is_added = fav["product_id"] in added_pids
                ic, tc, ac = st.columns([2, 5, 3])
                with ic:
                    if fav.get("image"):
                        try: st.image(fav["image"], use_container_width=True)
                        except: _img_placeholder()
                    else: _img_placeholder()
                with tc:
                    st.markdown(
                        f'<div style="font-size:.78rem;font-weight:600;color:#1C1C1E;">{fav["name"]}</div>'
                        f'<div style="font-size:.68rem;color:#9CA3AF;margin-top:3px;">'
                        f'{fav.get("brand","")}{" · "+fav.get("category","") if fav.get("category") else ""}</div>'
                        f'<div style="font-size:.80rem;font-weight:700;color:#B45309;margin-top:5px;">'
                        f'{_fmt(fav.get("price",""))}</div>',
                        unsafe_allow_html=True)
                with ac:
                    add_lbl = "✓ 추가됨" if is_added else "＋ 추가"
                    if st.button(add_lbl, key=f"fadd_{ti}_{fi}",
                                 type="primary" if not is_added else "secondary",
                                 use_container_width=True):
                        _add_mat(_copy.deepcopy(fav)); st.rerun()
                    if st.button("★ 삭제", key=f"fdel_{ti}_{fi}", use_container_width=True):
                        ss.favorites.pop(fi); st.rerun()
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #F3F4F6;margin:6px 0;">',
                    unsafe_allow_html=True)

    # ── 직접 입력 ─────────────────────────────────────────────────────────────
    with t_manual:
        with st.form(f"mf_{ti}", clear_on_submit=True):
            m_name = st.text_input("자재명 *", placeholder="예) LX 디아망 크림화이트 실크벽지")
            c1, c2 = st.columns(2)
            with c1: m_brand = st.text_input("브랜드", placeholder="예) LX하우시스")
            with c2: m_cat   = st.selectbox("카테고리", CAT_KEYS, key=f"mcat_{ti}")
            c3, c4 = st.columns(2)
            with c3: m_spec  = st.text_input("규격", placeholder="예) 1,000mm × 10m")
            with c4: m_price = st.text_input("단가 (원)", placeholder="예) 55000")
            m_memo = st.text_area("메모", height=64, placeholder="기타 참고 사항")
            if st.form_submit_button("＋ 자재 추가", use_container_width=True, type="primary"):
                if m_name.strip():
                    _add_mat({
                        "product_id": str(uuid.uuid4()), "name": m_name.strip(),
                        "brand": m_brand.strip(), "category": m_cat,
                        "sub_category": "", "price": m_price.strip(), "image": "",
                        "qty": 1, "spec": m_spec.strip(), "finish": "", "memo": m_memo.strip(),
                    }); st.rerun()
                else:
                    st.warning("자재명을 입력해주세요.")


# ══════════════════════════════════════════════════════════════════════════════
# MATERIALS PANEL
# ══════════════════════════════════════════════════════════════════════════════
CAT_BG = {
    "벽":"#FEF3E2","바닥":"#F0EDE8","천장":"#F7F7F5","타일":"#EFF6FF",
    "조명":"#FEFCE8","문/도어":"#FDF4E7","창호":"#F0FDF4","가구/목공":"#FEF9EE",
    "전기":"#F0FDF4","설비":"#EFF6FF","도장":"#FDF2F8","필름":"#EEF2FF",
    "몰딩/걸레받이":"#F7F3EE",
}

def _render_materials(ti: int):
    mats = ss.rooms[ti]["materials"]
    room_price = sum(
        int(m.get("price",0)) * m.get("qty",1)
        for m in mats if str(m.get("price","")).isdigit())

    # 헤더
    ph1, ph2 = st.columns([6, 4])
    with ph1:
        st.markdown(
            '<p style="font-size:.90rem;font-weight:700;color:#1C1C1E;margin:2px 0 0;">추가한 자재</p>',
            unsafe_allow_html=True)
    with ph2:
        st.markdown(
            f'<p style="text-align:right;font-size:.88rem;font-weight:700;'
            f'color:#B45309;margin:2px 0 0;">{_fmt(room_price)}</p>',
            unsafe_allow_html=True)

    # JSON 내보내기
    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    j_data = json.dumps(_to_json_safe({"project": ss.project, "rooms": ss.rooms}), ensure_ascii=False, indent=2)
    jc1, jc2 = st.columns(2)
    with jc1:
        st.download_button("💾 JSON 저장", data=j_data,
                           file_name="specbook.json", mime="application/json",
                           use_container_width=True, key=f"jdl_{ti}")
    with jc2:
        up = st.file_uploader("JSON 불러오기", type=["json"],
                              key=f"jup_{ti}", label_visibility="collapsed")
        if up and ss.get("_last_json") != up.name:
            ss._last_json = up.name
            try:
                d = _from_json_safe(json.loads(up.read()))
                if "project" in d: ss.project.update(d["project"])
                if "rooms" in d:   ss.rooms = d["rooms"]
                st.rerun()
            except Exception as e:
                st.error(f"JSON 오류: {e}")

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    if not mats:
        _empty_state("📦", "추가한 자재가 없습니다", "검색 후 자재를 추가해보세요")
        return

    fav_pids = {f["product_id"] for f in ss.favorites}

    for mi, mat in enumerate(mats):
        img   = mat.get("image","")
        pid   = mat.get("product_id", str(mi))
        qty   = mat.get("qty", 1)
        cat   = mat.get("category","")
        bg    = CAT_BG.get(cat, "#F9FAFB")
        is_fav = pid in fav_pids

        # 카드
        with st.container():
            ic, tc = st.columns([3, 7])
            with ic:
                if img:
                    try: st.image(img, use_container_width=True)
                    except:
                        st.markdown(
                            f'<div style="background:{bg};border-radius:10px;'
                            f'min-height:64px;aspect-ratio:1;"></div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div style="background:{bg};border-radius:10px;'
                        f'min-height:64px;aspect-ratio:1;"></div>', unsafe_allow_html=True)
            with tc:
                st.markdown(
                    f'<div style="font-size:.78rem;font-weight:700;color:#1C1C1E;line-height:1.4;">'
                    f'{mat.get("name","")}</div>'
                    f'<div style="font-size:.72rem;font-weight:700;color:#B45309;margin-top:4px;">'
                    f'{_fmt(mat.get("price",""))}</div>'
                    f'<div style="font-size:.66rem;color:#9CA3AF;margin-top:3px;">'
                    f'{mat.get("brand","")}{" · "+cat if cat else ""}</div>',
                    unsafe_allow_html=True)

            # 수량 + 버튼
            bm, bq, bp, bf, bd = st.columns([1.2, 1, 1.2, 1.5, 1.5])
            with bm:
                if st.button("−", key=f"qm_{ti}_{mi}", use_container_width=True):
                    if ss.rooms[ti]["materials"][mi]["qty"] > 1:
                        ss.rooms[ti]["materials"][mi]["qty"] -= 1
                    st.rerun()
            with bq:
                st.markdown(
                    f'<div style="text-align:center;padding:8px 0;font-size:.86rem;'
                    f'font-weight:700;color:#1C1C1E;">{qty}</div>',
                    unsafe_allow_html=True)
            with bp:
                if st.button("＋", key=f"qp_{ti}_{mi}", use_container_width=True):
                    ss.rooms[ti]["materials"][mi]["qty"] += 1; st.rerun()
            with bf:
                if st.button("★" if is_fav else "☆",
                             key=f"fm_{ti}_{mi}", use_container_width=True):
                    _toggle_fav(mat); st.rerun()
            with bd:
                if st.button("삭제", key=f"dl_{ti}_{mi}", use_container_width=True):
                    ss.rooms[ti]["materials"].pop(mi); st.rerun()

            with st.expander("상세 정보"):
                ns = st.text_input("규격",  mat.get("spec",""),   key=f"sp_{ti}_{mi}")
                nf = st.text_input("마감",  mat.get("finish",""), key=f"fi_{ti}_{mi}")
                nm = st.text_area ("메모",  mat.get("memo",""),   key=f"mo_{ti}_{mi}", height=56)
                ss.rooms[ti]["materials"][mi]["spec"]   = ns
                ss.rooms[ti]["materials"][mi]["finish"] = nf
                ss.rooms[ti]["materials"][mi]["memo"]   = nm

        st.markdown(
            '<hr style="border:none;border-top:1px solid #F3F4F6;margin:12px 0;">',
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODELING VIEWS PANEL  (PPT 5p — VIEW 01~04)
# ══════════════════════════════════════════════════════════════════════════════
def _render_modeling_views(ti: int):
    if "modeling_views" not in ss.rooms[ti]:
        ss.rooms[ti]["modeling_views"] = [{}, {}, {}, {}]
    views = ss.rooms[ti]["modeling_views"]
    while len(views) < 4:
        views.append({})

    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin:28px 0 14px;">'
        '<div style="width:3px;height:18px;background:#C9A87C;border-radius:2px;"></div>'
        '<span style="font-size:.88rem;font-weight:700;color:#1C1C1E;">모델링 이미지</span>'
        '<span style="font-size:.70rem;color:#9CA3AF;margin-left:4px;">'
        '최대 4장 · PPT VIEW 01~04 자동 연동</span>'
        '</div>', unsafe_allow_html=True)

    cols = st.columns(4, gap="small")
    for vi, col in enumerate(cols):
        view = views[vi]
        with col:
            st.markdown(
                f'<div style="font-size:.66rem;font-weight:700;color:#C9A87C;'
                f'letter-spacing:.08em;text-align:center;margin-bottom:6px;">'
                f'VIEW 0{vi+1}</div>',
                unsafe_allow_html=True)

            if view.get("image"):
                st.image(view["image"], use_container_width=True)
                if st.button("✕ 삭제", key=f"delv_{ti}_{vi}", use_container_width=True):
                    views[vi]["image"] = None
                    ss.rooms[ti]["modeling_views"] = views
                    st.rerun()
            else:
                img_file = st.file_uploader(
                    f"VIEW 0{vi+1}", type=["png","jpg","jpeg","webp"],
                    key=f"vimg_{ti}_{vi}", label_visibility="collapsed")
                if img_file is not None:
                    views[vi]["image"] = img_file.read()
                    ss.rooms[ti]["modeling_views"] = views
                    st.rerun()

            itm = st.text_input("품목", value=view.get("품목", ""),
                                key=f"vitm_{ti}_{vi}",
                                placeholder="품목 (예: 포세린 타일)",
                                label_visibility="collapsed")
            fin = st.text_input("재질마감", value=view.get("재질마감", ""),
                                key=f"vfin_{ti}_{vi}",
                                placeholder="재질마감 (예: 무광)",
                                label_visibility="collapsed")
            views[vi]["품목"] = itm
            views[vi]["재질마감"] = fin

    ss.rooms[ti]["modeling_views"] = views


# ── UI 유틸 ──────────────────────────────────────────────────────────────────
def _img_placeholder():
    st.markdown(
        '<div style="background:#F3F4F6;border-radius:8px;min-height:56px;'
        'aspect-ratio:1;display:flex;align-items:center;justify-content:center;'
        'font-size:1.2rem;color:#D1D5DB;">🖼</div>',
        unsafe_allow_html=True)

def _empty_state(icon, title, sub):
    st.markdown(
        f'<div style="text-align:center;padding:48px 24px;background:#FFFFFF;'
        f'border:1.5px dashed #E5E1DB;border-radius:16px;">'
        f'<div style="font-size:2rem;margin-bottom:12px;">{icon}</div>'
        f'<div style="font-size:.88rem;font-weight:600;color:#374151;margin-bottom:6px;">{title}</div>'
        f'<div style="font-size:.76rem;color:#9CA3AF;">{sub}</div>'
        f'</div>', unsafe_allow_html=True)


# ── 라우팅 ───────────────────────────────────────────────────────────────────
if ss.page == "setup":
    _render_setup()
else:
    _render_workspace()
