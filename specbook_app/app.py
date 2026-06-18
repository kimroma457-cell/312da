"""
인테리어 스펙북 생성기 v3 — 카테고리 → 업체 → 제품군 → 검색
"""
import re
import uuid
import json
import streamlit as st
from datetime import datetime
from brands import BRAND_CATALOG, CATEGORY_META
from naver_shopping import search_products, CATEGORIES
from pptx_generator import generate_pptx

st.set_page_config(page_title="스펙북 생성기", page_icon="🏠",
                   layout="wide", initial_sidebar_state="expanded")

CAT_KEYS = list(BRAND_CATALOG.keys())

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;}
.stApp{background:#F7F5F2;}
#MainMenu,footer,header{visibility:hidden;}

.top-bar{background:#1A1816;padding:14px 28px;margin:-1rem -1rem 1.2rem -1rem;
         display:flex;align-items:center;gap:16px;}
.top-bar h1{color:#fff;font-size:1.2rem;font-weight:700;margin:0;letter-spacing:1px;flex:1;}
.gold{color:#C8A97E;}

/* 단계 표시 브레드크럼 */
.breadcrumb{background:#fff;border:1px solid #E8E2DC;border-radius:8px;
            padding:8px 14px;margin-bottom:12px;font-size:.8rem;color:#9A8F86;}
.breadcrumb .sel{color:#1A1816;font-weight:700;}
.breadcrumb .sep{margin:0 6px;color:#D0CBC4;}

/* 카테고리 칩 */
.cat-chip-wrap{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;}

/* 업체 카드 그리드 */
.brand-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;margin-bottom:14px;}
.brand-card{background:#fff;border:1.5px solid #E8E2DC;border-radius:10px;
            padding:12px 10px;text-align:center;cursor:pointer;
            font-size:.82rem;font-weight:700;color:#4A4540;transition:.15s;}
.brand-card:hover{border-color:#C8A97E;color:#1A1816;box-shadow:0 2px 8px rgba(0,0,0,.06);}
.brand-card.active{background:#1A1816;border-color:#1A1816;color:#C8A97E;}

/* 제품군 칩 */
.group-chip-wrap{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;}
.group-chip{display:inline-block;background:#F5F3F0;border:1px solid #E0DCD8;
            border-radius:16px;padding:4px 12px;font-size:.75rem;
            font-weight:600;color:#4A4540;cursor:pointer;transition:.12s;}
.group-chip:hover,.group-chip.active{background:#1A1816;color:#C8A97E;border-color:#1A1816;}

/* 상품 카드 */
.pcard-title{font-size:.86rem;font-weight:700;color:#1A1816;line-height:1.3;margin-bottom:3px;}
.pcard-price{font-size:.92rem;font-weight:700;color:#C8A97E;}
.pcard-meta{font-size:.70rem;color:#9A8F86;}

/* 추가된 자재 */
.item-name{font-size:.82rem;font-weight:700;color:#1A1816;
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.item-price{font-size:.76rem;color:#C8A97E;font-weight:600;}
.sec-label{font-size:.62rem;font-weight:700;letter-spacing:2px;
           text-transform:uppercase;color:#C8A97E;margin:0 0 6px;}

/* 배지 (카테고리별 색상) */
.badge{display:inline-block;padding:2px 7px;border-radius:12px;font-size:.64rem;font-weight:700;
       background:#EFEBE9;color:#4E342E;}

/* 사이드바 */
section[data-testid="stSidebar"]{background:#1A1816!important;}
section[data-testid="stSidebar"] *{color:#E8E2DC!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:#2C2A28!important;border:1px solid #3C3A38!important;color:#C8A97E!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:#C8A97E!important;color:#1A1816!important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea{
  background:#2C2A28!important;border-color:#3C3A38!important;color:#E8E2DC!important;}
section[data-testid="stSidebar"] label{color:#8C7F74!important;font-size:.74rem!important;}

/* 탭 */
.stTabs [data-baseweb="tab-list"]{background:#EEEBE6;padding:4px;border-radius:10px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:600;font-size:.78rem;padding:5px 12px;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;}

/* 버튼 */
.stButton>button{border-radius:8px!important;font-size:.78rem!important;font-weight:600!important;}
div[data-testid="stButton"]>button[kind="primary"]{
  background:#1A1816!important;color:#C8A97E!important;border:none!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-bar">
  <h1>INTERIOR <span class="gold">SPEC BOOK</span></h1>
  <span style="color:#8C7F74;font-size:.72rem">업체 선택 → 제품군 선택 → 검색 → 추가</span>
</div>
""", unsafe_allow_html=True)

# ── 세션 초기화 ────────────────────────────────────────────────────────────────
def _init_specbook():
    return {k: [] for k in CAT_KEYS}

def _init_selector():
    return {"cat": None, "brand": None, "group": None}

if "rooms" not in st.session_state:
    st.session_state.rooms = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []   # 전역 즐겨찾기 (방과 무관)
if "project" not in st.session_state:
    st.session_state.project = {
        "company":  "DESICODE",
        "name":     "○○ 아파트 리모델링",
        "location": "서울시 강남구",
        "area":     "84㎡ (25.4평)",
        "period":   "2026.07 ~ 2026.08",
        "designer": "홍길동",
        "date":     datetime.now().strftime("%Y.%m.%d"),
    }

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
        "id":       str(uuid.uuid4())[:8],
        "name":     name,
        "name_en":  en,
        "specbook": _init_specbook(),
        "sel":      _init_selector(),
    })
    st.rerun()

def _extract_spec(title):
    m = re.search(
        r'\d+(?:\.\d+)?[\s]*[×xX\*][\s]*\d+(?:\.\d+)?'
        r'(?:[\s]*[×xX\*][\s]*\d+(?:\.\d+)?)?(?:[\s]*(?:mm|cm|m))?',
        title, re.IGNORECASE
    )
    if m: return m.group().strip()
    m = re.search(r'\d+(?:\.\d+)?[\s]*(?:mm|cm|m²|㎡)', title, re.IGNORECASE)
    return m.group().strip() if m else ""

# ── 사이드바: 프로젝트 정보 ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 프로젝트 정보")
    p = st.session_state.project
    p["company"]  = st.text_input("회사명",    p["company"])
    p["name"]     = st.text_input("프로젝트명", p["name"])
    p["location"] = st.text_input("위치",      p["location"])
    p["area"]     = st.text_input("면적",      p["area"])
    p["period"]   = st.text_input("공사기간",  p["period"])
    p["designer"] = st.text_input("담당자",    p["designer"])
    p["date"]     = st.text_input("작성일",    p["date"])
    st.markdown("---")
    if st.session_state.rooms:
        st.markdown("**추가된 공간**")
        for i, room in enumerate(st.session_state.rooms):
            total = sum(len(v) for v in room["specbook"].values())
            c1, c2 = st.columns([4,1])
            c1.markdown(
                f"**{room['name']}** <span style='color:#8C7F74;font-size:.72rem'>({total})</span>",
                unsafe_allow_html=True,
            )
            if c2.button("✕", key=f"dr{i}"):
                st.session_state.rooms.pop(i); st.rerun()
    st.markdown("---")
    total_items = sum(
        len(items)
        for room in st.session_state.rooms
        for items in room["specbook"].values()
    )
    st.markdown(
        f"<div style='text-align:center;color:#C8A97E;font-size:.82rem;font-weight:700'>"
        f"총 {len(st.session_state.rooms)}개 공간 · {total_items}개 자재</div>",
        unsafe_allow_html=True,
    )

# ── 탭 구성 ────────────────────────────────────────────────────────────────────
tab_labels = [r["name"] for r in st.session_state.rooms] + ["＋ 공간", "📄 PPT 생성"]
tabs = st.tabs(tab_labels)

# ── 공간 추가 탭 ───────────────────────────────────────────────────────────────
with tabs[-2]:
    st.markdown("#### 공간 추가")
    st.caption("프리셋을 클릭하면 즉시 추가됩니다. 같은 공간은 번호가 자동으로 붙습니다.")
    cols = st.columns(5)
    for idx, (ko, en, icon) in enumerate(ROOM_PRESETS):
        with cols[idx % 5]:
            if st.button(f"{icon}\n{ko}", key=f"preset_{ko}", use_container_width=True):
                _add_room(ko, en)
    st.markdown("---")
    c1, c2, c3 = st.columns([3,3,1])
    with c1: custom_ko = st.text_input("공간명 (한글)", placeholder="홈짐", key="cko")
    with c2: custom_en = st.text_input("공간명 (영어)", placeholder="Home Gym", key="cen")
    with c3:
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        if st.button("추가", use_container_width=True, type="primary") and custom_ko:
            _add_room(custom_ko, custom_en or custom_ko)
        st.markdown("</div>", unsafe_allow_html=True)
    if not st.session_state.rooms:
        st.info("👆 위에서 공간을 추가하면 탭이 생성됩니다.")


# ── 각 방 탭 ──────────────────────────────────────────────────────────────────
for ri, (tab, room) in enumerate(zip(tabs[:-2], st.session_state.rooms)):
    with tab:
        sel    = room.setdefault("sel", _init_selector())
        total_room = sum(len(v) for v in room["specbook"].values())

        st.markdown(
            f'<div style="border-bottom:2px solid #1A1816;padding-bottom:8px;margin-bottom:14px;'
            f'display:flex;align-items:center;gap:10px;">'
            f'<span style="font-size:1rem;font-weight:700">{room["name"]}</span>'
            f'<span style="font-size:.72rem;color:#9A8F86">{room["name_en"]}</span>'
            f'<span style="margin-left:auto;font-size:.72rem;color:#C8A97E;font-weight:700">'
            f'{total_room}개 자재</span></div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns([3, 2], gap="large")

        with left:
            # ── 브레드크럼 ─────────────────────────────────────────────────
            bc_cat   = f'<span class="sel">{sel["cat"]}</span>'   if sel["cat"]   else '<span>카테고리</span>'
            bc_brand = f'<span class="sel">{sel["brand"]}</span>' if sel["brand"] else '<span>업체</span>'
            bc_group = f'<span class="sel">{sel["group"]}</span>' if sel["group"] else '<span>제품군</span>'
            st.markdown(
                f'<div class="breadcrumb">{bc_cat}'
                f'<span class="sep">›</span>{bc_brand}'
                f'<span class="sep">›</span>{bc_group}</div>',
                unsafe_allow_html=True,
            )

            # ── STEP 1: 카테고리 선택 ──────────────────────────────────────
            st.markdown('<p class="sec-label">① 카테고리</p>', unsafe_allow_html=True)

            # 즐겨찾기 버튼 (전역 favorites 카운트)
            fav_count = len(st.session_state.favorites)
            fav_active = sel["cat"] == "__fav__"
            fav_label = f"⭐ 즐겨찾기 ({fav_count})" if fav_count else "⭐ 즐겨찾기"
            if st.button(fav_label, key=f"cat_{ri}___fav__",
                         use_container_width=False,
                         type="primary" if fav_active else "secondary"):
                sel["cat"] = None if fav_active else "__fav__"
                sel["brand"] = None
                sel["group"] = None
                st.session_state.pop(f"res_{ri}", None)
                st.rerun()

            cat_cols = st.columns(4)
            for ci, ck in enumerate(CAT_KEYS):
                meta = CATEGORY_META[ck]
                is_active = sel["cat"] == ck
                with cat_cols[ci % 4]:
                    if st.button(
                        f"{meta['icon']} {ck}",
                        key=f"cat_{ri}_{ck}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                    ):
                        if sel["cat"] != ck:
                            sel["cat"] = ck
                            sel["brand"] = None
                            sel["group"] = None
                            st.session_state.pop(f"res_{ri}", None)
                        st.rerun()

            # ── 즐겨찾기 뷰 ───────────────────────────────────────────────
            if sel["cat"] == "__fav__":
                favs = st.session_state.favorites
                if not favs:
                    st.info("⭐ 즐겨찾기가 비어있습니다. 검색 결과에서 ☆ 버튼으로 추가하세요.")
                else:
                    st.markdown(f"**⭐ 즐겨찾기 — {len(favs)}개**")
                    existing_urls = {
                        it["source_url"]
                        for items in room["specbook"].values()
                        for it in items
                    }
                    for fi, fav in enumerate(favs):
                        ck = fav.get("cat", "")
                        meta = CATEGORY_META.get(ck, {"icon": "📦", "item_code": ck})
                        is_dup = fav["url"] in existing_urls
                        c_img, c_info, c_act = st.columns([1, 5, 2])
                        with c_img:
                            if fav.get("image"):
                                st.image(fav["image"], use_container_width=True)
                        with c_info:
                            st.markdown(
                                f'<div class="pcard-title">{fav["title"][:44]}</div>'
                                f'<div class="pcard-price">{fav["price"]}</div>'
                                f'<div class="pcard-meta">'
                                f'<span class="badge">{meta["icon"]} {ck}</span>'
                                f' {fav.get("brand_name","")}' +
                                (f' › {fav["product_group"]}' if fav.get("product_group") else "")
                                + "</div>",
                                unsafe_allow_html=True,
                            )
                            if fav.get("url"):
                                st.markdown(f"[🔗 상품 링크]({fav['url']})")
                        with c_act:
                            if st.button("⭐", key=f"unfav_{ri}_{fi}",
                                         help="즐겨찾기 해제"):
                                st.session_state.favorites.pop(fi); st.rerun()
                            if is_dup:
                                st.caption("✓ 추가됨")
                            elif ck:
                                if st.button("＋ 추가", key=f"favadd_{ri}_{fi}",
                                             use_container_width=True, type="primary"):
                                    room["specbook"][ck].append({
                                        "id":           str(uuid.uuid4())[:8],
                                        "category":     ck,
                                        "brand_name":   fav.get("brand_name", ""),
                                        "product_group":fav.get("product_group", ""),
                                        "name":         fav["title"],
                                        "brand":        fav["brand"] or fav.get("brand_name", ""),
                                        "maker":        fav.get("maker", ""),
                                        "supplier":     fav.get("mall", ""),
                                        "price":        fav["price"],
                                        "price_int":    fav["price_int"],
                                        "image_url":    fav.get("image", ""),
                                        "source_url":   fav["url"],
                                        "material":     "",
                                        "color":        "",
                                        "size":         _extract_spec(fav["title"]),
                                        "model_number": "",
                                        "unit":         "EA",
                                        "qty":          1,
                                        "location":     "",
                                        "memo":         "",
                                        "item_code":    meta["item_code"],
                                        "is_common":    False,
                                        "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    })
                                    st.rerun()
                        st.markdown(
                            "<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>",
                            unsafe_allow_html=True,
                        )

            elif not sel["cat"]:
                st.info("카테고리를 선택하면 관련 업체 목록이 표시됩니다.")

            else:
                # ── STEP 2: 업체 선택 ─────────────────────────────────────
                st.markdown('<p class="sec-label" style="margin-top:12px">② 업체 / 브랜드</p>',
                            unsafe_allow_html=True)
                brands = BRAND_CATALOG[sel["cat"]]
                brand_cols = st.columns(3)
                for bi, b in enumerate(brands):
                    is_active = sel["brand"] == b["name"]
                    with brand_cols[bi % 3]:
                        if st.button(
                            b["name"],
                            key=f"brand_{ri}_{bi}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            if sel["brand"] != b["name"]:
                                sel["brand"] = b["name"]
                                sel["group"] = None
                                st.session_state.pop(f"res_{ri}", None)
                            st.rerun()

                if not sel["brand"]:
                    st.caption("업체를 선택하면 제품군과 검색창이 활성화됩니다.")
                else:
                    # ── STEP 3: 제품군 선택 ───────────────────────────────────
                    brand_data = next((b for b in brands if b["name"] == sel["brand"]), None)
                    groups = brand_data["groups"] if brand_data else []

                    st.markdown('<p class="sec-label" style="margin-top:10px">③ 제품군 선택</p>',
                                unsafe_allow_html=True)
                    group_cols = st.columns(4)
                    for gi, g in enumerate(groups):
                        is_active = sel["group"] == g
                        with group_cols[gi % 4]:
                            if st.button(
                                g,
                                key=f"group_{ri}_{gi}",
                                use_container_width=True,
                                type="primary" if is_active else "secondary",
                            ):
                                sel["group"] = None if is_active else g
                                st.session_state.pop(f"res_{ri}", None)
                                st.rerun()

                    # ── 검색창 ────────────────────────────────────────────────
                    st.markdown('<p class="sec-label" style="margin-top:10px">🔍 제품 검색</p>',
                                unsafe_allow_html=True)
                    group_hint = sel["group"] or "제품군을 선택하거나"
                    q_col, b_col = st.columns([5,1])
                    with q_col:
                        keyword = st.text_input(
                            "검색어",
                            placeholder=f"{group_hint} 여기에 추가 키워드 입력 (예: 베이지, 600각, 방염)",
                            key=f"kw_{ri}",
                            label_visibility="collapsed",
                        )
                    with b_col:
                        do_search = st.button("검색", key=f"sb_{ri}",
                                              use_container_width=True, type="primary")

                    if do_search:
                        if not sel["group"] and not keyword.strip():
                            st.warning("제품군을 선택하거나 검색어를 입력하세요.")
                        else:
                            with st.spinner(f"{sel['brand']} 제품 검색 중..."):
                                results = search_products(
                                    brand=sel["brand"],
                                    category=sel["cat"],
                                    product_group=sel["group"] or "",
                                    keyword=keyword.strip(),
                                    count=50,
                                )
                            st.session_state[f"res_{ri}"] = results
                            st.session_state[f"page_{ri}"] = 0

                    # ── 검색 결과 표시 ────────────────────────────────────────
                    products = st.session_state.get(f"res_{ri}", [])
                    page     = st.session_state.get(f"page_{ri}", 0)
                    PAGE_SIZE = 10

                    if products:
                        SORT_OPTIONS = {
                            "인기순": None,
                            "가격 낮은순": lambda x: x["price_int"],
                            "가격 높은순": lambda x: -x["price_int"],
                        }
                        sort_key = st.selectbox(
                            "정렬",
                            options=list(SORT_OPTIONS.keys()),
                            key=f"sort_{ri}",
                            label_visibility="collapsed",
                        )
                        sort_fn = SORT_OPTIONS[sort_key]
                        sorted_products = sorted(products, key=sort_fn) if sort_fn else products

                        total_pages = -(-len(sorted_products) // PAGE_SIZE)
                        page_items  = sorted_products[page * PAGE_SIZE: (page+1) * PAGE_SIZE]

                        hc1, hc2, hc3 = st.columns([3,2,3])
                        with hc1:
                            st.markdown(f"**{len(products)}개 결과**")
                        with hc2:
                            st.markdown(
                                f"<div style='text-align:center;font-size:.75rem;color:#9A8F86'>"
                                f"{page+1} / {total_pages} 페이지</div>",
                                unsafe_allow_html=True,
                            )
                        with hc3:
                            pc1, pc2 = st.columns(2)
                            with pc1:
                                if st.button("◀", key=f"prev_{ri}", disabled=(page==0),
                                             use_container_width=True):
                                    st.session_state[f"page_{ri}"] = page-1; st.rerun()
                            with pc2:
                                if st.button("▶", key=f"next_{ri}",
                                             disabled=(page>=total_pages-1), use_container_width=True):
                                    st.session_state[f"page_{ri}"] = page+1; st.rerun()

                        existing_urls = {
                            it["source_url"]
                            for items in room["specbook"].values()
                            for it in items
                        }
                        fav_urls = {f["url"] for f in st.session_state.favorites}

                        for pi, prod in enumerate(page_items):
                            gpi = page * PAGE_SIZE + pi
                            is_dup = prod["url"] in existing_urls
                            is_fav = prod["url"] in fav_urls
                            with st.container():
                                ic, inf, ac = st.columns([1,5,2])
                                with ic:
                                    if prod["image"]:
                                        st.image(prod["image"], use_container_width=True)
                                with inf:
                                    st.markdown(
                                        f'<div class="pcard-title">{prod["title"][:44]}</div>'
                                        f'<div class="pcard-price">{prod["price"]}</div>'
                                        f'<div class="pcard-meta">'
                                        f'{prod["brand"] or sel["brand"]}'
                                        f' | {prod["mall"] or "—"}</div>',
                                        unsafe_allow_html=True,
                                    )
                                    if prod["url"]:
                                        st.markdown(f"[🔗 상품 링크]({prod['url']})")
                                with ac:
                                    if st.button("⭐" if is_fav else "☆",
                                                 key=f"fav_{ri}_{gpi}",
                                                 help="즐겨찾기 등록/해제"):
                                        if is_fav:
                                            st.session_state.favorites = [
                                                f for f in st.session_state.favorites
                                                if f["url"] != prod["url"]
                                            ]
                                        else:
                                            st.session_state.favorites.append({
                                                **prod,
                                                "cat": sel["cat"],
                                                "brand_name": sel["brand"],
                                                "product_group": sel["group"] or "",
                                            })
                                        st.rerun()
                                    if is_dup:
                                        st.caption("✓ 추가됨")
                                    else:
                                        if st.button("＋ 추가", key=f"add_{ri}_{gpi}",
                                                     use_container_width=True, type="primary"):
                                            cat_key = sel["cat"]
                                            meta = CATEGORY_META[cat_key]
                                            room["specbook"][cat_key].append({
                                                "id":           str(uuid.uuid4())[:8],
                                                "category":     cat_key,
                                                "brand_name":   sel["brand"],
                                                "product_group":sel["group"] or "",
                                                "name":         prod["title"],
                                                "brand":        prod["brand"] or sel["brand"],
                                                "maker":        prod["maker"] or "",
                                                "supplier":     prod["mall"] or "",
                                                "price":        prod["price"],
                                                "price_int":    prod["price_int"],
                                                "image_url":    prod["image"],
                                                "source_url":   prod["url"],
                                                "material":     "",
                                                "color":        "",
                                                "size":         _extract_spec(prod["title"]),
                                                "model_number": "",
                                                "unit":         "EA",
                                                "qty":          1,
                                                "location":     "",
                                                "memo":         "",
                                                "item_code":    meta["item_code"],
                                                "is_common":    False,
                                                "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            })
                                            st.rerun()
                                st.markdown(
                                    "<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>",
                                    unsafe_allow_html=True,
                                )

                    elif f"res_{ri}" in st.session_state:
                        st.warning(
                            f"**{sel['brand']}**의 전문 시공 자재 결과가 없습니다.\n\n"
                            "다른 업체를 선택하거나, 제품군·검색어를 변경해보세요."
                        )

        # ── 오른쪽: 추가된 자재 목록 ──────────────────────────────────────
        with right:
            st.markdown('<p class="sec-label">추가된 자재</p>', unsafe_allow_html=True)
            if total_room == 0:
                st.caption("왼쪽에서 업체 → 제품군 선택 후 추가하세요.")
            else:
                for ck in CAT_KEYS:
                    items = room["specbook"][ck]
                    if not items:
                        continue
                    meta = CATEGORY_META[ck]
                    st.markdown(
                        f'<span class="badge">{meta["icon"]} {ck} {len(items)}</span>',
                        unsafe_allow_html=True,
                    )
                    for ii, item in enumerate(items):
                        c_img, c_info, c_act = st.columns([1,5,2])
                        with c_img:
                            if item.get("image_url"):
                                st.image(item["image_url"], use_container_width=True)
                            else:
                                st.markdown(
                                    f'<div style="width:44px;height:44px;background:#F0EDE8;'
                                    f'border-radius:6px;display:flex;align-items:center;'
                                    f'justify-content:center;font-size:1.1rem">{meta["icon"]}</div>',
                                    unsafe_allow_html=True,
                                )
                        with c_info:
                            st.markdown(
                                f'<div class="item-name">{item["name"][:26]}</div>'
                                f'<div class="item-price">{item["price"]}</div>'
                                f'<div style="font-size:.68rem;color:#9A8F86">'
                                f'{item.get("brand_name","")}' +
                                (f' › {item["product_group"]}' if item.get("product_group") else "")
                                + "</div>",
                                unsafe_allow_html=True,
                            )
                        with c_act:
                            item_url = item.get("source_url", "")
                            fav_urls_right = {f["url"] for f in st.session_state.favorites}
                            is_fav_right = item_url and item_url in fav_urls_right
                            if st.button("⭐" if is_fav_right else "☆",
                                         key=f"cm_{ri}_{ck}_{ii}",
                                         help="즐겨찾기 등록/해제"):
                                if is_fav_right:
                                    st.session_state.favorites = [
                                        f for f in st.session_state.favorites
                                        if f["url"] != item_url
                                    ]
                                else:
                                    st.session_state.favorites.append({
                                        "url":           item_url,
                                        "title":         item["name"],
                                        "price":         item["price"],
                                        "price_int":     item.get("price_int", 0),
                                        "brand":         item.get("brand", ""),
                                        "maker":         item.get("maker", ""),
                                        "mall":          item.get("supplier", ""),
                                        "image":         item.get("image_url", ""),
                                        "cat":           ck,
                                        "brand_name":    item.get("brand_name", ""),
                                        "product_group": item.get("product_group", ""),
                                    })
                                st.rerun()
                            if st.button("🗑", key=f"del_{ri}_{ck}_{ii}"):
                                room["specbook"][ck].pop(ii); st.rerun()

                        with st.expander("✏ 편집", expanded=False):
                            e1, e2 = st.columns(2)
                            with e1:
                                item["name"]     = st.text_input("제품명",  item["name"],    key=f"en_{ri}_{ck}_{ii}")
                                item["brand"]    = st.text_input("브랜드",  item["brand"],   key=f"eb_{ri}_{ck}_{ii}")
                                item["supplier"] = st.text_input("판매처",  item["supplier"],key=f"es_{ri}_{ck}_{ii}")
                                item["price"]    = st.text_input("가격",    item["price"],   key=f"ep_{ri}_{ck}_{ii}")
                                item["qty"]      = st.number_input("수량", min_value=1,
                                                    value=item.get("qty",1), key=f"eq_{ri}_{ck}_{ii}")
                            with e2:
                                item["size"]         = st.text_input("규격",  item.get("size",""),        key=f"esz_{ri}_{ck}_{ii}")
                                item["color"]        = st.text_input("색상",  item.get("color",""),       key=f"ec_{ri}_{ck}_{ii}")
                                item["material"]     = st.text_input("재질",  item.get("material",""),    key=f"em_{ri}_{ck}_{ii}")
                                item["model_number"] = st.text_input("품번",  item.get("model_number",""),key=f"emn_{ri}_{ck}_{ii}")
                                item["unit"]         = st.text_input("단위",  item.get("unit","EA"),      key=f"eu_{ri}_{ck}_{ii}")
                            item["location"] = st.text_input("적용 위치", item.get("location",""),
                                placeholder="예: 거실 벽면", key=f"el_{ri}_{ck}_{ii}")
                            item["memo"] = st.text_area("비고", item.get("memo",""),
                                key=f"emm_{ri}_{ck}_{ii}", height=52)
                            if item.get("source_url"):
                                st.markdown(f"[🔗 상품 페이지]({item['source_url']})")

                        st.markdown(
                            "<hr style='border:none;border-top:1px solid #F0EBE4;margin:3px 0'>",
                            unsafe_allow_html=True,
                        )


# ── PPT 생성 탭 ────────────────────────────────────────────────────────────────
with tabs[-1]:
  try:
    st.markdown('<p class="sec-label">Export</p>', unsafe_allow_html=True)
    total_all = sum(
        len(items)
        for room in st.session_state.rooms
        for items in room["specbook"].values()
    )
    common_cnt = sum(
        1 for room in st.session_state.rooms
        for items in room["specbook"].values()
        for it in items if it.get("is_common")
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("공간 수", len(st.session_state.rooms))
    m2.metric("총 자재 수", total_all)
    m3.metric("공통 자재 (슬라이드4)", common_cnt)

    if common_cnt:
        st.markdown("**⭐ 공통 자재**")
        for room in st.session_state.rooms:
            for ck, items in room["specbook"].items():
                for it in items:
                    if it.get("is_common"):
                        st.markdown(
                            f'&nbsp;&nbsp;<span class="badge">{CATEGORY_META[ck]["icon"]} {ck}</span>'
                            f'&nbsp;{it["name"][:30]}&nbsp;'
                            f'<span style="color:#C8A97E">{it["price"]}</span>',
                            unsafe_allow_html=True,
                        )

    st.markdown("---")
    for room in st.session_state.rooms:
        room_total = sum(len(v) for v in room["specbook"].values())
        if not room_total: continue
        st.markdown(f"**{room['name']}** ({room_total}개)")
        for ck, items in room["specbook"].items():
            if items:
                meta = CATEGORY_META[ck]
                names = " · ".join(it["name"][:16] for it in items[:3])
                st.markdown(
                    f'&nbsp;&nbsp;<span class="badge">{meta["icon"]} {ck}</span>'
                    f'&nbsp;{names}{"..." if len(items)>3 else ""}',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    col_j, col_p, _ = st.columns([2,2,3])
    export_data = {
        "project": st.session_state.project,
        "rooms": [
            {"name": r["name"], "name_en": r["name_en"],
             "items": [it for items in r["specbook"].values() for it in items]}
            for r in st.session_state.rooms
        ],
    }
    with col_j:
        st.download_button(
            "📊 JSON 내보내기",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name=f"{p['name']}_specbook.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_p:
        if st.button("🎨 PPT 스펙북 생성", type="primary",
                     use_container_width=True, disabled=total_all==0):
            common_materials = [
                {"item_code": it["item_code"], "product": it["name"],
                 "spec": it.get("size",""), "finish": it.get("material","") or it.get("color",""),
                 "vendor": it.get("supplier",""), "location": it.get("location","")}
                for room in st.session_state.rooms
                for items in room["specbook"].values()
                for it in items if it.get("is_common")
            ][:6]

            ppt_rooms = []
            for room in st.session_state.rooms:
                all_items = [
                    {"item_code": it["item_code"], "product": it["name"],
                     "spec": it.get("size",""),
                     "finish": it.get("material","") or it.get("color",""),
                     "vendor": it.get("supplier",""), "qty": it.get("qty",1),
                     "note": it.get("memo",""), "price": it["price"],
                     "image_url": it.get("image_url",""), "room": room["name"]}
                    for items in room["specbook"].values()
                    for it in items
                ]
                if all_items:
                    ppt_rooms.append({"name": room["name"], "name_en": room["name_en"],
                                      "items": all_items})

            with st.spinner("PPT 생성 중..."):
                pptx_bytes = generate_pptx(p, ppt_rooms, common_materials)

            st.download_button(
                "⬇️ PPT 다운로드",
                data=pptx_bytes,
                file_name=f"{p['name']}_스펙북.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
            st.success("✓ 생성 완료!")
    if total_all == 0:
        st.caption("각 공간 탭에서 자재를 추가한 뒤 생성하세요.")
  except Exception as e:
    st.error(f"PPT 탭 오류: {e}")
    import traceback; st.code(traceback.format_exc())
