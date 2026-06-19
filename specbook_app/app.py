"""
인테리어 스펙북 생성기 v5
구조: 탭(공간) + 사이드바(프로젝트/JSON) + 상단 PPT 버튼
"""
import re, uuid, json, copy as _copy
import streamlit as st
from datetime import datetime
from brands import BRAND_CATALOG, CATEGORY_META
from naver_shopping import search_products
from pptx_generator import generate_pptx

st.set_page_config(page_title="INTERIOR SPEC BOOK", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")

CAT_KEYS = list(BRAND_CATALOG.keys())

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;}
.stApp{background:#F4F2EE;}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent!important;height:0!important;}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"]{
  background:#EDEAE5;padding:3px;border-radius:10px;gap:2px;flex-wrap:nowrap;overflow-x:auto;}
.stTabs [data-baseweb="tab"]{
  border-radius:7px;font-weight:600;font-size:.76rem;padding:5px 11px;
  color:#6B6059!important;white-space:nowrap;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;}

/* ── 일반 버튼 ── */
.stButton>button{
  border-radius:8px!important;font-size:.76rem!important;font-weight:600!important;
  background:#fff!important;color:#4A4540!important;border:1.5px solid #DDD8D2!important;
  transition:.12s!important;}
.stButton>button:hover{
  background:#FDF8F2!important;border-color:#C8A97E!important;color:#1A1816!important;}
div[data-testid="stButton"]>button[kind="primary"]{
  background:#1A1816!important;color:#C8A97E!important;border-color:#1A1816!important;}
div[data-testid="stButton"]>button[kind="primary"]:hover{
  background:#C8A97E!important;color:#1A1816!important;}

/* ── 사이드바 ── */
section[data-testid="stSidebar"]{background:#1A1816!important;}
section[data-testid="stSidebar"] *{color:#C8C0B8!important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea{
  background:#252220!important;border:1px solid #383230!important;
  color:#E0DAD4!important;border-radius:6px!important;}
section[data-testid="stSidebar"] label{color:#7A7068!important;font-size:.70rem!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:#252220!important;border:1px solid #383230!important;
  color:#C0B8B0!important;border-radius:8px!important;font-size:.74rem!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  border-color:#C8A97E!important;color:#C8A97E!important;}
section[data-testid="stSidebar"] div[data-testid="stButton"]>button[kind="primary"]{
  background:#C8A97E!important;color:#1A1816!important;border-color:#C8A97E!important;font-weight:700!important;}

/* ── 스텝바 ── */
.stepbar{display:flex;margin-bottom:12px;border-radius:8px;overflow:hidden;border:1.5px solid #DDD8D2;}
.step{flex:1;padding:6px 4px;font-size:.66rem;font-weight:700;text-align:center;
      background:#F8F6F2;color:#A09890;}
.step+.step{border-left:1px solid #DDD8D2;}
.step.done{background:#F0EBE4;color:#7A6E68;}
.step.active{background:#1A1816;color:#C8A97E;}

/* ── 섹션 레이블 ── */
.slabel{font-size:.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
        color:#C8A97E;display:block;margin:10px 0 5px;}

/* ── 상품 카드 ── */
.pcard-title{font-size:.80rem;font-weight:700;color:#1A1816;line-height:1.35;margin-bottom:2px;}
.pcard-price{font-size:.82rem;font-weight:700;color:#C8A97E;}
.pcard-meta{font-size:.63rem;color:#9A8F86;}

/* ── 자재 카드 ── */
.mat-card{background:#fff;border:1px solid #EAE5DF;border-radius:10px;
          padding:9px 10px;margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
.mat-name{font-size:.78rem;font-weight:700;color:#1A1816;line-height:1.3;
          overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;}
.mat-meta{font-size:.63rem;color:#9A8F86;margin-top:2px;}
.mat-price{font-size:.72rem;font-weight:700;color:#C8A97E;}

/* ── 배지 ── */
.badge{display:inline-block;padding:2px 7px;border-radius:10px;
       font-size:.60rem;font-weight:700;background:#EDE8E0;color:#5A4E44;margin-bottom:5px;}

/* ── PPT 배너 ── */
.ppt-banner{background:#1A1816;border-radius:10px;padding:12px 16px;
            margin-bottom:14px;display:flex;align-items:center;gap:12px;}
.ppt-banner-txt{color:#C8A97E;font-size:.78rem;font-weight:700;flex:1;}
.ppt-banner-sub{color:#7A7068;font-size:.65rem;}
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def _init_specbook(): return {k: [] for k in CAT_KEYS}
def _init_sel():      return {"cat": None, "brand": None, "group": None}

_defaults = {
    "rooms": [], "favorites": [], "logo_bytes": None,
    "project": {
        "company": "DESICODE", "name": "○○ 아파트 리모델링",
        "location": "서울시 강남구", "area": "84㎡ (25.4평)",
        "period": "2026.07 ~ 2026.08", "designer": "홍길동",
        "date": datetime.now().strftime("%Y.%m.%d"),
    },
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

p = st.session_state.project

ROOM_PRESETS = [
    ("거실","Living Room","🛋"),("침실","Bedroom","🛏"),("주방","Kitchen","🍳"),
    ("욕실","Bathroom","🚿"),("현관","Entrance","🚪"),("드레스룸","Dressing Room","👗"),
    ("서재","Study Room","📚"),("다이닝","Dining Room","🍽"),
    ("복도","Hallway","🔲"),("발코니","Balcony","🌿"),
]

def _add_room(ko, en):
    same = sum(1 for r in st.session_state.rooms if r["name"].startswith(ko))
    name = f"{ko}{same+1}" if same else ko
    st.session_state.rooms.append({
        "id": str(uuid.uuid4())[:8], "name": name, "name_en": en,
        "specbook": _init_specbook(), "sel": _init_sel(),
    })
    st.rerun()

def _extract_spec(title):
    m = re.search(r'\d+(?:\.\d+)?[\s]*[×xX\*][\s]*\d+(?:\.\d+)?'
                  r'(?:[\s]*[×xX\*][\s]*\d+(?:\.\d+)?)?(?:[\s]*(?:mm|cm|m))?',
                  title, re.IGNORECASE)
    if m: return m.group().strip()
    m = re.search(r'\d+(?:\.\d+)?[\s]*(?:mm|cm|m²|㎡)', title, re.IGNORECASE)
    return m.group().strip() if m else ""

# ── 사이드바: 프로젝트 정보 + JSON ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 프로젝트")
    p["company"]  = st.text_input("회사명",    p.get("company",""),  key="si_co")
    p["name"]     = st.text_input("프로젝트명", p.get("name",""),    key="si_pj")
    p["location"] = st.text_input("위치",      p.get("location",""), key="si_lo")
    p["area"]     = st.text_input("면적",      p.get("area",""),     key="si_ar")
    p["period"]   = st.text_input("공사기간",  p.get("period",""),   key="si_pe")
    p["designer"] = st.text_input("담당자",    p.get("designer",""), key="si_de")
    p["date"]     = st.text_input("작성일",    p.get("date",""),     key="si_da")
    st.markdown("---")
    st.markdown("### 🖼 로고")
    logo_file = st.file_uploader("PNG/JPG", type=["png","jpg","jpeg"],
                                 key="logo_up", label_visibility="collapsed")
    if logo_file:
        st.session_state.logo_bytes = logo_file.read()
    if st.session_state.logo_bytes:
        st.image(st.session_state.logo_bytes, width=100)
        if st.button("제거", key="logo_clr"):
            st.session_state.logo_bytes = None; st.rerun()
    st.markdown("---")
    st.markdown("### 📂 파일")
    export_data = {
        "project": p, "favorites": st.session_state.favorites,
        "rooms": [{"name": r["name"], "name_en": r["name_en"],
                   "items": [it for its in r["specbook"].values() for it in its]}
                  for r in st.session_state.rooms],
    }
    st.download_button("📥 JSON 저장",
                       data=json.dumps(export_data, ensure_ascii=False, indent=2),
                       file_name=f"{p.get('name','spec')}_specbook.json",
                       mime="application/json", use_container_width=True)
    uploaded = st.file_uploader("JSON 불러오기", type="json", key="json_import",
                                label_visibility="collapsed")
    if uploaded and st.session_state.get("_last_json") != uploaded.name:
        st.session_state["_last_json"] = uploaded.name
        try:
            data = json.loads(uploaded.read())
            st.session_state.project   = data.get("project", p)
            st.session_state.favorites = data.get("favorites", [])
            st.session_state.rooms = []
            for r in data.get("rooms", []):
                sb = _init_specbook()
                for it in r.get("items", []):
                    cat = it.get("category","")
                    if cat in sb: sb[cat].append(it)
                st.session_state.rooms.append({
                    "id": str(uuid.uuid4())[:8], "name": r["name"],
                    "name_en": r.get("name_en",""), "specbook": sb, "sel": _init_sel(),
                })
            st.success("완료!"); st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

# ── 상단 헤더 ─────────────────────────────────────────────────────────────────
total_all = sum(len(it) for r in st.session_state.rooms for it in r["specbook"].values())
total_budget = sum(it.get("price_int",0)*it.get("qty",1)
                   for r in st.session_state.rooms
                   for its in r["specbook"].values() for it in its)

hc1, hc2 = st.columns([7, 3])
with hc1:
    st.markdown(
        f'<div style="background:#1A1816;border-radius:10px;padding:10px 18px;'
        f'display:flex;align-items:center;gap:10px;">'
        f'<span style="color:#fff;font-size:1rem;font-weight:700;letter-spacing:1px">'
        f'INTERIOR <span style="color:#C8A97E">SPEC BOOK</span></span>'
        f'<span style="color:#6B6059;font-size:.72rem;margin-left:auto">'
        f'공간 {len(st.session_state.rooms)}개 · 자재 {total_all}개 · {total_budget:,}원</span>'
        f'</div>', unsafe_allow_html=True)
with hc2:
    if st.button("🎨 PPT 스펙북 생성", type="primary",
                 use_container_width=True, disabled=total_all==0, key="ppt_top"):
        st.session_state["do_ppt"] = True

st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

# PPT 생성 처리
if st.session_state.get("do_ppt"):
    st.session_state["do_ppt"] = False
    ppt_rooms = []
    for room in st.session_state.rooms:
        all_items = [
            {"item_code": it["item_code"], "product": it["name"],
             "brand": it.get("brand","") or it.get("brand_name",""),
             "spec": it.get("size",""),
             "finish": it.get("material","") or it.get("color",""),
             "vendor": it.get("supplier",""), "qty": it.get("qty",1),
             "note": it.get("memo",""), "price": it["price"],
             "image_url": it.get("image_url",""), "location": it.get("location",""),
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
        pptx_bytes = generate_pptx(p, ppt_rooms, logo_bytes=st.session_state.logo_bytes)
    st.download_button("⬇️ PPT 다운로드", data=pptx_bytes,
                       file_name=f"{p.get('name','spec')}_스펙북.pptx",
                       mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                       use_container_width=False)
    st.success("✓ 생성 완료!")

# ── 탭 구성 ───────────────────────────────────────────────────────────────────
tab_labels = [r["name"] for r in st.session_state.rooms] + ["＋ 공간"]
tabs = st.tabs(tab_labels)

# ── 공간 추가 탭 ──────────────────────────────────────────────────────────────
with tabs[-1]:
    st.markdown("#### 공간 추가")
    cols = st.columns(5)
    for idx, (ko, en, icon) in enumerate(ROOM_PRESETS):
        with cols[idx % 5]:
            if st.button(f"{icon}  {ko}", key=f"pr_{ko}", use_container_width=True):
                _add_room(ko, en)
    st.markdown("---")
    c1, c2, c3 = st.columns([3,3,1])
    with c1: cko = st.text_input("공간명(한글)", placeholder="홈짐", key="cko")
    with c2: cen = st.text_input("공간명(영어)", placeholder="Home Gym", key="cen")
    with c3:
        st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
        if st.button("추가", key="cadd", type="primary", use_container_width=True) and cko:
            _add_room(cko, cen or cko)
        st.markdown("</div>", unsafe_allow_html=True)

# ── 각 방 탭 ──────────────────────────────────────────────────────────────────
for ri, (tab, room) in enumerate(zip(tabs[:-1], st.session_state.rooms)):
    with tab:
        sel = room.setdefault("sel", _init_sel())
        total_room = sum(len(v) for v in room["specbook"].values())

        # 방 헤더 (삭제 버튼 포함)
        rh1, rh2 = st.columns([8,2])
        with rh1:
            st.markdown(
                f'<div style="padding:8px 0;border-bottom:2px solid #1A1816;'
                f'display:flex;align-items:center;gap:10px;margin-bottom:12px">'
                f'<span style="font-size:.96rem;font-weight:700">{room["name"]}</span>'
                f'<span style="font-size:.74rem;color:#9A8F86">{room["name_en"]}</span>'
                f'<span style="margin-left:auto;font-size:.72rem;color:#C8A97E;font-weight:700">'
                f'{total_room}개 자재</span></div>',
                unsafe_allow_html=True)
        with rh2:
            if st.button(f"🗑 {room['name']} 삭제", key=f"rmv_{ri}"):
                st.session_state.rooms.pop(ri); st.rerun()

        # 메인 2열
        col_l, col_r = st.columns([55, 45], gap="large")

        # ═══ 왼쪽: 검색 ═══════════════════════════════════════════════════════
        with col_l:
            # 스텝 표시
            s1 = "active" if not sel["cat"]                        else "done"
            s2 = "active" if sel["cat"] and not sel["brand"]       else ("done" if sel["brand"] else "")
            s3 = "active" if sel["brand"] and not sel["group"]     else ("done" if sel["group"] else "")
            s4 = "active" if sel["group"] or f"res_{ri}" in st.session_state else ""
            st.markdown(
                f'<div class="stepbar">'
                f'<div class="step {s1}">① 카테고리</div>'
                f'<div class="step {s2}">② 업체</div>'
                f'<div class="step {s3}">③ 제품군</div>'
                f'<div class="step {s4}">④ 검색결과</div>'
                f'</div>', unsafe_allow_html=True)

            t_search, t_fav, t_manual = st.tabs([
                "🔍 검색", f"⭐ 즐겨찾기({len(st.session_state.favorites)})", "✏ 직접입력"])

            # ── 카테고리 검색 탭 ──────────────────────────────────────────────
            with t_search:
                # STEP 1
                st.markdown('<span class="slabel">① 카테고리</span>', unsafe_allow_html=True)
                cat_cols = st.columns(4)
                for ci, ck in enumerate(CAT_KEYS):
                    meta = CATEGORY_META[ck]
                    is_on = sel["cat"] == ck
                    with cat_cols[ci % 4]:
                        if st.button(f"{meta['icon']} {ck}", key=f"cat_{ri}_{ck}",
                                     use_container_width=True,
                                     type="primary" if is_on else "secondary"):
                            if is_on:
                                sel.update({"cat": None, "brand": None, "group": None})
                                st.session_state.pop(f"res_{ri}", None)
                            else:
                                sel.update({"cat": ck, "brand": None, "group": None})
                                st.session_state.pop(f"res_{ri}", None)
                            st.rerun()

                if not sel["cat"]:
                    st.info("카테고리를 선택하세요.", icon="ℹ️")
                else:
                    # STEP 2
                    st.markdown('<span class="slabel">② 업체 / 브랜드</span>', unsafe_allow_html=True)
                    brands = BRAND_CATALOG[sel["cat"]]
                    bc = st.columns(3)
                    for bi, b in enumerate(brands):
                        is_on = sel["brand"] == b["name"]
                        with bc[bi % 3]:
                            if st.button(b["name"], key=f"br_{ri}_{bi}",
                                         use_container_width=True,
                                         type="primary" if is_on else "secondary"):
                                if is_on:
                                    sel.update({"brand": None, "group": None})
                                    st.session_state.pop(f"res_{ri}", None)
                                else:
                                    sel.update({"brand": b["name"], "group": None})
                                    st.session_state.pop(f"res_{ri}", None)
                                st.rerun()

                    if sel["brand"]:
                        # STEP 3
                        brand_data = next((b for b in brands if b["name"] == sel["brand"]), None)
                        groups = brand_data["groups"] if brand_data else []
                        if groups:
                            st.markdown('<span class="slabel">③ 제품군</span>', unsafe_allow_html=True)
                            gc = st.columns(4)
                            for gi, g in enumerate(groups):
                                is_on = sel["group"] == g
                                with gc[gi % 4]:
                                    if st.button(g, key=f"grp_{ri}_{gi}",
                                                 use_container_width=True,
                                                 type="primary" if is_on else "secondary"):
                                        sel["group"] = None if is_on else g
                                        st.session_state.pop(f"res_{ri}", None)
                                        if sel["group"]:
                                            with st.spinner(f"{sel['brand']} {sel['group']} 검색 중..."):
                                                st.session_state[f"res_{ri}"] = search_products(
                                                    brand=sel["brand"], category=sel["cat"],
                                                    product_group=sel["group"], keyword="", count=50)
                                            st.session_state[f"page_{ri}"] = 0
                                        st.rerun()

                        # 검색창
                        st.markdown('<span class="slabel">④ 검색</span>', unsafe_allow_html=True)
                        qc, bc2 = st.columns([5,1])
                        with qc:
                            kw = st.text_input("검색어", key=f"kw_{ri}",
                                placeholder=f"{sel['group'] or '제품군 선택 또는'} 키워드 입력",
                                label_visibility="collapsed")
                        with bc2:
                            do_search = st.button("검색", key=f"sb_{ri}",
                                                  use_container_width=True, type="primary")
                        if do_search:
                            if not sel["group"] and not kw.strip():
                                st.warning("제품군을 선택하거나 검색어를 입력하세요.")
                            else:
                                with st.spinner("검색 중..."):
                                    st.session_state[f"res_{ri}"] = search_products(
                                        brand=sel["brand"], category=sel["cat"],
                                        product_group=sel["group"] or "", keyword=kw.strip(), count=50)
                                st.session_state[f"page_{ri}"] = 0

                        # 결과
                        products = st.session_state.get(f"res_{ri}", [])
                        page     = st.session_state.get(f"page_{ri}", 0)
                        PAGE_SZ  = 8
                        if products:
                            existing = {it["source_url"] for its in room["specbook"].values() for it in its}
                            fav_urls = {f["url"] for f in st.session_state.favorites}
                            SORT = {"인기순": None, "가격↑": lambda x: x["price_int"],
                                    "가격↓": lambda x: -x["price_int"]}
                            rc1,rc2,rc3,rc4 = st.columns([3,2,1,1])
                            with rc1: st.markdown(f"<span style='font-size:.70rem;color:#9A8F86'>{len(products)}개 결과</span>", unsafe_allow_html=True)
                            with rc2: sk = st.selectbox("정렬", list(SORT.keys()), key=f"sort_{ri}", label_visibility="collapsed")
                            total_pg = max(1, -(-len(products) // PAGE_SZ))
                            with rc3:
                                if st.button("◀", key=f"pv_{ri}", disabled=(page==0), use_container_width=True):
                                    st.session_state[f"page_{ri}"] = page-1; st.rerun()
                            with rc4:
                                if st.button("▶", key=f"nx_{ri}", disabled=(page>=total_pg-1), use_container_width=True):
                                    st.session_state[f"page_{ri}"] = page+1; st.rerun()

                            sfn = SORT[sk]
                            pg_items = (sorted(products,key=sfn) if sfn else products)[page*PAGE_SZ:(page+1)*PAGE_SZ]

                            for pi, prod in enumerate(pg_items):
                                gpi = page*PAGE_SZ+pi
                                is_dup = prod["url"] in existing
                                is_fav = prod["url"] in fav_urls
                                ic, inf, ac = st.columns([1,5,2])
                                with ic:
                                    if prod["image"]:
                                        st.image(prod["image"], use_container_width=True)
                                with inf:
                                    st.markdown(
                                        f'<div class="pcard-title">{prod["title"][:46]}</div>'
                                        f'<div class="pcard-price">{prod["price"]}</div>'
                                        f'<div class="pcard-meta">{prod["brand"] or sel["brand"]} | {prod["mall"] or "—"}</div>',
                                        unsafe_allow_html=True)
                                    if prod["url"]:
                                        st.markdown(f"[🔗 링크]({prod['url']})")
                                with ac:
                                    if st.button("⭐" if is_fav else "☆", key=f"fav_{ri}_{gpi}", help="즐겨찾기"):
                                        if is_fav:
                                            st.session_state.favorites = [f for f in st.session_state.favorites if f["url"]!=prod["url"]]
                                        else:
                                            st.session_state.favorites.append({**prod,"cat":sel["cat"],"brand_name":sel["brand"],"product_group":sel["group"] or ""})
                                        st.rerun()
                                    if is_dup:
                                        st.markdown("<span style='font-size:.65rem;color:#9A8F86'>✓ 추가됨</span>", unsafe_allow_html=True)
                                    else:
                                        if st.button("＋ 추가", key=f"add_{ri}_{gpi}",
                                                     use_container_width=True, type="primary"):
                                            meta = CATEGORY_META[sel["cat"]]
                                            room["specbook"][sel["cat"]].append({
                                                "id": str(uuid.uuid4())[:8], "category": sel["cat"],
                                                "brand_name": sel["brand"], "product_group": sel["group"] or "",
                                                "name": prod["title"], "brand": prod["brand"] or sel["brand"],
                                                "maker": prod["maker"] or "", "supplier": prod["mall"] or "",
                                                "price": prod["price"], "price_int": prod["price_int"],
                                                "image_url": prod["image"], "source_url": prod["url"],
                                                "material":"","color":"","size":_extract_spec(prod["title"]),
                                                "model_number":"","unit":"EA","qty":1,
                                                "location":"","memo":"","item_code":meta["item_code"],
                                                "is_common":False,
                                                "created_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            })
                                            st.rerun()
                                st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>", unsafe_allow_html=True)

                        elif f"res_{ri}" in st.session_state:
                            st.warning("검색 결과가 없습니다. 다른 업체나 키워드를 시도해보세요.")

            # ── 즐겨찾기 탭 ──────────────────────────────────────────────────
            with t_fav:
                favs = st.session_state.favorites
                if not favs:
                    st.info("검색 결과에서 ☆ 버튼으로 즐겨찾기를 추가하세요.", icon="⭐")
                else:
                    existing = {it["source_url"] for its in room["specbook"].values() for it in its}
                    for fi, fav in enumerate(favs):
                        ck = fav.get("cat","")
                        meta = CATEGORY_META.get(ck, {"icon":"📦","item_code":ck})
                        fc1,fc2,fc3 = st.columns([1,5,2])
                        with fc1:
                            if fav.get("image"): st.image(fav["image"], use_container_width=True)
                        with fc2:
                            st.markdown(
                                f'<div class="pcard-title">{fav["title"][:44]}</div>'
                                f'<div class="pcard-price">{fav["price"]}</div>'
                                f'<div class="pcard-meta"><span class="badge">{meta["icon"]} {ck}</span> {fav.get("brand_name","")}</div>',
                                unsafe_allow_html=True)
                        with fc3:
                            if st.button("⭐", key=f"ufav_{ri}_{fi}", help="해제"):
                                st.session_state.favorites.pop(fi); st.rerun()
                            if fav["url"] in existing:
                                st.caption("✓ 추가됨")
                            elif ck:
                                if st.button("＋ 추가", key=f"fadd_{ri}_{fi}",
                                             use_container_width=True, type="primary"):
                                    room["specbook"][ck].append({
                                        "id":str(uuid.uuid4())[:8],"category":ck,
                                        "brand_name":fav.get("brand_name",""),"product_group":fav.get("product_group",""),
                                        "name":fav["title"],"brand":fav["brand"] or fav.get("brand_name",""),
                                        "maker":fav.get("maker",""),"supplier":fav.get("mall",""),
                                        "price":fav["price"],"price_int":fav["price_int"],
                                        "image_url":fav.get("image",""),"source_url":fav["url"],
                                        "material":"","color":"","size":_extract_spec(fav["title"]),
                                        "model_number":"","unit":"EA","qty":1,"location":"","memo":"",
                                        "item_code":meta["item_code"],"is_common":False,
                                        "created_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    })
                                    st.rerun()
                        st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>", unsafe_allow_html=True)

            # ── 직접 입력 탭 ─────────────────────────────────────────────────
            with t_manual:
                m_cat = st.selectbox("카테고리", CAT_KEYS, key=f"mcat_{ri}")
                m1,m2 = st.columns(2)
                with m1:
                    m_name  = st.text_input("제품명 *",  key=f"mn_{ri}")
                    m_brand = st.text_input("브랜드",    key=f"mb_{ri}")
                    m_sup   = st.text_input("판매처",    key=f"ms_{ri}")
                    m_price = st.text_input("가격",      key=f"mp_{ri}", placeholder="50,000원")
                with m2:
                    m_size  = st.text_input("규격",      key=f"msz_{ri}")
                    m_color = st.text_input("색상",      key=f"mc_{ri}")
                    m_mat   = st.text_input("재질",      key=f"mm_{ri}")
                    m_model = st.text_input("품번",      key=f"mmd_{ri}")
                m_loc  = st.text_input("적용 위치", key=f"ml_{ri}", placeholder="예: 거실 벽면")
                m_memo = st.text_area("비고",       key=f"mmo_{ri}", height=52)
                if st.button("＋ 추가", key=f"madd_{ri}", type="primary"):
                    if not m_name.strip():
                        st.warning("제품명을 입력하세요.")
                    else:
                        meta_m = CATEGORY_META[m_cat]
                        try: p_int = int("".join(c for c in m_price if c.isdigit()))
                        except: p_int = 0
                        room["specbook"][m_cat].append({
                            "id":str(uuid.uuid4())[:8],"category":m_cat,
                            "brand_name":m_brand,"product_group":"",
                            "name":m_name.strip(),"brand":m_brand,"maker":"","supplier":m_sup,
                            "price":m_price or "0원","price_int":p_int,
                            "image_url":"","source_url":"","material":m_mat,"color":m_color,
                            "size":m_size,"model_number":m_model,"unit":"EA","qty":1,
                            "location":m_loc,"memo":m_memo,"item_code":meta_m["item_code"],
                            "is_common":False,"created_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
                        })
                        st.success(f"'{m_name}' 추가 완료!"); st.rerun()

        # ═══ 오른쪽: 자재 목록 ═══════════════════════════════════════════════
        with col_r:
            room_price = sum(it.get("price_int",0)*it.get("qty",1)
                             for its in room["specbook"].values() for it in its)
            lh1, lh2 = st.columns([3,2])
            with lh1:
                st.markdown('<span class="slabel">추가된 자재</span>', unsafe_allow_html=True)
            with lh2:
                if room_price:
                    st.markdown(
                        f'<div style="text-align:right;color:#C8A97E;font-size:.72rem;'
                        f'font-weight:700;padding-top:14px">{room_price:,}원</div>',
                        unsafe_allow_html=True)

            if total_room == 0:
                st.markdown(
                    '<div style="text-align:center;padding:30px 0;color:#B0A89E;font-size:.82rem">'
                    '왼쪽에서 자재를 추가하세요</div>', unsafe_allow_html=True)

            for ck in CAT_KEYS:
                items = room["specbook"][ck]
                if not items: continue
                meta = CATEGORY_META[ck]
                st.markdown(f'<span class="badge">{meta["icon"]} {ck} {len(items)}</span>',
                            unsafe_allow_html=True)
                for ii, item in enumerate(items):
                    # 카드
                    img_col, info_col = st.columns([1, 3])
                    with img_col:
                        if item.get("image_url"):
                            st.image(item["image_url"], use_container_width=True)
                        else:
                            st.markdown(
                                f'<div style="width:100%;aspect-ratio:1;background:#F0EDE8;'
                                f'border-radius:8px;display:flex;align-items:center;'
                                f'justify-content:center;font-size:1.4rem">{meta["icon"]}</div>',
                                unsafe_allow_html=True)
                    with info_col:
                        qty = item.get("qty",1)
                        st.markdown(
                            f'<div class="mat-name">{item["name"][:36]}</div>'
                            f'<div class="mat-price">{item["price"]}'
                            f'{"  ×"+str(qty) if qty>1 else ""}</div>'
                            f'<div class="mat-meta">{item.get("brand_name","")}'
                            f'{(" › "+item["product_group"]) if item.get("product_group") else ""}</div>',
                            unsafe_allow_html=True)
                        # 수량 + 액션
                        qa,qb,qc,sep,da,ea,fa = st.columns([1,1,1,0.2,1,1,1])
                        with qa:
                            if st.button("−", key=f"qm_{ri}_{ck}_{ii}", disabled=(qty<=1)):
                                item["qty"]=max(1,qty-1); st.rerun()
                        with qb:
                            st.markdown(f"<div style='text-align:center;font-size:.78rem;font-weight:700;padding-top:5px'>{qty}</div>", unsafe_allow_html=True)
                        with qc:
                            if st.button("＋", key=f"qp_{ri}_{ck}_{ii}"):
                                item["qty"]=qty+1; st.rerun()
                        with da:
                            fav_urls_r={f["url"] for f in st.session_state.favorites}
                            iu=item.get("source_url","")
                            is_fv=bool(iu and iu in fav_urls_r)
                            if st.button("⭐" if is_fv else "☆", key=f"fvr_{ri}_{ck}_{ii}"):
                                if is_fv:
                                    st.session_state.favorites=[f for f in st.session_state.favorites if f["url"]!=iu]
                                else:
                                    st.session_state.favorites.append({
                                        "url":iu,"title":item["name"],"price":item["price"],
                                        "price_int":item.get("price_int",0),"brand":item.get("brand",""),
                                        "maker":item.get("maker",""),"mall":item.get("supplier",""),
                                        "image":item.get("image_url",""),"cat":ck,
                                        "brand_name":item.get("brand_name",""),
                                        "product_group":item.get("product_group",""),
                                    })
                                st.rerun()
                        with ea:
                            exp_key=f"exp_{ri}_{ck}_{ii}"
                            if st.button("✏", key=f"ed_{ri}_{ck}_{ii}"):
                                st.session_state[exp_key]=not st.session_state.get(exp_key,False)
                                st.rerun()
                        with fa:
                            if st.button("🗑", key=f"dl_{ri}_{ck}_{ii}"):
                                room["specbook"][ck].pop(ii); st.rerun()

                    # 편집 패널
                    if st.session_state.get(f"exp_{ri}_{ck}_{ii}", False):
                        with st.container():
                            e1,e2 = st.columns(2)
                            with e1:
                                item["name"]     = st.text_input("제품명", item["name"],     key=f"en_{ri}_{ck}_{ii}")
                                item["brand"]    = st.text_input("브랜드", item["brand"],    key=f"eb_{ri}_{ck}_{ii}")
                                item["supplier"] = st.text_input("판매처", item["supplier"], key=f"es_{ri}_{ck}_{ii}")
                                item["price"]    = st.text_input("가격",   item["price"],    key=f"ep_{ri}_{ck}_{ii}")
                            with e2:
                                item["size"]         = st.text_input("규격", item.get("size",""),         key=f"esz_{ri}_{ck}_{ii}")
                                item["color"]        = st.text_input("색상", item.get("color",""),        key=f"ec_{ri}_{ck}_{ii}")
                                item["material"]     = st.text_input("재질", item.get("material",""),     key=f"em_{ri}_{ck}_{ii}")
                                item["model_number"] = st.text_input("품번", item.get("model_number",""), key=f"emn_{ri}_{ck}_{ii}")
                            item["location"] = st.text_input("적용 위치", item.get("location",""),
                                               placeholder="예: 거실 벽면", key=f"el_{ri}_{ck}_{ii}")
                            item["memo"] = st.text_area("비고", item.get("memo",""),
                                           key=f"emm_{ri}_{ck}_{ii}", height=52)
                            if item.get("source_url"):
                                st.markdown(f"[🔗 상품 페이지]({item['source_url']})")
                            other_rooms = [r for r in st.session_state.rooms if r["id"]!=room["id"]]
                            if other_rooms:
                                cp1,cp2 = st.columns([3,1])
                                with cp1:
                                    ct = st.selectbox("다른 공간으로 복사",
                                         [r["name"] for r in other_rooms],
                                         key=f"cpt_{ri}_{ck}_{ii}", label_visibility="collapsed")
                                with cp2:
                                    if st.button("복사", key=f"cp_{ri}_{ck}_{ii}", use_container_width=True):
                                        tgt=next(r for r in other_rooms if r["name"]==ct)
                                        ni=_copy.deepcopy(item)
                                        ni["id"]=str(uuid.uuid4())[:8]
                                        ni["created_at"]=datetime.now().strftime("%Y-%m-%d %H:%M")
                                        tgt["specbook"][ck].append(ni)
                                        st.success(f"'{ct}'에 복사 완료!"); st.rerun()

                    st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>", unsafe_allow_html=True)

            # 모델링 이미지
            st.markdown("---")
            with st.expander("🖼 모델링 이미지 (PPT VIEW 01–04)", expanded=False):
                ic1,ic2 = st.columns(2)
                for vi in range(4):
                    with (ic1 if vi%2==0 else ic2):
                        key=f"model_img_{room['id']}_{vi}"
                        uf=st.file_uploader(f"VIEW {vi+1:02d}", type=["png","jpg","jpeg"], key=key)
                        if uf: st.image(uf, use_container_width=True)
