"""
인테리어 스펙북 v9
page: "setup" → "workspace"
setup: 질문 wizard (현장명→주소→날짜→로고→색상)
workspace: 공간별 자재 검색/추가 + PPT
"""
import re, uuid, json, copy as _copy
import streamlit as st
from datetime import datetime, date
from brands import BRAND_CATALOG, CATEGORY_META
from naver_shopping import search_products
from pptx_generator import generate_pptx

st.set_page_config(
    page_title="INTERIOR SPEC BOOK",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CAT_KEYS = list(BRAND_CATALOG.keys())

# ── 글로벌 CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #F5F4F0 !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }

/* ── 버튼 기본 ── */
.stButton > button {
  border-radius: 6px !important; font-size: .80rem !important;
  font-weight: 500 !important; padding: 8px 16px !important;
  background: #FFFFFF !important; color: #374151 !important;
  border: 1.5px solid #D1D5DB !important; transition: all .15s !important;
}
.stButton > button:hover {
  background: #F9FAFB !important; border-color: #9CA3AF !important; color: #111827 !important;
}
/* 활성/선택 버튼 */
div[data-testid="stButton"] > button[kind="primary"] {
  background: #111827 !important; color: #F5C842 !important;
  border-color: #111827 !important; font-weight: 700 !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background: #374151 !important;
}

/* ── 입력창 ── */
.stTextInput input, .stTextArea textarea {
  background: #FFFFFF !important; border: 1.5px solid #D1D5DB !important;
  border-radius: 8px !important; color: #111827 !important;
  font-size: .85rem !important; padding: 10px 14px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #6366F1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,.12) !important;
}
[data-testid="stTextInputRootElement"] input {
  background: #FFFFFF !important; color: #111827 !important;
}
/* date input */
.stDateInput input { background: #FFFFFF !important; color: #111827 !important; }

/* ── 서브탭 ── */
.stTabs [data-baseweb="tab-list"] {
  background: #E5E7EB; padding: 4px; border-radius: 8px; gap: 3px; border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 6px; font-size: .76rem; font-weight: 600; padding: 7px 18px;
  color: #6B7280 !important; background: transparent !important; border: none !important;
}
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important; color: #111827 !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.08) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px !important; }

/* ── 폼 ── */
[data-testid="stForm"] {
  background: #FFFFFF; border: 1.5px solid #E5E7EB;
  border-radius: 10px; padding: 20px;
}

/* ── selectbox ── */
[data-baseweb="select"] > div {
  background: #FFFFFF !important; border: 1.5px solid #D1D5DB !important;
  border-radius: 8px !important; color: #111827 !important;
}

/* ── 색상 입력 (컬러피커) ── */
.stColorPicker > div { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def _new_room(name="거실"):
    return {"id": str(uuid.uuid4()), "name": name, "materials": []}

def _init():
    ss = st.session_state
    if "page" not in ss:           ss.page = "setup"
    if "setup_step" not in ss:     ss.setup_step = 0
    if "project" not in ss:
        ss.project = {
            "name": "", "address": "", "start_date": "", "end_date": "",
            "company": "", "primary_color": "#C9A87C",
            "secondary_color": "#1E1E1E", "accent_color": "#F5C842",
        }
    if "logo_bytes" not in ss:     ss.logo_bytes = None
    if "rooms" not in ss:          ss.rooms = [_new_room("거실")]
    if "cur_room" not in ss:       ss.cur_room = 0
    if "favorites" not in ss:      ss.favorites = []
    # 검색 상태
    for k, v in [
        ("sel_cat", None), ("sel_brand", None), ("sel_sub", None),
        ("search_mat_dicts", []),   # 안정적 mat_dict 목록
        ("search_done", False), ("search_keyword", ""),
    ]:
        if k not in ss: ss[k] = v

_init()

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def _fmt(v):
    try: return f"{int(v):,}원"
    except: return str(v) if v else "-"

def _rooms():  return st.session_state.rooms
def _cur_i():  return min(st.session_state.cur_room, len(_rooms()) - 1)
def _room():   return _rooms()[_cur_i()]

def _add_mat(mat):
    """세션스테이트 직접 접근 — 인덱스 기반으로 안전하게 추가"""
    idx  = _cur_i()
    pid  = mat["product_id"]
    mats = st.session_state.rooms[idx]["materials"]
    ex   = next((m for m in mats if m["product_id"] == pid), None)
    if ex:
        ex["qty"] = ex.get("qty", 1) + 1
    else:
        mats.append(mat)

def _toggle_fav(mat):
    pid  = mat["product_id"]
    favs = st.session_state.favorites
    if any(f["product_id"] == pid for f in favs):
        st.session_state.favorites = [f for f in favs if f["product_id"] != pid]
    else:
        st.session_state.favorites.append(_copy.deepcopy(mat))

def _reset_search():
    st.session_state.sel_cat = None
    st.session_state.sel_brand = None
    st.session_state.sel_sub = None
    st.session_state.search_mat_dicts = []
    st.session_state.search_done = False
    st.session_state.search_keyword = ""

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1: SETUP WIZARD
# ══════════════════════════════════════════════════════════════════════════════
WIZARD_STEPS = [
    {"q": "현장명이 무엇인가요?",          "key": "name",            "type": "text",  "ph": "예) 강남 오피스 리모델링"},
    {"q": "현장 주소를 입력해주세요.",      "key": "address",         "type": "text",  "ph": "예) 서울시 강남구 테헤란로 123"},
    {"q": "착공일과 준공일을 선택해주세요.", "key": "dates",           "type": "dates", "ph": ""},
    {"q": "회사명 또는 로고를 등록하세요.", "key": "company",         "type": "logo",  "ph": "예) (주)인테리어디자인"},
    {"q": "브랜드 색상을 설정하세요.",      "key": "colors",          "type": "colors","ph": ""},
]

def _render_setup():
    ss   = st.session_state
    step = ss.setup_step
    proj = ss.project

    # 전체 중앙 정렬 컨테이너
    _, center, _ = st.columns([1, 2, 1])
    with center:
        # 로고/앱명
        st.markdown(
            '<div style="text-align:center;margin-bottom:32px;">'
            '<div style="font-size:1.4rem;font-weight:700;color:#111827;letter-spacing:.04em;">'
            'INTERIOR SPEC BOOK</div>'
            '<div style="font-size:.80rem;color:#9CA3AF;margin-top:4px;">프로젝트 기본 정보 설정</div>'
            '</div>', unsafe_allow_html=True)

        # 진행 표시
        progress = (step + 1) / len(WIZARD_STEPS)
        st.progress(progress)
        st.markdown(
            f'<div style="text-align:right;font-size:.72rem;color:#9CA3AF;margin:-8px 0 20px;">'
            f'{step + 1} / {len(WIZARD_STEPS)}</div>', unsafe_allow_html=True)

        # 현재 질문
        info = WIZARD_STEPS[step]
        st.markdown(
            f'<div style="font-size:1.10rem;font-weight:700;color:#111827;'
            f'margin-bottom:20px;">{info["q"]}</div>', unsafe_allow_html=True)

        # 입력 위젯
        answer_ok = True
        if info["type"] == "text":
            val = st.text_input("답변", value=proj.get(info["key"], ""),
                                label_visibility="collapsed",
                                placeholder=info["ph"],
                                key=f"wiz_{info['key']}")
            proj[info["key"]] = val
            answer_ok = bool(val.strip())

        elif info["type"] == "dates":
            dc1, dc2 = st.columns(2)
            with dc1:
                st.caption("착공일")
                start_str = proj.get("start_date", "")
                start_def = date.fromisoformat(start_str) if start_str else date.today()
                sd = st.date_input("착공일", value=start_def, label_visibility="collapsed",
                                   key="wiz_start")
                proj["start_date"] = sd.isoformat()
            with dc2:
                st.caption("준공일")
                end_str = proj.get("end_date", "")
                end_def = date.fromisoformat(end_str) if end_str else date.today()
                ed = st.date_input("준공일", value=end_def, label_visibility="collapsed",
                                   key="wiz_end")
                proj["end_date"] = ed.isoformat()

        elif info["type"] == "logo":
            comp = st.text_input("회사명", value=proj.get("company", ""),
                                 label_visibility="collapsed",
                                 placeholder=info["ph"],
                                 key="wiz_company")
            proj["company"] = comp
            st.caption("또는 로고 이미지 업로드 (선택)")
            logo_file = st.file_uploader("로고", type=["png","jpg","jpeg"],
                                         label_visibility="collapsed", key="wiz_logo")
            if logo_file:
                ss.logo_bytes = logo_file.read()
            if ss.logo_bytes:
                lc, _ = st.columns([1, 2])
                with lc:
                    st.image(ss.logo_bytes, use_container_width=True)

        elif info["type"] == "colors":
            st.caption("스펙북 전반에 사용될 브랜드 색상입니다.")
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                st.caption("주 색상")
                c1 = st.color_picker("주색", value=proj.get("primary_color","#C9A87C"),
                                     label_visibility="collapsed", key="wiz_c1")
                proj["primary_color"] = c1
            with cc2:
                st.caption("보조 색상")
                c2 = st.color_picker("보조색", value=proj.get("secondary_color","#1E1E1E"),
                                     label_visibility="collapsed", key="wiz_c2")
                proj["secondary_color"] = c2
            with cc3:
                st.caption("강조 색상")
                c3 = st.color_picker("강조색", value=proj.get("accent_color","#F5C842"),
                                     label_visibility="collapsed", key="wiz_c3")
                proj["accent_color"] = c3

        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)

        # 이전 / 다음 버튼
        nav1, nav2, nav3 = st.columns([2, 3, 2])
        with nav1:
            if step > 0:
                if st.button("← 이전", use_container_width=True):
                    ss.setup_step -= 1
                    st.rerun()
        with nav3:
            is_last = (step == len(WIZARD_STEPS) - 1)
            next_label = "완료 →" if is_last else "다음 →"
            if st.button(next_label, type="primary", use_container_width=True):
                if is_last:
                    ss.page = "workspace"
                    ss.setup_step = 0
                    st.rerun()
                else:
                    ss.setup_step += 1
                    st.rerun()

        # 건너뛰기
        st.markdown(
            '<div style="text-align:center;margin-top:16px;">', unsafe_allow_html=True)
        if st.button("건너뛰기", key="wiz_skip"):
            if step == len(WIZARD_STEPS) - 1:
                ss.page = "workspace"
            else:
                ss.setup_step += 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2: WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════
def _render_workspace():
    ss   = st.session_state
    proj = ss.project

    # ── 상단 네비바 ──────────────────────────────────────────────────────────
    nb1, nb2, nb3 = st.columns([5, 3, 2])
    with nb1:
        pname = proj.get("name") or "프로젝트"
        st.markdown(
            f'<div style="background:#111827;color:#F5C842;padding:12px 20px;'
            f'font-size:.88rem;font-weight:700;letter-spacing:.04em;border-radius:8px;">'
            f'INTERIOR SPEC BOOK &nbsp;·&nbsp; {pname}</div>',
            unsafe_allow_html=True)
    with nb2:
        total_items = sum(len(r["materials"]) for r in _rooms())
        total_price = sum(
            int(m.get("price",0)) * m.get("qty",1)
            for r in _rooms() for m in r["materials"]
            if str(m.get("price","")).isdigit())
        st.markdown(
            f'<div style="padding:14px 0;font-size:.76rem;color:#6B7280;">'
            f'공간 {len(_rooms())}개 &nbsp;·&nbsp; 자재 {total_items}개 &nbsp;·&nbsp; {_fmt(total_price)}'
            f'</div>', unsafe_allow_html=True)
    with nb3:
        if st.button("✦ PPT 생성", type="primary", use_container_width=True, key="ppt_top"):
            ss._ppt_requested = True
        if st.button("← 프로젝트 수정", use_container_width=True, key="back_setup"):
            ss.page = "setup"
            st.rerun()

    # PPT 처리
    if ss.get("_ppt_requested"):
        ss._ppt_requested = False
        with st.spinner("PPT 생성 중..."):
            try:
                buf = generate_pptx(proj, ss.rooms, logo_bytes=ss.logo_bytes)
                fname = f"specbook_{proj.get('name','프로젝트')}.pptx"
                st.download_button("⬇ 다운로드", data=buf, file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    key="ppt_dl_top")
            except Exception as e:
                st.error(f"PPT 오류: {e}")

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    # ── 공간 탭 ──────────────────────────────────────────────────────────────
    room_labels = [r["name"] for r in _rooms()] + ["＋ 공간 추가"]
    tabs = st.tabs(room_labels)

    for ti, tab in enumerate(tabs):
        with tab:
            # "공간 추가" 탭
            if ti == len(_rooms()):
                st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
                _, ac, _ = st.columns([1, 2, 1])
                with ac:
                    new_name = st.text_input("새 공간명", placeholder="예) 안방", key="new_room_name")
                    if st.button("공간 추가", type="primary", use_container_width=True):
                        if new_name.strip():
                            ss.rooms.append(_new_room(new_name.strip()))
                        else:
                            ss.rooms.append(_new_room(f"공간{len(ss.rooms)+1}"))
                        st.rerun()
                continue

            # 공간 탭 선택 → cur_room 갱신 (탭 클릭 감지)
            # Streamlit 탭은 클릭 시 자동 rerun 되지 않으므로,
            # 탭 내부에서 cur_room을 해당 인덱스로 설정
            if ss.cur_room != ti:
                ss.cur_room = ti
                _reset_search()

            room = _rooms()[ti]

            # 공간명 편집 + 삭제
            rn1, rn2, rn3 = st.columns([6, 2, 2])
            with rn1:
                new_name = st.text_input("공간명", room["name"],
                                         label_visibility="collapsed",
                                         key=f"rname_{ti}",
                                         placeholder="공간명")
                if new_name != room["name"]:
                    ss.rooms[ti]["name"] = new_name
            with rn2:
                st.markdown(
                    f'<div style="padding-top:10px;font-size:.76rem;color:#9CA3AF;">'
                    f'{len(room["materials"])}개 자재</div>', unsafe_allow_html=True)
            with rn3:
                if len(_rooms()) > 1:
                    if st.button("공간 삭제", key=f"del_room_{ti}"):
                        ss.rooms.pop(ti)
                        ss.cur_room = max(0, ti - 1)
                        _reset_search()
                        st.rerun()

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

            # ── 2열: 검색 + 자재 목록 ────────────────────────────────────
            left, right = st.columns([57, 43], gap="large")

            # ── 왼쪽: 검색 ───────────────────────────────────────────────
            with left:
                _render_search(ti)

            # ── 오른쪽: 자재 목록 ────────────────────────────────────────
            with right:
                _render_materials(ti)


def _render_search(tab_idx: int):
    ss      = st.session_state
    s_cat   = ss.sel_cat
    s_brand = ss.sel_brand
    s_sub   = ss.sel_sub

    # 스텝바
    step_now = 1
    if s_cat:   step_now = 2
    if s_brand: step_now = 3
    if s_sub:   step_now = 4

    STEPS = [("① 카테고리", 1), ("② 업체", 2), ("③ 제품군", 3), ("④ 검색", 4)]
    sh = ""
    for label, n in STEPS:
        if n < step_now:
            s = "background:#E8DDD0;color:#92400E;border:1.5px solid #D4BC96;"
        elif n == step_now:
            s = "background:#111827;color:#F5C842;border:1.5px solid #111827;font-weight:700;"
        else:
            s = "background:#F3F4F6;color:#D1D5DB;border:1.5px solid #E5E7EB;"
        sh += f'<div style="{s}flex:1;text-align:center;padding:8px 4px;border-radius:6px;font-size:.72rem;">{label}</div>'
    st.markdown(f'<div style="display:flex;gap:5px;margin-bottom:14px;">{sh}</div>', unsafe_allow_html=True)

    fav_n = len(ss.favorites)
    t_search, t_fav, t_manual = st.tabs([
        "🔍 카테고리 검색", f"⭐ 즐겨찾기 ({fav_n})", "✏ 직접 입력"])

    # ── 카테고리 검색 ─────────────────────────────────────────────────────────
    with t_search:
        _section("① 카테고리 선택")
        rows = [CAT_KEYS[i:i+4] for i in range(0, len(CAT_KEYS), 4)]
        for row in rows:
            cols = st.columns(len(row))
            for col, ck in zip(cols, row):
                meta  = CATEGORY_META.get(ck, {})
                icon  = meta.get("icon", "")
                with col:
                    if st.button(f"{icon} {ck}" if icon else ck,
                                 key=f"cat_{ck}_{tab_idx}",
                                 type="primary" if s_cat == ck else "secondary",
                                 use_container_width=True):
                        ss.sel_cat = ck
                        ss.sel_brand = None
                        ss.sel_sub = None
                        ss.search_mat_dicts = []
                        ss.search_done = False
                        st.rerun()

        if s_cat and s_cat in BRAND_CATALOG:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            _section("② 업체 / 브랜드")
            brands = [b["name"] for b in BRAND_CATALOG[s_cat]]
            rows_b = [brands[i:i+3] for i in range(0, len(brands), 3)]
            for row in rows_b:
                cols = st.columns(len(row))
                for col, bk in zip(cols, row):
                    with col:
                        if st.button(bk, key=f"br_{bk}_{tab_idx}",
                                     type="primary" if s_brand == bk else "secondary",
                                     use_container_width=True):
                            ss.sel_brand = bk
                            ss.sel_sub = None
                            ss.search_mat_dicts = []
                            ss.search_done = False
                            st.rerun()

        brand_entry = None
        if s_brand and s_cat in BRAND_CATALOG:
            brand_entry = next(
                (b for b in BRAND_CATALOG[s_cat] if b["name"] == s_brand), None)
        if brand_entry:
            subs = brand_entry["groups"]
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            _section("③ 제품군")
            rows_s = [subs[i:i+4] for i in range(0, len(subs), 4)]
            for row in rows_s:
                cols = st.columns(len(row))
                for col, sk in zip(cols, row):
                    with col:
                        if st.button(sk, key=f"sub_{sk}_{tab_idx}",
                                     type="primary" if s_sub == sk else "secondary",
                                     use_container_width=True):
                            ss.sel_sub = sk
                            ss.search_mat_dicts = []
                            ss.search_done = False
                            ss.search_keyword = f"{s_brand} {sk}"
                            st.rerun()

        if s_sub:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            _section("④ 검색")
            kc, bc = st.columns([7, 3])
            with kc:
                kw = st.text_input("kw", value=ss.search_keyword,
                                   label_visibility="collapsed",
                                   key=f"kw_{tab_idx}",
                                   placeholder="검색어 입력")
                ss.search_keyword = kw
            with bc:
                do_search = st.button("검색", key=f"do_search_{tab_idx}",
                                      use_container_width=True)
            if do_search and kw.strip():
                with st.spinner("검색 중..."):
                    try:
                        raw = search_products(
                            brand=s_brand or "",
                            category=s_cat or "",
                            product_group=s_sub or "",
                            keyword=kw.strip(),
                            count=20,
                        )
                        # ★ 핵심: mat_dict를 한 번만 생성해 세션에 저장
                        mat_dicts = []
                        for item in raw:
                            name  = re.sub(r"<[^>]+>", "", item.get("title",""))
                            brand = item.get("brand", item.get("mallName",""))
                            price = item.get("lprice","")
                            img   = item.get("image","")
                            pid   = str(item.get("productId") or item.get("id") or uuid.uuid4())
                            mat_dicts.append({
                                "product_id":   pid,
                                "name":         name,
                                "brand":        brand,
                                "category":     s_cat or "",
                                "sub_category": s_sub or "",
                                "price":        price,
                                "image":        img,
                                "qty":          1,
                                "spec":         "",
                                "finish":       "",
                                "memo":         "",
                            })
                        ss.search_mat_dicts = mat_dicts
                        ss.search_done      = True
                    except Exception as e:
                        st.error(f"검색 오류: {e}")
                        ss.search_mat_dicts = []
                        ss.search_done      = True

            if ss.search_done:
                mat_dicts = ss.search_mat_dicts
                if not mat_dicts:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.markdown(
                        f'<p style="font-size:.70rem;color:#9CA3AF;margin:6px 0 10px;">'
                        f'{len(mat_dicts)}개 결과</p>', unsafe_allow_html=True)

                    # 현재 공간 자재 pid 목록 (추가 여부 표시용)
                    added_pids = {m["product_id"] for m in _rooms()[tab_idx]["materials"]}
                    fav_pids   = {f["product_id"] for f in ss.favorites}

                    # ★ 인덱스 i 기반 버튼 키 — pid 변동 없음
                    for i, mat in enumerate(mat_dicts):
                        img_url = mat["image"]
                        is_added = mat["product_id"] in added_pids
                        is_fav   = mat["product_id"] in fav_pids

                        ic, tc, ac = st.columns([2, 5, 3])
                        with ic:
                            if img_url:
                                try: st.image(img_url, use_container_width=True)
                                except: st.markdown("🖼")
                            else:
                                st.markdown(
                                    '<div style="background:#E5E7EB;border-radius:6px;'
                                    'min-height:54px;display:flex;align-items:center;'
                                    'justify-content:center;font-size:1.2rem;">🖼</div>',
                                    unsafe_allow_html=True)
                        with tc:
                            st.markdown(
                                f'<div style="font-size:.76rem;font-weight:600;color:#111827;'
                                f'line-height:1.4;">{mat["name"]}</div>'
                                f'<div style="font-size:.68rem;color:#9CA3AF;margin-top:2px;">'
                                f'{mat["brand"]}{"  ·  "+mat["category"] if mat["category"] else ""}</div>'
                                f'<div style="font-size:.78rem;font-weight:700;color:#DC2626;'
                                f'margin-top:4px;">{_fmt(mat["price"])}</div>',
                                unsafe_allow_html=True)
                        with ac:
                            add_lbl = "✓ 추가됨" if is_added else "＋ 추가"
                            if st.button(add_lbl, key=f"add_{tab_idx}_{i}",
                                         use_container_width=True):
                                _add_mat(mat)
                                st.rerun()
                            fav_lbl = "★ 저장됨" if is_fav else "☆ 즐겨찾기"
                            if st.button(fav_lbl, key=f"fav_res_{tab_idx}_{i}",
                                         use_container_width=True):
                                _toggle_fav(mat)
                                st.rerun()

                        st.markdown(
                            '<hr style="border:none;border-top:1px solid #F3F4F6;margin:6px 0;">',
                            unsafe_allow_html=True)

    # ── 즐겨찾기 탭 ──────────────────────────────────────────────────────────
    with t_fav:
        favs = ss.favorites
        if not favs:
            st.markdown(
                '<div style="text-align:center;padding:40px 20px;color:#D1D5DB;font-size:.82rem;">'
                '검색 결과에서 ☆ 즐겨찾기 버튼으로<br>자재를 저장하세요.</div>',
                unsafe_allow_html=True)
        else:
            added_pids = {m["product_id"] for m in _rooms()[tab_idx]["materials"]}
            for fi, fav in enumerate(favs):
                is_added = fav["product_id"] in added_pids
                ic, tc, ac = st.columns([2, 5, 3])
                with ic:
                    if fav.get("image"):
                        try: st.image(fav["image"], use_container_width=True)
                        except: st.markdown("🖼")
                    else:
                        st.markdown("🖼")
                with tc:
                    st.markdown(
                        f'<div style="font-size:.76rem;font-weight:600;color:#111827;">{fav["name"]}</div>'
                        f'<div style="font-size:.68rem;color:#9CA3AF;margin-top:2px;">'
                        f'{fav.get("brand","")}{"  ·  "+fav.get("category","") if fav.get("category") else ""}</div>'
                        f'<div style="font-size:.78rem;font-weight:700;color:#DC2626;margin-top:4px;">'
                        f'{_fmt(fav.get("price",""))}</div>',
                        unsafe_allow_html=True)
                with ac:
                    add_lbl = "✓ 추가됨" if is_added else "＋ 추가"
                    if st.button(add_lbl, key=f"fav_add_{fi}_{tab_idx}",
                                 use_container_width=True):
                        _add_mat(_copy.deepcopy(fav))
                        st.rerun()
                    if st.button("★ 삭제", key=f"fav_del_{fi}_{tab_idx}",
                                 use_container_width=True):
                        ss.favorites.pop(fi)
                        st.rerun()
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #F3F4F6;margin:6px 0;">',
                    unsafe_allow_html=True)

    # ── 직접 입력 탭 ─────────────────────────────────────────────────────────
    with t_manual:
        with st.form(f"manual_{tab_idx}", clear_on_submit=True):
            m_name = st.text_input("자재명 *", placeholder="예) LX 디아망 크림화이트 실크벽지")
            mc1, mc2 = st.columns(2)
            with mc1:
                m_brand = st.text_input("브랜드", placeholder="예) LX하우시스")
            with mc2:
                m_cat = st.selectbox("카테고리", CAT_KEYS, key=f"mcat_{tab_idx}")
            mc3, mc4 = st.columns(2)
            with mc3:
                m_spec = st.text_input("규격", placeholder="예) 1,000mm × 10m")
            with mc4:
                m_price = st.text_input("단가 (원)", placeholder="예) 55000")
            m_memo = st.text_area("메모", height=60, placeholder="기타 참고 사항")
            if st.form_submit_button("＋ 자재 추가", use_container_width=True):
                if m_name.strip():
                    _add_mat({
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


def _render_materials(tab_idx: int):
    ss   = st.session_state
    mats = ss.rooms[tab_idx]["materials"]
    room_total = sum(
        int(m.get("price",0)) * m.get("qty",1)
        for m in mats if str(m.get("price","")).isdigit())

    ph1, ph2 = st.columns([6, 4])
    with ph1:
        st.markdown(
            '<p style="font-size:.86rem;font-weight:700;color:#111827;margin:2px 0 0;">추가한 자재</p>',
            unsafe_allow_html=True)
    with ph2:
        st.markdown(
            f'<p style="text-align:right;font-size:.84rem;font-weight:700;'
            f'color:#DC2626;margin:2px 0 0;">{_fmt(room_total)}</p>',
            unsafe_allow_html=True)

    # JSON 내보내기
    j_data = json.dumps({"project": ss.project, "rooms": ss.rooms},
                        ensure_ascii=False, indent=2)
    dc1, dc2 = st.columns(2)
    with dc1:
        st.download_button("💾 JSON 저장", data=j_data,
                           file_name="specbook.json", mime="application/json",
                           use_container_width=True, key=f"json_dl_{tab_idx}")
    with dc2:
        uploaded = st.file_uploader("JSON 불러오기", type=["json"],
                                    key=f"json_up_{tab_idx}",
                                    label_visibility="collapsed")
        if uploaded and ss.get("_last_json") != uploaded.name:
            ss._last_json = uploaded.name
            try:
                d = json.loads(uploaded.read())
                if "project" in d: ss.project.update(d["project"])
                if "rooms" in d:   ss.rooms = d["rooms"]
                st.rerun()
            except Exception as e:
                st.error(f"JSON 오류: {e}")

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    if not mats:
        st.markdown(
            '<div style="text-align:center;padding:48px 20px;background:#FFFFFF;'
            'border:1.5px dashed #D1D5DB;border-radius:10px;">'
            '<div style="font-size:2rem;margin-bottom:10px;">📦</div>'
            '<div style="font-size:.80rem;color:#9CA3AF;">검색 후 자재를 추가하세요</div>'
            '</div>', unsafe_allow_html=True)
        return

    CAT_BG = {
        "벽":"#FEF3E2","바닥":"#F0EDE8","천장":"#F5F5F4","타일":"#EFF6FF",
        "조명":"#FEFCE8","문/도어":"#FDF4E7","창호":"#F0FDF4","가구/목공":"#FEF9EE",
        "전기":"#F0FDF4","설비":"#EFF6FF","도장":"#FDF2F8","필름":"#EEF2FF",
        "몰딩/걸레받이":"#F7F3EE",
    }
    fav_pids = {f["product_id"] for f in ss.favorites}

    for mi, mat in enumerate(mats):
        img   = mat.get("image","")
        name  = mat.get("name","")
        brand = mat.get("brand","")
        cat   = mat.get("category","")
        price = mat.get("price","")
        qty   = mat.get("qty",1)
        pid   = mat.get("product_id", str(mi))
        bg    = CAT_BG.get(cat, "#F9FAFB")
        is_fav = pid in fav_pids

        with st.container():
            ic, tc = st.columns([3, 7])
            with ic:
                if img:
                    try: st.image(img, use_container_width=True)
                    except:
                        st.markdown(
                            f'<div style="background:{bg};border-radius:6px;'
                            f'min-height:60px;aspect-ratio:1;"></div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div style="background:{bg};border-radius:6px;'
                        f'min-height:60px;aspect-ratio:1;"></div>', unsafe_allow_html=True)
            with tc:
                st.markdown(
                    f'<div style="font-size:.78rem;font-weight:700;color:#111827;line-height:1.35;">{name}</div>'
                    f'<div style="font-size:.72rem;font-weight:700;color:#DC2626;margin-top:3px;">{_fmt(price)}</div>'
                    f'<div style="font-size:.66rem;color:#9CA3AF;margin-top:2px;">'
                    f'{brand}{"  ·  "+cat if cat else ""}</div>',
                    unsafe_allow_html=True)

            # 수량 + 액션 버튼
            bm, bq, bp, bf, bd = st.columns([1.2, 1, 1.2, 1.5, 1.5])
            with bm:
                if st.button("−", key=f"qm_{tab_idx}_{mi}", use_container_width=True):
                    if ss.rooms[tab_idx]["materials"][mi]["qty"] > 1:
                        ss.rooms[tab_idx]["materials"][mi]["qty"] -= 1
                    st.rerun()
            with bq:
                st.markdown(
                    f'<div style="text-align:center;padding:7px 0;font-size:.84rem;'
                    f'font-weight:700;color:#111827;">{qty}</div>',
                    unsafe_allow_html=True)
            with bp:
                if st.button("＋", key=f"qp_{tab_idx}_{mi}", use_container_width=True):
                    ss.rooms[tab_idx]["materials"][mi]["qty"] += 1
                    st.rerun()
            with bf:
                if st.button("★" if is_fav else "☆", key=f"fmat_{tab_idx}_{mi}",
                             use_container_width=True):
                    _toggle_fav(mat)
                    st.rerun()
            with bd:
                if st.button("삭제", key=f"del_{tab_idx}_{mi}", use_container_width=True):
                    ss.rooms[tab_idx]["materials"].pop(mi)
                    st.rerun()

            with st.expander("상세 정보"):
                new_spec = st.text_input("규격", mat.get("spec",""), key=f"sp_{tab_idx}_{mi}")
                new_fin  = st.text_input("마감", mat.get("finish",""), key=f"fi_{tab_idx}_{mi}")
                new_memo = st.text_area("메모", mat.get("memo",""), key=f"mo_{tab_idx}_{mi}", height=56)
                ss.rooms[tab_idx]["materials"][mi]["spec"]   = new_spec
                ss.rooms[tab_idx]["materials"][mi]["finish"] = new_fin
                ss.rooms[tab_idx]["materials"][mi]["memo"]   = new_memo

        st.markdown(
            '<hr style="border:none;border-top:1px solid #F3F4F6;margin:10px 0;">',
            unsafe_allow_html=True)


def _section(title: str):
    st.markdown(
        f'<p style="font-size:.68rem;font-weight:700;color:#9CA3AF;'
        f'letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px;">{title}</p>',
        unsafe_allow_html=True)


# ── 라우팅 ───────────────────────────────────────────────────────────────────
if st.session_state.page == "setup":
    _render_setup()
else:
    _render_workspace()
