"""
인테리어 스펙북 생성기 v4
구조: 사이드바(공간관리+프로젝트+내보내기) + 메인(검색 | 자재목록)
"""
import re, uuid, json, copy as _copy
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
#MainMenu,footer,header{visibility:hidden;}

/* ── Top bar ── */
.top-bar{background:#1A1816;padding:10px 28px;margin:-1rem -1rem 1.4rem -1rem;
         display:flex;align-items:center;gap:14px;}
.tb-title{color:#fff;font-size:1.05rem;font-weight:700;letter-spacing:1.5px;flex:1;margin:0;}
.gold{color:#C8A97E;}
.tb-room{color:#8C8078;font-size:.75rem;margin-left:auto;}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{background:#1A1816!important;}
section[data-testid="stSidebar"] *{color:#C8C0B8!important;}
section[data-testid="stSidebar"] .stMarkdown h3{
  color:#8C8078!important;font-size:.6rem!important;letter-spacing:2.5px!important;
  text-transform:uppercase!important;margin:16px 0 6px!important;font-weight:700!important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea{
  background:#252220!important;border:1px solid #383230!important;
  color:#E0DAD4!important;border-radius:6px!important;font-size:.75rem!important;}
section[data-testid="stSidebar"] label{color:#7A7068!important;font-size:.68rem!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:#252220!important;border:1px solid #383230!important;color:#C0B8B0!important;
  border-radius:8px!important;font-size:.75rem!important;font-weight:500!important;
  text-align:left!important;width:100%!important;transition:.12s!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  border-color:#C8A97E!important;color:#C8A97E!important;background:#2C2926!important;}
section[data-testid="stSidebar"] div[data-testid="stButton"]>button[kind="primary"]{
  background:#C8A97E!important;color:#1A1816!important;border-color:#C8A97E!important;
  font-weight:700!important;}
section[data-testid="stSidebar"] div[data-testid="stButton"]>button[kind="primary"]:hover{
  background:#B8956A!important;border-color:#B8956A!important;}
section[data-testid="stSidebar"] hr{border-color:#2C2926!important;margin:8px 0!important;}

/* ── Main buttons ── */
.stButton>button{
  border-radius:8px!important;font-size:.76rem!important;font-weight:600!important;
  background:#fff!important;color:#4A4540!important;border:1.5px solid #DDD8D2!important;
  transition:.12s!important;box-shadow:0 1px 2px rgba(0,0,0,.04)!important;}
.stButton>button:hover{
  background:#FDF8F2!important;border-color:#C8A97E!important;color:#1A1816!important;}
div[data-testid="stButton"]>button[kind="primary"]{
  background:#1A1816!important;color:#C8A97E!important;border-color:#1A1816!important;}
div[data-testid="stButton"]>button[kind="primary"]:hover{
  background:#C8A97E!important;color:#1A1816!important;border-color:#C8A97E!important;}

/* ── Step bar ── */
.stepbar{display:flex;align-items:center;gap:0;margin-bottom:14px;border-radius:8px;overflow:hidden;border:1.5px solid #DDD8D2;}
.step{flex:1;padding:7px 10px;font-size:.68rem;font-weight:700;text-align:center;
      background:#F8F6F2;color:#A09890;letter-spacing:.3px;}
.step+.step{border-left:1px solid #DDD8D2;}
.step.done{background:#F0EBE4;color:#7A6E68;}
.step.active{background:#1A1816;color:#C8A97E;}

/* ── Section label ── */
.slabel{font-size:.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
        color:#C8A97E;margin:12px 0 6px;display:block;}

/* ── Product card ── */
.pcard-title{font-size:.80rem;font-weight:700;color:#1A1816;line-height:1.35;margin-bottom:2px;}
.pcard-price{font-size:.82rem;font-weight:700;color:#C8A97E;}
.pcard-meta{font-size:.64rem;color:#9A8F86;}

/* ── Material card ── */
.mat-card{background:#fff;border:1px solid #EAE5DF;border-radius:10px;
          padding:9px 11px;margin-bottom:5px;
          box-shadow:0 1px 3px rgba(0,0,0,.04);}
.mat-name{font-size:.78rem;font-weight:700;color:#1A1816;
          overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.mat-meta{font-size:.63rem;color:#9A8F86;margin-top:2px;}
.mat-price{font-size:.71rem;font-weight:700;color:#C8A97E;}

/* ── Badge ── */
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.60rem;
       font-weight:700;background:#EDE8E0;color:#5A4E44;}

/* ── Tabs (즐겨찾기/직접입력) ── */
.stTabs [data-baseweb="tab-list"]{background:#EDEAE5;padding:3px;border-radius:8px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:6px;font-weight:600;font-size:.73rem;
                              padding:4px 10px;color:#6B6059!important;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;}

/* ── Qty inline ── */
.qty-row{display:flex;align-items:center;gap:4px;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def _init_specbook():
    return {k: [] for k in CAT_KEYS}

def _init_sel():
    return {"cat": None, "brand": None, "group": None}

for key, val in [
    ("rooms",         []),
    ("favorites",     []),
    ("logo_bytes",    None),
    ("active_rid",    None),   # 현재 선택된 방 id
    ("view",          "workspace"),  # workspace | export
    ("pptx_bytes",    None),
    ("project", {
        "company":  "DESICODE",
        "name":     "○○ 아파트 리모델링",
        "location": "서울시 강남구",
        "area":     "84㎡ (25.4평)",
        "period":   "2026.07 ~ 2026.08",
        "designer": "홍길동",
        "date":     datetime.now().strftime("%Y.%m.%d"),
    }),
]:
    if key not in st.session_state:
        st.session_state[key] = val

ROOM_PRESETS = [
    ("거실","Living Room","🛋"),("침실","Bedroom","🛏"),("주방","Kitchen","🍳"),
    ("욕실","Bathroom","🚿"),("현관","Entrance","🚪"),("드레스룸","Dressing Room","👗"),
    ("서재","Study Room","📚"),("다이닝","Dining Room","🍽"),
    ("복도","Hallway","🔲"),("발코니","Balcony","🌿"),
]

def _add_room(ko, en):
    same = sum(1 for r in st.session_state.rooms if r["name"].startswith(ko))
    name = f"{ko}{same+1}" if same else ko
    rid  = str(uuid.uuid4())[:8]
    st.session_state.rooms.append({
        "id":      rid, "name": name, "name_en": en,
        "specbook": _init_specbook(), "sel": _init_sel(),
    })
    st.session_state.active_rid = rid
    st.session_state.view = "workspace"
    st.rerun()

def _extract_spec(title):
    m = re.search(r'\d+(?:\.\d+)?[\s]*[×xX\*][\s]*\d+(?:\.\d+)?'
                  r'(?:[\s]*[×xX\*][\s]*\d+(?:\.\d+)?)?(?:[\s]*(?:mm|cm|m))?',
                  title, re.IGNORECASE)
    if m: return m.group().strip()
    m = re.search(r'\d+(?:\.\d+)?[\s]*(?:mm|cm|m²|㎡)', title, re.IGNORECASE)
    return m.group().strip() if m else ""

def _active_room():
    rid = st.session_state.active_rid
    return next((r for r in st.session_state.rooms if r["id"] == rid), None)

# p와 total_all은 전역에서 먼저 계산
p = st.session_state.project
total_all = sum(len(it) for r in st.session_state.rooms for it in r["specbook"].values())

# ── Top Bar ───────────────────────────────────────────────────────────────────
room_now = _active_room()
room_label = f"&nbsp;·&nbsp;<span style='color:#8C8078;font-size:.74rem'>{room_now['name']}</span>" if room_now else ""
st.markdown(f"""
<div class="top-bar">
  <p class="tb-title">INTERIOR <span class="gold">SPEC BOOK</span>{room_label}</p>
</div>""", unsafe_allow_html=True)

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # 프로젝트 정보
    with st.expander("📋 프로젝트 정보", expanded=False):
        p["company"]  = st.text_input("회사명",    p.get("company",""),  key="si_co")
        p["name"]     = st.text_input("프로젝트명", p.get("name",""),    key="si_pj")
        p["location"] = st.text_input("위치",      p.get("location",""), key="si_lo")
        p["area"]     = st.text_input("면적",      p.get("area",""),     key="si_ar")
        p["period"]   = st.text_input("공사기간",  p.get("period",""),   key="si_pe")
        p["designer"] = st.text_input("담당자",    p.get("designer",""), key="si_de")
        p["date"]     = st.text_input("작성일",    p.get("date",""),     key="si_da")

    # 로고
    with st.expander("🖼 표지 로고", expanded=False):
        logo_file = st.file_uploader("PNG/JPG", type=["png","jpg","jpeg"],
                                     key="logo_upload", label_visibility="collapsed")
        if logo_file:
            st.session_state.logo_bytes = logo_file.read()
        if st.session_state.logo_bytes:
            st.image(st.session_state.logo_bytes, width=100)
            if st.button("로고 제거", key="logo_clr"):
                st.session_state.logo_bytes = None; st.rerun()

    st.markdown("---")
    st.markdown("### SPACES")

    # 공간 목록
    for room in st.session_state.rooms:
        n_items = sum(len(v) for v in room["specbook"].values())
        is_active = room["id"] == st.session_state.active_rid
        label = f"{'▶ ' if is_active else ''}{room['name']}  ({n_items})"
        if st.button(label, key=f"sel_{room['id']}",
                     type="primary" if is_active else "secondary",
                     use_container_width=True):
            st.session_state.active_rid = room["id"]
            st.session_state.view = "workspace"
            st.rerun()
        if st.button(f"✕ {room['name']} 삭제", key=f"del_{room['id']}",
                     use_container_width=True):
            st.session_state.rooms = [r for r in st.session_state.rooms if r["id"] != room["id"]]
            if st.session_state.active_rid == room["id"]:
                st.session_state.active_rid = st.session_state.rooms[0]["id"] if st.session_state.rooms else None
            st.rerun()

    # 공간 추가
    with st.expander("＋ 공간 추가", expanded=not st.session_state.rooms):
        for ko, en, icon in ROOM_PRESETS:
            if st.button(f"{icon} {ko}", key=f"pr_{ko}", use_container_width=True):
                _add_room(ko, en)
        st.markdown("---")
        cko = st.text_input("직접 입력 (한글)", placeholder="홈짐", key="cko")
        cen = st.text_input("영문명", placeholder="Home Gym", key="cen")
        if st.button("추가", key="cadd", type="primary", use_container_width=True) and cko:
            _add_room(cko, cen or cko)

    st.markdown("---")
    st.markdown("### FILE")

    # JSON 저장
    export_data = {
        "project": st.session_state.project,
        "favorites": st.session_state.favorites,
        "rooms": [
            {"name": r["name"], "name_en": r["name_en"],
             "items": [it for its in r["specbook"].values() for it in its]}
            for r in st.session_state.rooms
        ],
    }
    st.download_button("📥 JSON 저장", data=json.dumps(export_data, ensure_ascii=False, indent=2),
                       file_name=f"{p['name']}_specbook.json", mime="application/json",
                       use_container_width=True)

    # JSON 불러오기
    uploaded = st.file_uploader("📂 JSON 불러오기", type="json", key="json_import",
                                label_visibility="collapsed")
    if uploaded and st.session_state.get("_last_json") != uploaded.name:
        st.session_state["_last_json"] = uploaded.name
        try:
            data = json.loads(uploaded.read())
            st.session_state.project   = data.get("project", st.session_state.project)
            st.session_state.favorites = data.get("favorites", [])
            st.session_state.rooms = []
            for r in data.get("rooms", []):
                sb = _init_specbook()
                for it in r.get("items", []):
                    cat = it.get("category", "")
                    if cat in sb: sb[cat].append(it)
                st.session_state.rooms.append({
                    "id": str(uuid.uuid4())[:8], "name": r["name"],
                    "name_en": r.get("name_en", ""), "specbook": sb, "sel": _init_sel(),
                })
            st.session_state.active_rid = st.session_state.rooms[0]["id"] if st.session_state.rooms else None
            st.success("불러오기 완료!"); st.rerun()
        except Exception as e:
            st.error(f"파일 오류: {e}")

    st.markdown("---")
    st.markdown("### EXPORT")

    total_budget = sum(it.get("price_int",0)*it.get("qty",1)
                       for r in st.session_state.rooms
                       for its in r["specbook"].values() for it in its)
    st.markdown(
        f"<div style='font-size:.68rem;color:#7A7068;margin-bottom:8px'>"
        f"공간 {len(st.session_state.rooms)}개 · 자재 {total_all}개 · {total_budget:,}원</div>",
        unsafe_allow_html=True,
    )

    if st.button("🎨 PPT 스펙북 생성", type="primary", use_container_width=True,
                 disabled=total_all == 0, key="sb_ppt"):
        st.session_state.view = "export"
        st.session_state.pptx_bytes = None
        st.rerun()

    if st.session_state.view == "export" and st.session_state.pptx_bytes:
        st.download_button(
            "⬇️ PPT 다운로드",
            data=st.session_state.pptx_bytes,
            file_name=f"{p['name']}_스펙북.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )

# ── 메인 뷰 ──────────────────────────────────────────────────────────────────

# ── Export 뷰 ──────────────────────────────────────────────────────────────
if st.session_state.view == "export":
    st.markdown("## 📄 PPT 스펙북 생성")

    # 요약 메트릭
    m1, m2, m3 = st.columns(3)
    m1.metric("공간 수", len(st.session_state.rooms))
    m2.metric("총 자재 수", total_all)
    m3.metric("총 예산", f"{total_budget:,}원")

    # 공간별 요약
    st.markdown("---")
    for room in st.session_state.rooms:
        rt = sum(len(v) for v in room["specbook"].values())
        if not rt: continue
        with st.expander(f"**{room['name']}** — {rt}개 자재", expanded=False):
            for ck, items in room["specbook"].items():
                if not items: continue
                meta = CATEGORY_META[ck]
                names = " · ".join(it["name"][:18] for it in items[:3])
                st.markdown(
                    f'<span class="badge">{meta["icon"]} {ck}</span>&nbsp;'
                    f'{names}{"…" if len(items)>3 else ""}',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    if st.session_state.pptx_bytes is None:
        if st.button("▶ 지금 생성하기", type="primary", key="gen_now"):
            ppt_rooms = []
            for room in st.session_state.rooms:
                all_items = [
                    {"item_code": it["item_code"], "product": it["name"],
                     "brand": it.get("brand","") or it.get("brand_name",""),
                     "spec": it.get("size",""),
                     "finish": it.get("material","") or it.get("color",""),
                     "vendor": it.get("supplier",""), "qty": it.get("qty",1),
                     "note": it.get("memo",""), "price": it["price"],
                     "image_url": it.get("image_url",""),
                     "location": it.get("location",""),
                     "color": it.get("color",""), "material": it.get("material",""),
                     "room": room["name"]}
                    for its in room["specbook"].values() for it in its
                ]
                if all_items:
                    model_images = []
                    for vi in range(4):
                        uf = st.session_state.get(f"model_img_{room['id']}_{vi}")
                        model_images.append(uf.read() if uf else None)
                    ppt_rooms.append({"name": room["name"], "name_en": room["name_en"],
                                      "items": all_items, "model_images": model_images})
            with st.spinner("PPT 생성 중..."):
                st.session_state.pptx_bytes = generate_pptx(
                    p, ppt_rooms, logo_bytes=st.session_state.logo_bytes)
            st.success("✓ 생성 완료! 사이드바 하단에서 다운로드하세요.")
            st.rerun()
    else:
        st.success("✓ PPT가 준비됐습니다. 사이드바 하단 **⬇️ PPT 다운로드** 버튼을 클릭하세요.")
        if st.button("↩ 작업으로 돌아가기", key="back_ws"):
            st.session_state.view = "workspace"; st.rerun()

    st.stop()

# ── Workspace 뷰 ─────────────────────────────────────────────────────────────

if not st.session_state.rooms:
    st.markdown("""
    <div style='text-align:center;padding:80px 20px;color:#9A8F86;'>
      <div style='font-size:3rem;margin-bottom:16px'>🏠</div>
      <div style='font-size:1.1rem;font-weight:700;color:#4A4540;margin-bottom:8px'>
        사이드바에서 공간을 추가해 시작하세요</div>
      <div style='font-size:.84rem'>거실·침실·욕실 등 공간을 추가하면 자재 검색이 활성화됩니다.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

room = _active_room()
if room is None:
    room = st.session_state.rooms[0]
    st.session_state.active_rid = room["id"]

sel = room.setdefault("sel", _init_sel())
ri  = next(i for i, r in enumerate(st.session_state.rooms) if r["id"] == room["id"])
total_room = sum(len(v) for v in room["specbook"].values())

# 방 헤더
st.markdown(
    f'<div style="background:#fff;border:1px solid #EAE5DF;border-radius:12px;'
    f'padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'
    f'box-shadow:0 1px 4px rgba(0,0,0,.05);">'
    f'<span style="font-size:1rem;font-weight:700;color:#1A1816">{room["name"]}</span>'
    f'<span style="font-size:.76rem;color:#9A8F86">{room["name_en"]}</span>'
    f'<span style="margin-left:auto;font-size:.74rem;color:#C8A97E;font-weight:700">'
    f'{total_room}개 자재</span></div>',
    unsafe_allow_html=True,
)

# 2-컬럼 레이아웃
col_search, col_mat = st.columns([57, 43], gap="large")

# ═══════════════════════════════════════════════════
# 왼쪽: 검색 패널
# ═══════════════════════════════════════════════════
with col_search:

    # 단계 표시 바
    s1 = "active" if not sel["cat"]   else "done"
    s2 = "active" if sel["cat"] and not sel["brand"]  else ("done" if sel["brand"] else "")
    s3 = "active" if sel["brand"] and not sel["group"] else ("done" if sel["group"] else "")
    s4 = "active" if sel["group"] or sel["cat"] == "__fav__" else ""
    st.markdown(f"""
    <div class="stepbar">
      <div class="step {s1}">① 카테고리</div>
      <div class="step {s2}">② 업체</div>
      <div class="step {s3}">③ 제품군</div>
      <div class="step {s4}">④ 검색결과</div>
    </div>""", unsafe_allow_html=True)

    # 탭: 카테고리 검색 | 즐겨찾기 | 직접입력
    tab_search, tab_fav, tab_manual = st.tabs(["🔍 카테고리 검색", f"⭐ 즐겨찾기 ({len(st.session_state.favorites)})", "✏ 직접 입력"])

    # ── 카테고리 검색 탭 ────────────────────────────────────────────────
    with tab_search:
        # STEP 1: 카테고리
        st.markdown('<span class="slabel">① 카테고리 선택</span>', unsafe_allow_html=True)
        cat_cols = st.columns(4)
        for ci, ck in enumerate(CAT_KEYS):
            meta = CATEGORY_META[ck]
            is_active = sel["cat"] == ck
            with cat_cols[ci % 4]:
                if st.button(f"{meta['icon']} {ck}", key=f"cat_{ri}_{ck}",
                             use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    if sel["cat"] != ck:
                        sel.update({"cat": ck, "brand": None, "group": None})
                        st.session_state.pop(f"res_{ri}", None)
                    else:
                        sel.update({"cat": None, "brand": None, "group": None})
                        st.session_state.pop(f"res_{ri}", None)
                    st.rerun()

        if not sel["cat"]:
            st.info("카테고리를 선택하면 관련 업체 목록이 표시됩니다.", icon="ℹ️")
            st.stop()

        # STEP 2: 업체
        st.markdown('<span class="slabel">② 업체 / 브랜드</span>', unsafe_allow_html=True)
        brands = BRAND_CATALOG[sel["cat"]]
        brand_cols = st.columns(3)
        for bi, b in enumerate(brands):
            is_active = sel["brand"] == b["name"]
            with brand_cols[bi % 3]:
                if st.button(b["name"], key=f"brand_{ri}_{bi}",
                             use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    if sel["brand"] != b["name"]:
                        sel.update({"brand": b["name"], "group": None})
                        st.session_state.pop(f"res_{ri}", None)
                    else:
                        sel.update({"brand": None, "group": None})
                        st.session_state.pop(f"res_{ri}", None)
                    st.rerun()

        if not sel["brand"]:
            st.stop()

        # STEP 3: 제품군
        brand_data = next((b for b in brands if b["name"] == sel["brand"]), None)
        groups = brand_data["groups"] if brand_data else []
        if groups:
            st.markdown('<span class="slabel">③ 제품군</span>', unsafe_allow_html=True)
            grp_cols = st.columns(4)
            for gi, g in enumerate(groups):
                is_active = sel["group"] == g
                with grp_cols[gi % 4]:
                    if st.button(g, key=f"grp_{ri}_{gi}",
                                 use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        sel["group"] = None if is_active else g
                        st.session_state.pop(f"res_{ri}", None)
                        if sel["group"]:
                            with st.spinner(f"{sel['brand']} {sel['group']} 검색 중..."):
                                st.session_state[f"res_{ri}"] = search_products(
                                    brand=sel["brand"], category=sel["cat"],
                                    product_group=sel["group"], keyword="", count=50)
                            st.session_state[f"page_{ri}"] = 0
                        st.rerun()

        # STEP 4: 검색창
        st.markdown('<span class="slabel">④ 검색</span>', unsafe_allow_html=True)
        qc, bc = st.columns([5, 1])
        with qc:
            keyword = st.text_input("검색어", key=f"kw_{ri}",
                placeholder=f"{sel['group'] or '제품군 선택 또는'} 키워드 입력 (예: 베이지, 방염)",
                label_visibility="collapsed")
        with bc:
            do_search = st.button("검색", key=f"sb_{ri}", use_container_width=True, type="primary")

        if do_search:
            if not sel["group"] and not keyword.strip():
                st.warning("제품군을 선택하거나 검색어를 입력하세요.")
            else:
                with st.spinner("검색 중..."):
                    st.session_state[f"res_{ri}"] = search_products(
                        brand=sel["brand"], category=sel["cat"],
                        product_group=sel["group"] or "", keyword=keyword.strip(), count=50)
                st.session_state[f"page_{ri}"] = 0

        # 검색 결과
        products = st.session_state.get(f"res_{ri}", [])
        page     = st.session_state.get(f"page_{ri}", 0)
        PAGE_SIZE = 8

        if products:
            existing_urls = {it["source_url"] for its in room["specbook"].values() for it in its}
            fav_urls = {f["url"] for f in st.session_state.favorites}

            SORT_OPTS = {"인기순": None, "가격↑": lambda x: x["price_int"],
                         "가격↓": lambda x: -x["price_int"]}
            rc1, rc2, rc3, rc4, rc5 = st.columns([2, 2, 1, 1, 1])
            with rc1: st.markdown(f"<span style='font-size:.72rem;color:#9A8F86'>{len(products)}개 결과</span>", unsafe_allow_html=True)
            with rc2:
                sort_key = st.selectbox("정렬", list(SORT_OPTS.keys()),
                                        key=f"sort_{ri}", label_visibility="collapsed")
            total_pages = max(1, -(-len(products) // PAGE_SIZE))
            with rc3:
                st.markdown(f"<div style='text-align:center;font-size:.7rem;color:#9A8F86;padding-top:8px'>{page+1}/{total_pages}</div>",
                            unsafe_allow_html=True)
            with rc4:
                if st.button("◀", key=f"prev_{ri}", disabled=(page==0), use_container_width=True):
                    st.session_state[f"page_{ri}"] = page-1; st.rerun()
            with rc5:
                if st.button("▶", key=f"next_{ri}", disabled=(page>=total_pages-1), use_container_width=True):
                    st.session_state[f"page_{ri}"] = page+1; st.rerun()

            sort_fn = SORT_OPTS[sort_key]
            sorted_products = sorted(products, key=sort_fn) if sort_fn else products
            page_items = sorted_products[page*PAGE_SIZE:(page+1)*PAGE_SIZE]

            for pi, prod in enumerate(page_items):
                gpi = page * PAGE_SIZE + pi
                is_dup = prod["url"] in existing_urls
                is_fav = prod["url"] in fav_urls
                ic, inf, ac = st.columns([1, 5, 2])
                with ic:
                    if prod["image"]:
                        st.image(prod["image"], use_container_width=True)
                with inf:
                    st.markdown(
                        f'<div class="pcard-title">{prod["title"][:46]}</div>'
                        f'<div class="pcard-price">{prod["price"]}</div>'
                        f'<div class="pcard-meta">{prod["brand"] or sel["brand"]} | {prod["mall"] or "—"}</div>',
                        unsafe_allow_html=True,
                    )
                    if prod["url"]:
                        st.markdown(f"[🔗 링크]({prod['url']})", unsafe_allow_html=False)
                with ac:
                    fav_icon = "⭐" if is_fav else "☆"
                    if st.button(fav_icon, key=f"fav_{ri}_{gpi}", help="즐겨찾기"):
                        if is_fav:
                            st.session_state.favorites = [f for f in st.session_state.favorites if f["url"] != prod["url"]]
                        else:
                            st.session_state.favorites.append({**prod, "cat": sel["cat"],
                                "brand_name": sel["brand"], "product_group": sel["group"] or ""})
                        st.rerun()
                    if is_dup:
                        st.markdown("<span style='font-size:.65rem;color:#9A8F86'>✓ 추가됨</span>", unsafe_allow_html=True)
                    else:
                        if st.button("＋", key=f"add_{ri}_{gpi}", use_container_width=True, type="primary"):
                            meta = CATEGORY_META[sel["cat"]]
                            room["specbook"][sel["cat"]].append({
                                "id": str(uuid.uuid4())[:8], "category": sel["cat"],
                                "brand_name": sel["brand"], "product_group": sel["group"] or "",
                                "name": prod["title"], "brand": prod["brand"] or sel["brand"],
                                "maker": prod["maker"] or "", "supplier": prod["mall"] or "",
                                "price": prod["price"], "price_int": prod["price_int"],
                                "image_url": prod["image"], "source_url": prod["url"],
                                "material": "", "color": "", "size": _extract_spec(prod["title"]),
                                "model_number": "", "unit": "EA", "qty": 1,
                                "location": "", "memo": "", "item_code": meta["item_code"],
                                "is_common": False,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                            st.rerun()
                st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:3px 0'>", unsafe_allow_html=True)

        elif f"res_{ri}" in st.session_state:
            st.warning("검색 결과가 없습니다. 다른 업체나 키워드를 시도해보세요.")

    # ── 즐겨찾기 탭 ─────────────────────────────────────────────────────
    with tab_fav:
        favs = st.session_state.favorites
        if not favs:
            st.info("검색 결과에서 ☆ 버튼으로 즐겨찾기를 추가하세요.", icon="⭐")
        else:
            existing_urls = {it["source_url"] for its in room["specbook"].values() for it in its}
            for fi, fav in enumerate(favs):
                ck = fav.get("cat", "")
                meta = CATEGORY_META.get(ck, {"icon": "📦", "item_code": ck})
                is_dup = fav["url"] in existing_urls
                fc1, fc2, fc3 = st.columns([1, 5, 2])
                with fc1:
                    if fav.get("image"): st.image(fav["image"], use_container_width=True)
                with fc2:
                    st.markdown(
                        f'<div class="pcard-title">{fav["title"][:44]}</div>'
                        f'<div class="pcard-price">{fav["price"]}</div>'
                        f'<div class="pcard-meta"><span class="badge">{meta["icon"]} {ck}</span>'
                        f' {fav.get("brand_name","")}</div>',
                        unsafe_allow_html=True,
                    )
                with fc3:
                    if st.button("⭐", key=f"unfav_{ri}_{fi}", help="즐겨찾기 해제"):
                        st.session_state.favorites.pop(fi); st.rerun()
                    if is_dup:
                        st.caption("✓ 추가됨")
                    elif ck:
                        if st.button("＋ 추가", key=f"favadd_{ri}_{fi}",
                                     use_container_width=True, type="primary"):
                            room["specbook"][ck].append({
                                "id": str(uuid.uuid4())[:8], "category": ck,
                                "brand_name": fav.get("brand_name",""),
                                "product_group": fav.get("product_group",""),
                                "name": fav["title"], "brand": fav["brand"] or fav.get("brand_name",""),
                                "maker": fav.get("maker",""), "supplier": fav.get("mall",""),
                                "price": fav["price"], "price_int": fav["price_int"],
                                "image_url": fav.get("image",""), "source_url": fav["url"],
                                "material": "", "color": "", "size": _extract_spec(fav["title"]),
                                "model_number": "", "unit": "EA", "qty": 1, "location": "", "memo": "",
                                "item_code": meta["item_code"], "is_common": False,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                            st.rerun()
                st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:3px 0'>", unsafe_allow_html=True)

    # ── 직접 입력 탭 ─────────────────────────────────────────────────────
    with tab_manual:
        m_cat = st.selectbox("카테고리", CAT_KEYS, key=f"mcat_{ri}")
        mc1, mc2 = st.columns(2)
        with mc1:
            m_name  = st.text_input("제품명 *",    key=f"mname_{ri}")
            m_brand = st.text_input("브랜드",      key=f"mbrand_{ri}")
            m_sup   = st.text_input("판매처",      key=f"msup_{ri}")
            m_price = st.text_input("가격",        key=f"mprice_{ri}", placeholder="50,000원")
        with mc2:
            m_size  = st.text_input("규격",        key=f"msize_{ri}")
            m_color = st.text_input("색상",        key=f"mcolor_{ri}")
            m_mat   = st.text_input("재질",        key=f"mmat_{ri}")
            m_model = st.text_input("품번",        key=f"mmodel_{ri}")
        m_loc  = st.text_input("적용 위치",  key=f"mloc_{ri}", placeholder="예: 거실 벽면")
        m_memo = st.text_area("비고",        key=f"mmemo_{ri}", height=52)
        if st.button("＋ 추가", key=f"madd_{ri}", type="primary"):
            if not m_name.strip():
                st.warning("제품명을 입력하세요.")
            else:
                meta_m = CATEGORY_META[m_cat]
                try:    p_int = int("".join(c for c in m_price if c.isdigit()))
                except: p_int = 0
                room["specbook"][m_cat].append({
                    "id": str(uuid.uuid4())[:8], "category": m_cat,
                    "brand_name": m_brand, "product_group": "",
                    "name": m_name.strip(), "brand": m_brand, "maker": "",
                    "supplier": m_sup, "price": m_price or "0원", "price_int": p_int,
                    "image_url": "", "source_url": "", "material": m_mat,
                    "color": m_color, "size": m_size, "model_number": m_model,
                    "unit": "EA", "qty": 1, "location": m_loc, "memo": m_memo,
                    "item_code": meta_m["item_code"], "is_common": False,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                st.success(f"'{m_name}' 추가 완료!")
                st.rerun()

# ═══════════════════════════════════════════════════
# 오른쪽: 자재 목록
# ═══════════════════════════════════════════════════
with col_mat:
    room_price = sum(it.get("price_int",0)*it.get("qty",1)
                     for its in room["specbook"].values() for it in its)
    hc1, hc2 = st.columns([3,2])
    with hc1:
        st.markdown('<span class="slabel">추가된 자재</span>', unsafe_allow_html=True)
    with hc2:
        if room_price:
            st.markdown(
                f'<div style="text-align:right;color:#C8A97E;font-size:.72rem;font-weight:700;padding-top:14px">'
                f'{room_price:,}원</div>', unsafe_allow_html=True)

    if total_room == 0:
        st.markdown(
            '<div style="text-align:center;padding:40px 0;color:#B0A89E;font-size:.82rem">'
            '왼쪽에서 자재를 추가하세요</div>', unsafe_allow_html=True)
    else:
        for ck in CAT_KEYS:
            items = room["specbook"][ck]
            if not items: continue
            meta = CATEGORY_META[ck]
            st.markdown(
                f'<span class="badge">{meta["icon"]} {ck} {len(items)}</span>',
                unsafe_allow_html=True)
            for ii, item in enumerate(items):
                with st.container():
                    st.markdown('<div class="mat-card">', unsafe_allow_html=True)
                    # 이름 + 액션 버튼
                    nc1, nc2 = st.columns([6, 2])
                    with nc1:
                        st.markdown(
                            f'<div class="mat-name">{item["name"][:28]}</div>'
                            f'<div class="mat-price">{item["price"]}'
                            f'{"  ×"+str(item["qty"]) if item.get("qty",1)>1 else ""}</div>'
                            f'<div class="mat-meta">{item.get("brand_name","")}'
                            f'{(" › "+item["product_group"]) if item.get("product_group") else ""}</div>',
                            unsafe_allow_html=True)
                    with nc2:
                        # 수량 인라인 버튼
                        qty = item.get("qty", 1)
                        qa, qb, qc = st.columns([1,1,1])
                        with qa:
                            if st.button("−", key=f"qm_{ri}_{ck}_{ii}",
                                         disabled=(qty<=1)):
                                item["qty"] = max(1, qty-1); st.rerun()
                        with qb:
                            st.markdown(f"<div style='text-align:center;font-size:.76rem;font-weight:700;padding-top:6px'>{qty}</div>", unsafe_allow_html=True)
                        with qc:
                            if st.button("＋", key=f"qp_{ri}_{ck}_{ii}"):
                                item["qty"] = qty+1; st.rerun()

                    # 액션 행
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        item_url = item.get("source_url","")
                        fav_urls_r = {f["url"] for f in st.session_state.favorites}
                        is_fav_r   = bool(item_url and item_url in fav_urls_r)
                        if st.button("⭐" if is_fav_r else "☆",
                                     key=f"favr_{ri}_{ck}_{ii}", use_container_width=True):
                            if is_fav_r:
                                st.session_state.favorites = [f for f in st.session_state.favorites if f["url"] != item_url]
                            else:
                                st.session_state.favorites.append({
                                    "url": item_url, "title": item["name"],
                                    "price": item["price"], "price_int": item.get("price_int",0),
                                    "brand": item.get("brand",""), "maker": item.get("maker",""),
                                    "mall": item.get("supplier",""), "image": item.get("image_url",""),
                                    "cat": ck, "brand_name": item.get("brand_name",""),
                                    "product_group": item.get("product_group",""),
                                })
                            st.rerun()
                    with ac2:
                        if st.button("✏", key=f"edit_{ri}_{ck}_{ii}", use_container_width=True):
                            key_e = f"expand_{ri}_{ck}_{ii}"
                            st.session_state[key_e] = not st.session_state.get(key_e, False)
                            st.rerun()
                    with ac3:
                        if st.button("🗑", key=f"del_{ri}_{ck}_{ii}", use_container_width=True):
                            room["specbook"][ck].pop(ii); st.rerun()

                    # 편집 패널 (토글)
                    if st.session_state.get(f"expand_{ri}_{ck}_{ii}", False):
                        st.markdown("<hr style='margin:6px 0;border-color:#F0EBE4'>", unsafe_allow_html=True)
                        e1, e2 = st.columns(2)
                        with e1:
                            item["name"]     = st.text_input("제품명",  item["name"],     key=f"en_{ri}_{ck}_{ii}")
                            item["brand"]    = st.text_input("브랜드",  item["brand"],    key=f"eb_{ri}_{ck}_{ii}")
                            item["supplier"] = st.text_input("판매처",  item["supplier"], key=f"es_{ri}_{ck}_{ii}")
                            item["price"]    = st.text_input("가격",    item["price"],    key=f"ep_{ri}_{ck}_{ii}")
                        with e2:
                            item["size"]         = st.text_input("규격",  item.get("size",""),         key=f"esz_{ri}_{ck}_{ii}")
                            item["color"]        = st.text_input("색상",  item.get("color",""),        key=f"ec_{ri}_{ck}_{ii}")
                            item["material"]     = st.text_input("재질",  item.get("material",""),     key=f"em_{ri}_{ck}_{ii}")
                            item["model_number"] = st.text_input("품번",  item.get("model_number",""), key=f"emn_{ri}_{ck}_{ii}")
                        item["location"] = st.text_input("적용 위치", item.get("location",""),
                                           placeholder="예: 거실 벽면", key=f"el_{ri}_{ck}_{ii}")
                        item["memo"]     = st.text_area("비고", item.get("memo",""),
                                           key=f"emm_{ri}_{ck}_{ii}", height=52)
                        if item.get("source_url"):
                            st.markdown(f"[🔗 상품 페이지]({item['source_url']})")
                        # 방 간 복사
                        other_rooms = [r for r in st.session_state.rooms if r["id"] != room["id"]]
                        if other_rooms:
                            cp1, cp2 = st.columns([3,1])
                            with cp1:
                                copy_target = st.selectbox("다른 공간으로 복사",
                                    [r["name"] for r in other_rooms],
                                    key=f"cptgt_{ri}_{ck}_{ii}", label_visibility="collapsed")
                            with cp2:
                                if st.button("복사", key=f"cp_{ri}_{ck}_{ii}", use_container_width=True):
                                    tgt = next(r for r in other_rooms if r["name"] == copy_target)
                                    new_it = _copy.deepcopy(item)
                                    new_it["id"] = str(uuid.uuid4())[:8]
                                    new_it["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                    tgt["specbook"][ck].append(new_it)
                                    st.success(f"'{copy_target}'에 복사 완료!")
                                    st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)

    # 모델링 이미지 (하단)
    st.markdown("---")
    with st.expander("🖼 모델링 이미지 (VIEW 01–04)", expanded=False):
        st.caption("PPT에 삽입할 렌더링 이미지 (각 VIEW 박스)")
        ic1, ic2 = st.columns(2)
        for vi in range(4):
            with (ic1 if vi % 2 == 0 else ic2):
                key = f"model_img_{room['id']}_{vi}"
                uf  = st.file_uploader(f"VIEW {vi+1:02d}", type=["png","jpg","jpeg"], key=key)
                if uf:
                    st.image(uf, use_container_width=True)
