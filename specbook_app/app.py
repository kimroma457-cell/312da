"""
인테리어 스펙북 생성기 v2 — 최소 조작 · 방대한 정보
"""
import re
import uuid
import json
import streamlit as st
from datetime import datetime
from naver_shopping import search_products, CATEGORIES
from pptx_generator import generate_pptx

st.set_page_config(page_title="스펙북 생성기", page_icon="🏠",
                   layout="wide", initial_sidebar_state="expanded")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;}
.stApp{background:#F7F5F2;}
#MainMenu,footer,header{visibility:hidden;}

.top-bar{background:#1A1816;padding:16px 28px;margin:-1rem -1rem 1.2rem -1rem;
         display:flex;align-items:center;gap:20px;}
.top-bar h1{color:#fff;font-size:1.25rem;font-weight:700;margin:0;letter-spacing:1px;flex:1;}
.top-bar .sub{color:#8C7F74;font-size:.75rem;}
.gold{color:#C8A97E;}

.sec-label{font-size:.65rem;font-weight:700;letter-spacing:2px;
           text-transform:uppercase;color:#C8A97E;margin:0 0 6px;}

/* 방 프리셋 칩 */
.room-chip{display:inline-flex;align-items:center;gap:6px;
           background:#fff;border:1.5px solid #E8E2DC;border-radius:20px;
           padding:6px 14px;cursor:pointer;font-size:.82rem;font-weight:600;
           color:#4A4540;transition:.15s;margin:3px;}
.room-chip:hover{border-color:#C8A97E;color:#1A1816;}

/* 카테고리 버튼 */
.stButton>button{border-radius:8px!important;font-size:.8rem!important;font-weight:600!important;}

/* 상품 카드 */
.pcard{background:#fff;border:1.5px solid #E8E2DC;border-radius:10px;
       padding:12px;margin-bottom:8px;}
.pcard-title{font-size:.88rem;font-weight:700;color:#1A1816;line-height:1.3;margin-bottom:3px;}
.pcard-price{font-size:.95rem;font-weight:700;color:#C8A97E;}
.pcard-meta{font-size:.72rem;color:#9A8F86;}

/* 자재 항목 (오른쪽 패널) */
.item-row{background:#fff;border:1px solid #E8E2DC;border-radius:8px;
          padding:10px 12px;margin-bottom:6px;display:flex;gap:10px;align-items:flex-start;}
.item-thumb{width:48px;height:48px;object-fit:cover;border-radius:6px;flex-shrink:0;}
.item-thumb-ph{width:48px;height:48px;background:#F0EDE8;border-radius:6px;
               display:flex;align-items:center;justify-content:center;
               font-size:1.2rem;flex-shrink:0;}
.item-info{flex:1;min-width:0;}
.item-name{font-size:.83rem;font-weight:700;color:#1A1816;
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.item-price{font-size:.78rem;color:#C8A97E;font-weight:600;}
.item-meta{font-size:.7rem;color:#9A8F86;}

/* 배지 */
.badge{display:inline-block;padding:2px 7px;border-radius:12px;font-size:.65rem;font-weight:700;}
.badge-벽   {background:#E3F2FD;color:#1565C0;}
.badge-바닥  {background:#E8F5E9;color:#2E7D32;}
.badge-천장  {background:#FFF8E1;color:#F57F17;}
.badge-조명  {background:#FFF9C4;color:#F9A825;}
.badge-욕실  {background:#E0F7FA;color:#006064;}
.badge-주방  {background:#FCE4EC;color:#880E4F;}
.badge-가구  {background:#F3E5F5;color:#4A148C;}
.badge-전기  {background:#FBE9E7;color:#BF360C;}
.badge-기타  {background:#EFEBE9;color:#4E342E;}

/* 사이드바 */
section[data-testid="stSidebar"]{background:#1A1816!important;}
section[data-testid="stSidebar"] *{color:#E8E2DC!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:#2C2A28!important;border:1px solid #3C3A38!important;
  color:#C8A97E!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:#C8A97E!important;color:#1A1816!important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] select{
  background:#2C2A28!important;border-color:#3C3A38!important;color:#E8E2DC!important;}
section[data-testid="stSidebar"] label{color:#8C7F74!important;font-size:.75rem!important;}

/* 탭 */
.stTabs [data-baseweb="tab-list"]{background:#EEEBE6;padding:4px;border-radius:10px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:600;font-size:.8rem;padding:6px 14px;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;}

/* 기본 버튼 */
div[data-testid="stButton"]>button[kind="primary"]{
  background:#1A1816!important;color:#C8A97E!important;border:none!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-bar">
  <h1>INTERIOR <span class="gold">SPEC BOOK</span></h1>
  <span class="sub">카테고리 검색 → 한 번 클릭으로 추가 → PPT 생성</span>
</div>
""", unsafe_allow_html=True)

# ── 상수 ──────────────────────────────────────────────────────────────────────
CAT_KEYS = list(CATEGORIES.keys())

ROOM_PRESETS = [
    ("거실",    "Living Room",    "🛋"),
    ("침실",    "Bedroom",        "🛏"),
    ("주방",    "Kitchen",        "🍳"),
    ("욕실",    "Bathroom",       "🚿"),
    ("현관",    "Entrance",       "🚪"),
    ("드레스룸","Dressing Room",  "👗"),
    ("서재",    "Study Room",     "📚"),
    ("다이닝",  "Dining Room",    "🍽"),
    ("복도",    "Hallway",        "🔲"),
    ("발코니",  "Balcony",        "🌿"),
]
ROOM_PRESET_MAP = {ko: (en, icon) for ko, en, icon in ROOM_PRESETS}


# ── 세션 초기화 ──────────────────────────────────────────────────────────────
def _init_room_specbook():
    return {k: [] for k in CAT_KEYS}


if "rooms" not in st.session_state:
    st.session_state.rooms = []
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


def _add_room(ko: str, en: str):
    same = sum(1 for r in st.session_state.rooms if r["name"].startswith(ko))
    name = f"{ko}{same + 1}" if same else ko
    st.session_state.rooms.append({
        "id":       str(uuid.uuid4())[:8],
        "name":     name,
        "name_en":  en,
        "specbook": _init_room_specbook(),
    })
    st.rerun()


def _extract_spec(title: str) -> str:
    """제품명에서 치수 정보를 자동 추출."""
    m = re.search(
        r'\d+(?:\.\d+)?[\s]*[×xX\*][\s]*\d+(?:\.\d+)?'
        r'(?:[\s]*[×xX\*][\s]*\d+(?:\.\d+)?)?(?:[\s]*(?:mm|cm|m))?',
        title, re.IGNORECASE
    )
    if m:
        return m.group().strip()
    m = re.search(r'\d+(?:\.\d+)?[\s]*(?:mm|cm|m)', title, re.IGNORECASE)
    return m.group().strip() if m else ""


# ── 사이드바: 프로젝트 정보 ──────────────────────────────────────────────────
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

    # 추가된 공간 목록 (삭제 버튼만)
    if st.session_state.rooms:
        st.markdown("**추가된 공간**")
        for i, room in enumerate(st.session_state.rooms):
            total = sum(len(v) for v in room["specbook"].values())
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{room['name']}** <span style='color:#8C7F74;font-size:.75rem'>({total})</span>",
                        unsafe_allow_html=True)
            if c2.button("✕", key=f"dr{i}"):
                st.session_state.rooms.pop(i)
                st.rerun()

    st.markdown("---")
    total_items = sum(
        len(items)
        for room in st.session_state.rooms
        for items in room["specbook"].values()
    )
    st.markdown(f"<div style='text-align:center;color:#C8A97E;font-size:.85rem;font-weight:700'>"
                f"총 {len(st.session_state.rooms)}개 공간 · {total_items}개 자재</div>",
                unsafe_allow_html=True)


# ── 메인: 탭 (방별 + + 탭 + PPT 탭) ─────────────────────────────────────────
tab_labels = [r["name"] for r in st.session_state.rooms] + ["＋ 공간", "📄 PPT 생성"]
tabs = st.tabs(tab_labels)

# ── 공간 추가 탭 ──────────────────────────────────────────────────────────────
with tabs[-2]:
    st.markdown("#### 공간 추가")
    st.caption("아래 프리셋을 클릭하면 즉시 추가됩니다. 같은 공간은 번호가 자동으로 붙습니다.")

    # 프리셋 그리드 (5열)
    preset_cols = st.columns(5)
    for idx, (ko, en, icon) in enumerate(ROOM_PRESETS):
        with preset_cols[idx % 5]:
            if st.button(f"{icon}\n{ko}", key=f"preset_{ko}", use_container_width=True):
                _add_room(ko, en)

    st.markdown("---")
    st.markdown("**직접 입력**")
    c1, c2, c3 = st.columns([3, 3, 1])
    with c1:
        custom_ko = st.text_input("공간명 (한글)", placeholder="예: 홈짐", key="custom_ko")
    with c2:
        custom_en = st.text_input("공간명 (영어)", placeholder="Home Gym",  key="custom_en")
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
        total_room = sum(len(v) for v in room["specbook"].values())
        st.markdown(
            f'<div style="border-bottom:2px solid #1A1816;padding-bottom:8px;margin-bottom:16px;'
            f'display:flex;align-items:center;gap:10px;">'
            f'<span style="font-size:1rem;font-weight:700">{room["name"]}</span>'
            f'<span style="font-size:.75rem;color:#9A8F86">{room["name_en"]}</span>'
            f'<span style="margin-left:auto;font-size:.75rem;color:#C8A97E;font-weight:700">'
            f'{total_room}개 자재</span></div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns([3, 2], gap="large")

        # ── 왼쪽: 카테고리 + 검색 ─────────────────────────────────────────
        with left:
            st.markdown('<p class="sec-label">카테고리</p>', unsafe_allow_html=True)

            cat_key = f"cat_{ri}"
            if cat_key not in st.session_state:
                st.session_state[cat_key] = CAT_KEYS[0]

            # 카테고리 버튼 (3열 그리드)
            cat_cols = st.columns(3)
            for ci, ck in enumerate(CAT_KEYS):
                cat = CATEGORIES[ck]
                item_cnt = len(room["specbook"][ck])
                label = f"{cat['icon']} {ck}" + (f" ({item_cnt})" if item_cnt else "")
                is_active = st.session_state[cat_key] == ck
                with cat_cols[ci % 3]:
                    if st.button(label, key=f"catbtn_{ri}_{ck}",
                                 use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        st.session_state[cat_key] = ck
                        st.rerun()

            sel_cat = st.session_state[cat_key]
            sel_info = CATEGORIES[sel_cat]

            st.markdown(f"<div style='margin:8px 0 4px;font-size:.78rem;color:#8C7F74'>"
                        f"검색 예시: {', '.join(sel_info['include'][:4])}</div>",
                        unsafe_allow_html=True)

            # 검색창 + 버튼
            q_col, b_col = st.columns([5, 1])
            with q_col:
                query = st.text_input(
                    "검색어",
                    placeholder=f"{sel_info['include'][0]} / {sel_info['include'][1]} ...",
                    key=f"q_{ri}_{sel_cat}",
                    label_visibility="collapsed",
                )
            with b_col:
                do_search = st.button("검색", key=f"sb_{ri}_{sel_cat}",
                                      use_container_width=True, type="primary")

            result_key = f"results_{ri}_{sel_cat}"
            page_key   = f"page_{ri}_{sel_cat}"
            PAGE_SIZE  = 10
            MAX_COUNT  = 50

            if do_search and query:
                with st.spinner(f"'{query}' 검색 중 (최대 {MAX_COUNT}개)..."):
                    products = search_products(query, sel_cat, count=MAX_COUNT)
                st.session_state[result_key] = products
                st.session_state[page_key]   = 0  # 검색 시 첫 페이지로

            products = st.session_state.get(result_key, [])
            page     = st.session_state.get(page_key, 0)

            if products:
                total_pages = -(-len(products) // PAGE_SIZE)  # ceil
                page_start  = page * PAGE_SIZE
                page_items  = products[page_start: page_start + PAGE_SIZE]

                # 상단: 결과 수 + 페이지 네비
                hc1, hc2, hc3 = st.columns([3, 2, 3])
                with hc1:
                    lx_cnt = sum(1 for p in products if "LX" in (p.get("brand","") + p.get("mall","")))
                    st.markdown(
                        f"**{len(products)}개 결과**"
                        + (f" <span style='color:#C8A97E;font-size:.75rem'>(LX지인 {lx_cnt}개 포함)</span>"
                           if lx_cnt and sel_cat in {"벽","바닥","천장"} else ""),
                        unsafe_allow_html=True,
                    )
                with hc2:
                    st.markdown(
                        f"<div style='text-align:center;font-size:.78rem;color:#9A8F86'>"
                        f"{page+1} / {total_pages} 페이지</div>",
                        unsafe_allow_html=True,
                    )
                with hc3:
                    pc1, pc2 = st.columns(2)
                    with pc1:
                        if st.button("◀ 이전", key=f"prev_{ri}_{sel_cat}",
                                     disabled=(page == 0), use_container_width=True):
                            st.session_state[page_key] = page - 1
                            st.rerun()
                    with pc2:
                        if st.button("다음 ▶", key=f"next_{ri}_{sel_cat}",
                                     disabled=(page >= total_pages - 1), use_container_width=True):
                            st.session_state[page_key] = page + 1
                            st.rerun()

                existing_urls = {
                    it["source_url"]
                    for items in room["specbook"].values()
                    for it in items
                }

                for pi, prod in enumerate(page_items):
                    global_pi = page_start + pi
                    is_dup = prod["url"] in existing_urls
                    is_lx  = "LX" in (prod.get("brand","") + prod.get("mall",""))
                    with st.container():
                        ic, inf, ac = st.columns([1, 5, 2])
                        with ic:
                            if prod["image"]:
                                st.image(prod["image"], use_container_width=True)
                        with inf:
                            brand_tag = (
                                '<span style="background:#1A1816;color:#C8A97E;'
                                'font-size:.65rem;padding:1px 6px;border-radius:10px;'
                                'margin-right:4px">LX Z:IN</span>'
                                if is_lx else ""
                            )
                            st.markdown(
                                f'<div class="pcard-title">{brand_tag}{prod["title"][:42]}</div>'
                                f'<div class="pcard-price">{prod["price"]}</div>'
                                f'<div class="pcard-meta">'
                                f'{prod["brand"] or "브랜드 미상"}'
                                f' | {prod["mall"] or "판매처 미상"}</div>',
                                unsafe_allow_html=True,
                            )
                            if prod["url"]:
                                st.markdown(f"[🔗 상품 링크]({prod['url']})")
                        with ac:
                            if is_dup:
                                st.caption("✓ 추가됨")
                            else:
                                if st.button("＋ 추가", key=f"add_{ri}_{sel_cat}_{global_pi}",
                                             use_container_width=True, type="primary"):
                                    auto_spec = _extract_spec(prod["title"])
                                    new_item = {
                                        "id":           str(uuid.uuid4())[:8],
                                        "category":     sel_cat,
                                        "name":         prod["title"],
                                        "brand":        prod["brand"] or "",
                                        "maker":        prod["maker"] or "",
                                        "supplier":     prod["mall"] or "",
                                        "price":        prod["price"],
                                        "price_int":    prod["price_int"],
                                        "image_url":    prod["image"],
                                        "source_url":   prod["url"],
                                        "material":     "",
                                        "color":        "",
                                        "size":         auto_spec,
                                        "model_number": "",
                                        "unit":         "EA",
                                        "qty":          1,
                                        "location":     "",
                                        "memo":         "",
                                        "item_code":    sel_info["item_code"],
                                        "is_common":    False,
                                        "source":       "lxzin" if is_lx else "naver",
                                        "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    }
                                    room["specbook"][sel_cat].append(new_item)
                                    st.rerun()
                        st.markdown(
                            "<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>",
                            unsafe_allow_html=True,
                        )

                # 하단 페이지 버튼
                bc1, bc2, bc3 = st.columns([3, 2, 3])
                with bc1:
                    if st.button("◀ 이전 ", key=f"prev2_{ri}_{sel_cat}",
                                 disabled=(page == 0), use_container_width=True):
                        st.session_state[page_key] = page - 1
                        st.rerun()
                with bc3:
                    if st.button(" 다음 ▶", key=f"next2_{ri}_{sel_cat}",
                                 disabled=(page >= total_pages - 1), use_container_width=True):
                        st.session_state[page_key] = page + 1
                        st.rerun()

            elif do_search and query and not products:
                st.warning(
                    "⚠️ 전문 시공용 자재 결과가 부족합니다.\n\n"
                    "검색어를 더 구체화해주세요.  \n"
                    "예) '실크' → '실크벽지 시공'  |  '타일' → '포세린타일 600x600'  |  '조명' → '매입등 다운라이트'"
                )

        # ── 오른쪽: 추가된 자재 목록 ──────────────────────────────────────
        with right:
            st.markdown('<p class="sec-label">추가된 자재</p>', unsafe_allow_html=True)

            if total_room == 0:
                st.caption("왼쪽에서 검색 후 추가하세요.")
            else:
                for ck in CAT_KEYS:
                    items = room["specbook"][ck]
                    if not items:
                        continue
                    cat_info = CATEGORIES[ck]
                    st.markdown(
                        f'<span class="badge badge-{ck}">{cat_info["icon"]} {ck} {len(items)}</span>',
                        unsafe_allow_html=True,
                    )
                    for ii, item in enumerate(items):
                        # 컴팩트 행
                        c_img, c_info, c_act = st.columns([1, 5, 2])
                        with c_img:
                            if item.get("image_url"):
                                st.image(item["image_url"], use_container_width=True)
                            else:
                                st.markdown(
                                    f'<div class="item-thumb-ph">{cat_info["icon"]}</div>',
                                    unsafe_allow_html=True,
                                )
                        with c_info:
                            st.markdown(
                                f'<div class="item-name">{item["name"][:28]}</div>'
                                f'<div class="item-price">{item["price"]}</div>'
                                f'<div class="item-meta">{item.get("brand","")}'
                                + (f' | {item["size"]}' if item.get("size") else "")
                                + "</div>",
                                unsafe_allow_html=True,
                            )
                        with c_act:
                            # 공통 자재 토글
                            is_common = item.get("is_common", False)
                            if st.button(
                                "⭐" if is_common else "☆",
                                key=f"common_{ri}_{ck}_{ii}",
                                help="공통 자재(슬라이드4)로 지정/해제",
                            ):
                                item["is_common"] = not is_common
                                st.rerun()
                            if st.button("🗑", key=f"del_{ri}_{ck}_{ii}"):
                                room["specbook"][ck].pop(ii)
                                st.rerun()

                        # 상세 편집 (expander)
                        with st.expander("✏ 편집", expanded=False):
                            e1, e2 = st.columns(2)
                            with e1:
                                item["name"]     = st.text_input("제품명",  item["name"],    key=f"en_{ri}_{ck}_{ii}")
                                item["brand"]    = st.text_input("브랜드",  item["brand"],   key=f"eb_{ri}_{ck}_{ii}")
                                item["supplier"] = st.text_input("판매처",  item["supplier"],key=f"es_{ri}_{ck}_{ii}")
                                item["price"]    = st.text_input("가격",    item["price"],   key=f"ep_{ri}_{ck}_{ii}")
                                item["qty"]      = st.number_input("수량",  min_value=1, value=item.get("qty",1), key=f"eq_{ri}_{ck}_{ii}")
                            with e2:
                                item["size"]         = st.text_input("규격",  item.get("size",""),        key=f"esz_{ri}_{ck}_{ii}")
                                item["color"]        = st.text_input("색상",  item.get("color",""),       key=f"ec_{ri}_{ck}_{ii}")
                                item["material"]     = st.text_input("재질",  item.get("material",""),    key=f"em_{ri}_{ck}_{ii}")
                                item["model_number"] = st.text_input("품번",  item.get("model_number",""),key=f"emn_{ri}_{ck}_{ii}")
                                item["unit"]         = st.text_input("단위",  item.get("unit","EA"),      key=f"eu_{ri}_{ck}_{ii}")
                            item["location"] = st.text_input(
                                "적용 위치", item.get("location",""),
                                placeholder="예: 거실 벽면",
                                key=f"el_{ri}_{ck}_{ii}",
                            )
                            item["memo"] = st.text_area(
                                "비고", item.get("memo",""),
                                key=f"emm_{ri}_{ck}_{ii}", height=56,
                            )
                            if item.get("source_url"):
                                st.markdown(f"[🔗 상품 페이지]({item['source_url']})")

                        st.markdown(
                            "<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>",
                            unsafe_allow_html=True,
                        )


# ── PPT 생성 탭 ──────────────────────────────────────────────────────────────
with tabs[-1]:
    st.markdown('<p class="sec-label">Export</p>', unsafe_allow_html=True)

    total_all = sum(
        len(items)
        for room in st.session_state.rooms
        for items in room["specbook"].values()
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("공간 수", len(st.session_state.rooms))
    m2.metric("총 자재 수", total_all)
    common_cnt = sum(
        1
        for room in st.session_state.rooms
        for items in room["specbook"].values()
        for it in items
        if it.get("is_common")
    )
    m3.metric("공통 자재 (슬라이드4)", common_cnt)

    # 공통 자재 목록
    if common_cnt:
        st.markdown("**⭐ 공통 자재 (슬라이드 4 반영)**")
        for room in st.session_state.rooms:
            for ck, items in room["specbook"].items():
                for it in items:
                    if it.get("is_common"):
                        cat = CATEGORIES[ck]
                        st.markdown(
                            f'&nbsp;&nbsp;<span class="badge badge-{ck}">{cat["icon"]} {ck}</span>'
                            f'&nbsp;{it["name"][:30]}&nbsp;'
                            f'<span style="color:#C8A97E">{it["price"]}</span>',
                            unsafe_allow_html=True,
                        )

    st.markdown("---")

    # 공간별 요약
    for room in st.session_state.rooms:
        room_total = sum(len(v) for v in room["specbook"].values())
        if not room_total:
            continue
        st.markdown(f"**{room['name']}** ({room_total}개)")
        for ck, items in room["specbook"].items():
            if items:
                cat = CATEGORIES[ck]
                names = " · ".join(it["name"][:16] for it in items[:3])
                st.markdown(
                    f'&nbsp;&nbsp;<span class="badge badge-{ck}">{cat["icon"]} {ck}</span>'
                    f'&nbsp;{names}{"..." if len(items) > 3 else ""}',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # JSON 내보내기
    col_j, col_p, _ = st.columns([2, 2, 3])
    export_data = {
        "project": st.session_state.project,
        "rooms": [
            {
                "name":    room["name"],
                "name_en": room["name_en"],
                "items": [
                    it
                    for items in room["specbook"].values()
                    for it in items
                ],
            }
            for room in st.session_state.rooms
        ],
    }
    with col_j:
        st.download_button(
            "📊 JSON 내보내기",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name=f"{st.session_state.project['name']}_specbook.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_p:
        if st.button("🎨 PPT 스펙북 생성", type="primary",
                     use_container_width=True, disabled=total_all == 0):
            # 공통 자재 수집
            common_materials = [
                {
                    "item_code": it["item_code"],
                    "product":   it["name"],
                    "spec":      it.get("size", ""),
                    "finish":    it.get("material", "") or it.get("color", ""),
                    "vendor":    it.get("supplier", ""),
                    "location":  it.get("location", ""),
                }
                for room in st.session_state.rooms
                for items in room["specbook"].values()
                for it in items
                if it.get("is_common")
            ][:6]

            # PPT용 room 구조
            ppt_rooms = []
            for room in st.session_state.rooms:
                all_items = []
                for ck, items in room["specbook"].items():
                    for it in items:
                        finish = it.get("material", "") or it.get("color", "")
                        all_items.append({
                            "item_code":  it["item_code"],
                            "product":    it["name"],
                            "spec":       it.get("size", ""),
                            "finish":     finish,
                            "vendor":     it.get("supplier", ""),
                            "qty":        it.get("qty", 1),
                            "note":       it.get("memo", ""),
                            "price":      it["price"],
                            "image_url":  it.get("image_url", ""),
                            "source_url": it.get("source_url", ""),
                            "room":       room["name"],
                        })
                if all_items:
                    ppt_rooms.append({
                        "name":    room["name"],
                        "name_en": room["name_en"],
                        "items":   all_items,
                    })

            with st.spinner("PPT 생성 중..."):
                pptx_bytes = generate_pptx(
                    st.session_state.project,
                    ppt_rooms,
                    common_materials,
                )

            st.download_button(
                "⬇️ PPT 다운로드",
                data=pptx_bytes,
                file_name=f"{st.session_state.project['name']}_스펙북.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
            st.success("✓ 생성 완료!")

    if total_all == 0:
        st.caption("각 공간 탭에서 자재를 추가한 뒤 생성하세요.")
