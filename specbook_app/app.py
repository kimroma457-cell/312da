"""
인테리어 스펙북 생성기 v6
구조: 사이드바(공간/프로젝트/PPT) + 메인(스텝검색 + 추가자재)
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

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;}
.stApp{background:#F4F2EE;}
#MainMenu,footer{visibility:hidden;}
[data-testid="stHeader"]{display:none!important;}

/* 사이드바 다크 */
[data-testid="stSidebar"]{background:#1A1816!important;min-width:220px!important;max-width:260px!important;}
[data-testid="stSidebar"] *{color:#C8C0B8!important;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea{
  background:#2A2520!important;border:1px solid #3A3530!important;color:#F0EAE2!important;border-radius:6px!important;}
[data-testid="stSidebar"] .stButton>button{
  width:100%!important;background:#2A2520!important;color:#C8A97E!important;
  border:1px solid #3A3530!important;border-radius:7px!important;font-size:.76rem!important;
  font-weight:600!important;margin-bottom:2px!important;transition:.12s!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:#3A3530!important;border-color:#C8A97E!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{
  background:#C8A97E!important;color:#1A1816!important;border-color:#C8A97E!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{background:#B8997E!important;}
[data-testid="stSidebar"] hr{border-color:#3A3530!important;margin:8px 0!important;}
[data-testid="stSidebar"] label{color:#8A8280!important;font-size:.72rem!important;}
[data-testid="stSidebarContent"]{padding:12px 12px 20px!important;}

/* 사이드바 섹션 레이블 */
.sb-label{color:#6A6260!important;font-size:.64rem!important;font-weight:700!important;
  letter-spacing:.08em!important;text-transform:uppercase!important;
  margin:14px 0 5px!important;padding:0!important;}

/* 공간 버튼 - 활성 */
.space-active button{background:#C8A97E!important;color:#1A1816!important;border-color:#C8A97E!important;}

/* 일반 버튼 */
.stButton>button{
  border-radius:8px!important;font-size:.76rem!important;font-weight:600!important;
  background:#fff!important;color:#4A4540!important;border:1.5px solid #DDD8D2!important;
  transition:.12s!important;white-space:nowrap!important;}
.stButton>button:hover{background:#FDF8F2!important;border-color:#C8A97E!important;color:#1A1816!important;}
div[data-testid="stButton"]>button[kind="primary"]{
  background:#1A1816!important;color:#C8A97E!important;border-color:#1A1816!important;}
div[data-testid="stButton"]>button[kind="primary"]:hover{background:#C8A97E!important;color:#1A1816!important;}

/* 카드 */
.mat-card{background:#fff;border:1.5px solid #E8E4DE;border-radius:10px;
  padding:10px;margin-bottom:8px;}
.mat-card-title{font-size:.82rem;font-weight:700;color:#1A1816;line-height:1.3;}
.mat-card-sub{font-size:.70rem;color:#8A8280;margin-top:2px;}
.mat-price{font-size:.80rem;font-weight:700;color:#C8A97E;margin-top:3px;}

/* 스텝바 */
.step-bar{display:flex;gap:4px;margin-bottom:12px;}
.step-item{flex:1;text-align:center;padding:7px 4px;border-radius:8px;
  font-size:.72rem;font-weight:600;background:#EDEAE5;color:#8A8280;cursor:default;}
.step-active{background:#1A1816;color:#C8A97E;}

/* 섹션 타이틀 */
.sec-title{font-size:.70rem;font-weight:700;color:#8A8280;letter-spacing:.06em;
  text-transform:uppercase;margin:14px 0 7px;}

/* 검색결과 행 */
.result-row{display:flex;gap:10px;align-items:flex-start;padding:10px;
  border-bottom:1px solid #F0ECE8;}
.result-row:hover{background:#FDFAF7;}
.result-info{flex:1;min-width:0;}
.result-name{font-size:.78rem;font-weight:600;color:#1A1816;line-height:1.35;}
.result-brand{font-size:.68rem;color:#8A8280;margin-top:2px;}
.result-price{font-size:.76rem;font-weight:700;color:#C8A97E;margin-top:3px;}

/* 헤더바 */
.top-header{background:#1A1816;color:#C8A97E;padding:12px 20px;
  font-size:.88rem;font-weight:700;letter-spacing:.04em;
  border-radius:10px;margin-bottom:14px;}

/* 서브탭 */
.stTabs [data-baseweb="tab-list"]{background:#EDEAE5;padding:3px;border-radius:8px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:6px;font-size:.73rem;font-weight:600;
  padding:5px 14px;color:#6B6059!important;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;}

/* 입력창 */
.stTextInput input,.stTextArea textarea{border-radius:8px!important;
  border:1.5px solid #DDD8D2!important;font-size:.80rem!important;}

/* 숫자 입력 */
.stNumberInput input{border-radius:8px!important;font-size:.80rem!important;}

/* 메트릭 */
[data-testid="stMetric"]{background:#fff;border-radius:10px;padding:10px 14px;
  border:1px solid #E8E4DE;}
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
    # 검색 상태
    for k, v in [("sel_cat", None), ("sel_brand", None), ("sel_sub", None),
                 ("search_results", []), ("search_done", False),
                 ("search_keyword", "")]:
        if k not in st.session_state:
            st.session_state[k] = v

_init()

p = st.session_state.project
rooms = st.session_state.rooms
cur_idx = st.session_state.current_room_idx
if cur_idx >= len(rooms):
    cur_idx = 0
    st.session_state.current_room_idx = 0
room = rooms[cur_idx]

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def _fmt_price(v):
    try: return f"{int(v):,}원"
    except: return str(v)

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
    st.session_state.sel_cat = None
    st.session_state.sel_brand = None
    st.session_state.sel_sub = None
    st.session_state.search_results = []
    st.session_state.search_done = False
    st.session_state.search_keyword = ""

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # 프로젝트 정보
    with st.expander("📋 프로젝트 정보", expanded=False):
        p["name"]     = st.text_input("프로젝트명", p["name"], key="p_name")
        p["client"]   = st.text_input("의뢰인", p.get("client",""), key="p_client")
        p["designer"] = st.text_input("디자이너", p.get("designer",""), key="p_designer")
        p["date"]     = st.text_input("날짜", p.get("date",""), key="p_date")
        p["address"]  = st.text_input("현장주소", p.get("address",""), key="p_addr")

    # 표지 로고
    with st.expander("🖼 표지 로고", expanded=False):
        logo_file = st.file_uploader("로고 이미지", type=["png","jpg","jpeg"],
                                     key="logo_up", label_visibility="collapsed")
        if logo_file:
            st.session_state.logo_bytes = logo_file.read()
        if st.session_state.logo_bytes:
            st.image(st.session_state.logo_bytes, use_container_width=True)

    st.markdown('<div class="sb-label">SPACES</div>', unsafe_allow_html=True)

    # 공간 목록
    for i, r in enumerate(rooms):
        active = (i == cur_idx)
        col_a, col_b = st.columns([7, 3])
        with col_a:
            btn_style = "primary" if active else "secondary"
            if st.button(f"{'▶ ' if active else ''}{r['name']}", key=f"room_sel_{i}",
                         type=btn_style if active else "secondary",
                         use_container_width=True):
                if not active:
                    st.session_state.current_room_idx = i
                    _reset_search()
                    st.rerun()
        with col_b:
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
    st.markdown('<div class="sb-label">FILE</div>', unsafe_allow_html=True)

    # JSON 저장
    json_data = json.dumps(
        {"project": p, "rooms": rooms}, ensure_ascii=False, indent=2)
    st.download_button("💾 JSON 저장", data=json_data,
                       file_name="specbook.json", mime="application/json",
                       use_container_width=True)

    # JSON 업로드
    uploaded = st.file_uploader("Upload", type=["json"],
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

    st.markdown('<div style="font-size:.62rem;color:#6A6260;margin-top:4px;">200MB per file • JSON</div>',
                unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sb-label">EXPORT</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:.70rem;color:#8A8280;margin-bottom:8px;">'
        f'공간 {len(rooms)}개 · 자재 {_total_items()}개 · {_fmt_price(_total_price())}</div>',
        unsafe_allow_html=True)

    if st.button("✦ PPT 스펙북 생성", type="primary", use_container_width=True):
        with st.spinner("PPT 생성 중..."):
            try:
                buf = generate_pptx(p, rooms,
                                    logo_bytes=st.session_state.logo_bytes)
                st.download_button("⬇ 다운로드", data=buf,
                                   file_name=f"specbook_{p['name']}.pptx",
                                   mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"PPT 오류: {e}")

# ── 메인 ─────────────────────────────────────────────────────────────────────
# 헤더
st.markdown(
    f'<div class="top-header">INTERIOR SPEC BOOK &nbsp;•&nbsp; {room["name"]}</div>',
    unsafe_allow_html=True)

# 공간명 행
c1, c2 = st.columns([8, 2])
with c1:
    new_name = st.text_input("", room["name"], label_visibility="collapsed",
                              key=f"rname_{room['id']}", placeholder="공간명")
    if new_name != room["name"]:
        room["name"] = new_name
with c2:
    mat_count = len(room["materials"])
    st.markdown(
        f'<div style="text-align:right;padding-top:8px;font-size:.78rem;'
        f'color:#8A8280;">{mat_count}개 자재</div>',
        unsafe_allow_html=True)

# ── 2열: 검색(좌) + 추가한 자재(우) ─────────────────────────────────────────
left_col, right_col = st.columns([58, 42], gap="medium")

# ════════════════════════════════════════════════════════════
# 왼쪽: 검색 영역
# ════════════════════════════════════════════════════════════
with left_col:
    s_cat   = st.session_state.sel_cat
    s_brand = st.session_state.sel_brand
    s_sub   = st.session_state.sel_sub

    # 스텝 표시
    step_num = 1
    if s_cat:   step_num = 2
    if s_brand: step_num = 3
    if s_sub:   step_num = 4

    steps_html = ""
    for i, label in enumerate(["① 카테고리", "② 업체", "③ 제품군", "④ 검색결과"], 1):
        cls = "step-active" if i == step_num else "step-item"
        # override: if already selected, show as completed style
        if i < step_num:
            steps_html += f'<div class="step-item" style="color:#C8A97E;background:#2A2520;">{label}</div>'
        else:
            steps_html += f'<div class="{cls}">{label}</div>'
    st.markdown(f'<div class="step-bar">{steps_html}</div>', unsafe_allow_html=True)

    # 서브탭
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🔍 카테고리 검색", f"⭐ 즐겨찾기 ({len(st.session_state.favorites)})", "✏ 직접 입력"])

    # ── 탭1: 카테고리 검색 ────────────────────────────────────
    with sub_tab1:
        # ① 카테고리
        st.markdown('<div class="sec-title">① 카테고리 선택</div>', unsafe_allow_html=True)
        n_cols = 4
        rows_cat = [CAT_KEYS[i:i+n_cols] for i in range(0, len(CAT_KEYS), n_cols)]
        for row in rows_cat:
            cols = st.columns(len(row))
            for col, ck in zip(cols, row):
                meta = CATEGORY_META.get(ck, {})
                icon = meta.get("icon", "")
                label = f"{icon} {ck}" if icon else ck
                is_sel = (s_cat == ck)
                with col:
                    btn_type = "primary" if is_sel else "secondary"
                    if st.button(label, key=f"cat_{ck}", type=btn_type,
                                 use_container_width=True):
                        st.session_state.sel_cat = ck
                        st.session_state.sel_brand = None
                        st.session_state.sel_sub = None
                        st.session_state.search_results = []
                        st.session_state.search_done = False
                        st.rerun()

        # ② 업체/브랜드 (카테고리 선택 후)
        if s_cat and s_cat in BRAND_CATALOG:
            brands = list(BRAND_CATALOG[s_cat].keys())
            st.markdown('<div class="sec-title">② 업체 / 브랜드</div>', unsafe_allow_html=True)
            rows_br = [brands[i:i+3] for i in range(0, len(brands), 3)]
            for row in rows_br:
                cols = st.columns(len(row))
                for col, bk in zip(cols, row):
                    is_sel = (s_brand == bk)
                    with col:
                        if st.button(bk, key=f"br_{bk}", type="primary" if is_sel else "secondary",
                                     use_container_width=True):
                            st.session_state.sel_brand = bk
                            st.session_state.sel_sub = None
                            st.session_state.search_results = []
                            st.session_state.search_done = False
                            st.rerun()

        # ③ 제품군 (브랜드 선택 후)
        if s_brand and s_cat in BRAND_CATALOG and s_brand in BRAND_CATALOG[s_cat]:
            subs = BRAND_CATALOG[s_cat][s_brand]
            st.markdown('<div class="sec-title">③ 제품군</div>', unsafe_allow_html=True)
            rows_sub = [subs[i:i+4] for i in range(0, len(subs), 4)]
            for row in rows_sub:
                cols = st.columns(len(row))
                for col, sk in zip(cols, row):
                    is_sel = (s_sub == sk)
                    with col:
                        if st.button(sk, key=f"sub_{sk}", type="primary" if is_sel else "secondary",
                                     use_container_width=True):
                            st.session_state.sel_sub = sk
                            st.session_state.search_results = []
                            st.session_state.search_done = False
                            kw = f"{s_brand} {sk}"
                            st.session_state.search_keyword = kw
                            st.rerun()

        # ④ 검색
        if s_sub:
            st.markdown('<div class="sec-title">④ 검색</div>', unsafe_allow_html=True)
            kw_c, btn_c = st.columns([7, 3])
            with kw_c:
                kw = st.text_input("", value=st.session_state.search_keyword,
                                   label_visibility="collapsed",
                                   key="kw_input", placeholder="검색어 입력")
                st.session_state.search_keyword = kw
            with btn_c:
                do_search = st.button("🔍 검색", key="do_search", use_container_width=True)

            if do_search and kw.strip():
                with st.spinner("검색 중..."):
                    try:
                        results = search_products(kw.strip(), display=20)
                        st.session_state.search_results = results
                        st.session_state.search_done = True
                    except Exception as e:
                        st.error(f"검색 오류: {e}")
                        st.session_state.search_results = []
                        st.session_state.search_done = True

            results = st.session_state.search_results
            if st.session_state.search_done:
                if not results:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.markdown(f'<div style="font-size:.70rem;color:#8A8280;margin-bottom:6px;">{len(results)}개 결과</div>',
                                unsafe_allow_html=True)
                    for item in results:
                        img_url  = item.get("image", "")
                        name     = re.sub(r"<[^>]+>", "", item.get("title", ""))
                        brand    = item.get("brand", item.get("mallName", ""))
                        price    = item.get("lprice", "")
                        prod_id  = item.get("productId", item.get("id", str(uuid.uuid4())))

                        rc1, rc2, rc3 = st.columns([2, 6, 2])
                        with rc1:
                            if img_url:
                                try: st.image(img_url, use_container_width=True)
                                except: st.markdown("🖼")
                            else:
                                st.markdown("🖼")
                        with rc2:
                            st.markdown(
                                f'<div class="result-name">{name}</div>'
                                f'<div class="result-brand">{brand} · {s_cat}</div>'
                                f'<div class="result-price">{_fmt_price(price)}</div>',
                                unsafe_allow_html=True)
                        with rc3:
                            if st.button("＋ 추가", key=f"add_{prod_id}_{room['id']}",
                                         use_container_width=True):
                                # 중복 체크
                                existing = next(
                                    (m for m in room["materials"] if m.get("product_id") == prod_id), None)
                                if existing:
                                    existing["qty"] = existing.get("qty", 1) + 1
                                else:
                                    room["materials"].append({
                                        "product_id": prod_id,
                                        "name": name,
                                        "brand": brand,
                                        "category": s_cat,
                                        "sub_category": s_sub or "",
                                        "price": price,
                                        "image": img_url,
                                        "qty": 1,
                                        "spec": "",
                                        "finish": "",
                                        "memo": "",
                                    })
                                st.rerun()
                        st.markdown('<hr style="margin:4px 0;border-color:#F0ECE8;">', unsafe_allow_html=True)

    # ── 탭2: 즐겨찾기 ─────────────────────────────────────────
    with sub_tab2:
        favs = st.session_state.favorites
        if not favs:
            st.info("즐겨찾기한 자재가 없습니다. 검색 후 ☆ 버튼으로 추가하세요.")
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
                        f'<div class="result-name">{fav["name"]}</div>'
                        f'<div class="result-brand">{fav.get("brand","")} · {fav.get("category","")}</div>'
                        f'<div class="result-price">{_fmt_price(fav.get("price",""))}</div>',
                        unsafe_allow_html=True)
                with fc3:
                    if st.button("＋", key=f"fav_add_{fi}", use_container_width=True):
                        pid = fav.get("product_id", str(uuid.uuid4()))
                        existing = next((m for m in room["materials"]
                                         if m.get("product_id") == pid), None)
                        if existing:
                            existing["qty"] = existing.get("qty", 1) + 1
                        else:
                            room["materials"].append(_copy.deepcopy(fav))
                        st.rerun()
                st.markdown('<hr style="margin:4px 0;border-color:#F0ECE8;">', unsafe_allow_html=True)

    # ── 탭3: 직접 입력 ───────────────────────────────────────
    with sub_tab3:
        st.markdown('<div class="sec-title">자재 직접 입력</div>', unsafe_allow_html=True)
        with st.form("manual_form", clear_on_submit=True):
            m_name  = st.text_input("자재명 *", placeholder="예) LX 디아망 실크벽지")
            m_brand = st.text_input("브랜드", placeholder="예) LX하우시스")
            m_cat   = st.selectbox("카테고리", CAT_KEYS)
            m_spec  = st.text_input("규격", placeholder="예) 1,000mm × 10m")
            m_price = st.text_input("단가 (원)", placeholder="예) 55000")
            m_memo  = st.text_area("메모", height=60)
            if st.form_submit_button("＋ 자재 추가", use_container_width=True):
                if m_name.strip():
                    room["materials"].append({
                        "product_id": str(uuid.uuid4()),
                        "name": m_name.strip(),
                        "brand": m_brand.strip(),
                        "category": m_cat,
                        "sub_category": "",
                        "price": m_price.strip(),
                        "image": "",
                        "qty": 1,
                        "spec": m_spec.strip(),
                        "finish": "",
                        "memo": m_memo.strip(),
                    })
                    st.rerun()
                else:
                    st.warning("자재명을 입력하세요.")

# ════════════════════════════════════════════════════════════
# 오른쪽: 추가한 자재
# ════════════════════════════════════════════════════════════
with right_col:
    mats = room["materials"]
    room_total = sum(
        int(m.get("price", 0)) * m.get("qty", 1)
        for m in mats if str(m.get("price","")).isdigit()
    )

    rc1h, rc2h = st.columns([6, 4])
    with rc1h:
        st.markdown('<div style="font-weight:700;font-size:.82rem;color:#1A1816;padding-top:6px;">추가한 자재</div>',
                    unsafe_allow_html=True)
    with rc2h:
        st.markdown(
            f'<div style="text-align:right;font-size:.78rem;color:#C8A97E;font-weight:700;padding-top:6px;">'
            f'{_fmt_price(room_total)}</div>',
            unsafe_allow_html=True)

    if not mats:
        st.markdown(
            '<div style="text-align:center;padding:30px 10px;color:#B0A898;font-size:.78rem;">'
            '자재를 검색하여 추가하세요.</div>',
            unsafe_allow_html=True)
    else:
        for mi, mat in enumerate(mats):
            with st.container():
                img_url = mat.get("image", "")
                name    = mat.get("name", "")
                brand   = mat.get("brand", "")
                cat     = mat.get("category", "")
                price   = mat.get("price", "")
                qty     = mat.get("qty", 1)
                pid     = mat.get("product_id", str(mi))

                # 색상 스와치 (카테고리별)
                cat_colors = {
                    "벽": "#E8C4A0", "바닥": "#B8A898", "천장": "#D8D4CE",
                    "타일": "#A8B8C8", "조명": "#F0D878", "문/도어": "#C8A870",
                }
                swatch = cat_colors.get(cat, "#C8C0B8")

                ma1, ma2 = st.columns([3, 7])
                with ma1:
                    if img_url:
                        try:
                            st.image(img_url, use_container_width=True)
                        except:
                            st.markdown(
                                f'<div style="width:100%;aspect-ratio:1;background:{swatch};'
                                f'border-radius:6px;"></div>',
                                unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'<div style="width:100%;aspect-ratio:1;background:{swatch};'
                            f'border-radius:6px;"></div>',
                            unsafe_allow_html=True)
                with ma2:
                    st.markdown(
                        f'<div class="mat-card-title">{name}</div>'
                        f'<div class="mat-price">{_fmt_price(price)}</div>'
                        f'<div class="mat-card-sub">{brand}{"  ·  " + cat if cat else ""}</div>',
                        unsafe_allow_html=True)

                # 수량 + 버튼 행
                qc1, qc2, qc3, qc4, qc5 = st.columns([1, 1, 1, 1, 1])
                with qc1:
                    if st.button("−", key=f"qty_m_{pid}_{mi}", use_container_width=True):
                        if mat["qty"] > 1:
                            mat["qty"] -= 1
                        st.rerun()
                with qc2:
                    st.markdown(
                        f'<div style="text-align:center;padding:5px 0;font-size:.80rem;font-weight:700;">{qty}</div>',
                        unsafe_allow_html=True)
                with qc3:
                    if st.button("＋", key=f"qty_p_{pid}_{mi}", use_container_width=True):
                        mat["qty"] = mat.get("qty", 1) + 1
                        st.rerun()
                with qc4:
                    is_fav = any(f.get("product_id") == pid for f in st.session_state.favorites)
                    fav_icon = "★" if is_fav else "☆"
                    if st.button(fav_icon, key=f"fav_{pid}_{mi}", use_container_width=True):
                        if is_fav:
                            st.session_state.favorites = [
                                f for f in st.session_state.favorites
                                if f.get("product_id") != pid]
                        else:
                            st.session_state.favorites.append(_copy.deepcopy(mat))
                        st.rerun()
                with qc5:
                    if st.button("×", key=f"del_{pid}_{mi}", use_container_width=True):
                        room["materials"].pop(mi)
                        st.rerun()

                # 스펙/피니시 입력
                with st.expander("상세 정보", expanded=False):
                    mat["spec"]   = st.text_input("규격", mat.get("spec",""),
                                                  key=f"spec_{pid}_{mi}")
                    mat["finish"] = st.text_input("마감", mat.get("finish",""),
                                                  key=f"fin_{pid}_{mi}")
                    mat["memo"]   = st.text_area("메모", mat.get("memo",""),
                                                 key=f"memo_{pid}_{mi}", height=60)

                st.markdown('<hr style="margin:6px 0;border-color:#F0ECE8;">', unsafe_allow_html=True)
