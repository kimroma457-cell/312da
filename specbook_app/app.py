"""
인테리어 스펙북 생성기 — 카테고리별 자재 검색 + 네이버 쇼핑 API
"""
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

.top-bar{background:#1A1816;padding:18px 28px;margin:-1rem -1rem 1.5rem -1rem;}
.top-bar h1{color:#fff;font-size:1.35rem;font-weight:700;margin:0;letter-spacing:1px;}
.top-bar .sub{color:#8C7F74;font-size:.78rem;margin:3px 0 0;}
.gold{color:#C8A97E;}

/* 카테고리 그리드 */
.cat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));
          gap:8px;margin-bottom:16px;}
.cat-btn{background:#fff;border:1.5px solid #E8E2DC;border-radius:10px;
         padding:10px 6px;text-align:center;cursor:pointer;
         font-size:.78rem;font-weight:600;color:#4A4540;transition:.15s;}
.cat-btn:hover{border-color:#C8A97E;color:#C8A97E;}
.cat-btn.active{background:#1A1816;border-color:#1A1816;color:#C8A97E;}

/* 상품 카드 */
.pcard{background:#fff;border:1.5px solid #E8E2DC;border-radius:10px;
       padding:14px;margin-bottom:10px;transition:.15s;}
.pcard:hover{border-color:#C8A97E;box-shadow:0 2px 10px rgba(0,0,0,.06);}
.pcard-title{font-size:.9rem;font-weight:700;color:#1A1816;margin-bottom:4px;line-height:1.35;}
.pcard-price{font-size:1rem;font-weight:700;color:#C8A97E;margin:3px 0;}
.pcard-meta{font-size:.73rem;color:#9A8F86;margin:2px 0;}
.pcard-cat{font-size:.68rem;color:#B8AFA8;background:#F5F3F0;
           padding:2px 7px;border-radius:20px;display:inline-block;margin-top:4px;}

/* 자재 항목 */
.item-row{background:#fff;border:1px solid #E8E2DC;border-radius:10px;
          padding:14px 16px;margin-bottom:8px;}
.item-title{font-size:.88rem;font-weight:700;color:#1A1816;}
.item-meta{font-size:.75rem;color:#9A8F86;}
.item-price{font-size:.88rem;font-weight:700;color:#C8A97E;}

/* 배지 */
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.68rem;font-weight:700;}
.badge-벽   {background:#E3F2FD;color:#1565C0;}
.badge-바닥  {background:#E8F5E9;color:#2E7D32;}
.badge-천장  {background:#FFF8E1;color:#F57F17;}
.badge-조명  {background:#FFF9C4;color:#F9A825;}
.badge-욕실  {background:#E0F7FA;color:#006064;}
.badge-주방  {background:#FCE4EC;color:#880E4F;}
.badge-가구  {background:#F3E5F5;color:#4A148C;}
.badge-전기  {background:#FBE9E7;color:#BF360C;}
.badge-기타  {background:#EFEBE9;color:#4E342E;}

.sec-label{font-size:.65rem;font-weight:700;letter-spacing:2px;
           text-transform:uppercase;color:#C8A97E;margin-bottom:8px;}
.room-header{border-bottom:2px solid #1A1816;padding-bottom:8px;margin-bottom:20px;}

section[data-testid="stSidebar"]{background:#1A1816!important;}
section[data-testid="stSidebar"] *{color:#E8E2DC!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:#2C2A28!important;border:1px solid #3C3A38!important;
  color:#C8A97E!important;border-radius:6px!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:#C8A97E!important;color:#1A1816!important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] select{
  background:#2C2A28!important;border-color:#3C3A38!important;color:#E8E2DC!important;}

.stTabs [data-baseweb="tab-list"]{background:#EEEBE6;padding:4px;border-radius:10px;gap:3px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:600;font-size:.82rem;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;}

div[data-testid="stButton"]>button[kind="primary"]{
  background:#1A1816!important;color:#C8A97E!important;border:none!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-bar">
  <h1>INTERIOR <span class="gold">SPEC BOOK</span> GENERATOR</h1>
  <div class="sub">카테고리 선택 → 자재 검색 → 스펙북 추가 → PPT 생성</div>
</div>
""", unsafe_allow_html=True)

# ── 세션 초기화 ──────────────────────────────────────────────────────────────────
CAT_KEYS = list(CATEGORIES.keys())

def _init_room_specbook():
    """공간별 카테고리 스펙북 초기 구조."""
    return {k: [] for k in CAT_KEYS}

if "rooms"   not in st.session_state: st.session_state.rooms   = []
if "project" not in st.session_state:
    st.session_state.project = {
        "name":"○○ 아파트 리모델링","location":"서울시 강남구",
        "area":"84㎡ (25.4평)","period":"2026.07 ~ 2026.08",
        "designer":"홍길동","date":"2026.06.17",
    }

ROOM_PRESETS = {
    "거실":"Living Room","침실":"Bedroom","주방":"Kitchen",
    "욕실":"Bathroom","현관":"Entrance","드레스룸":"Dressing Room",
    "서재":"Study Room","다이닝":"Dining Room",
}

# ── 사이드바 ────────────────────────────────────────────────────────────────────
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
    st.caption("같은 공간 여러 번 추가 가능 (침실1·침실2 등)")
    preset = st.selectbox("공간 선택", list(ROOM_PRESETS.keys()) + ["직접 입력"])
    if preset == "직접 입력":
        add_ko = st.text_input("공간명(한글)", key="cko")
        add_en = st.text_input("공간명(영어)", key="cen")
    else:
        add_ko, add_en = preset, ROOM_PRESETS[preset]
    same = sum(1 for r in st.session_state.rooms if r["name"].startswith(add_ko))
    disp = f"{add_ko}{same+1}" if same else add_ko
    if st.button("＋ 공간 추가", use_container_width=True):
        if add_ko:
            st.session_state.rooms.append({
                "id": str(uuid.uuid4())[:8],
                "name": disp, "name_en": add_en,
                "specbook": _init_room_specbook(),
            })
            st.rerun()
    if st.session_state.rooms:
        st.markdown("---")
        st.markdown("**추가된 공간**")
        for i, room in enumerate(st.session_state.rooms):
            total = sum(len(v) for v in room["specbook"].values())
            c1, c2 = st.columns([4,1])
            c1.markdown(f"• {room['name']} ({total}개)")
            if c2.button("✕", key=f"dr{i}"):
                st.session_state.rooms.pop(i); st.rerun()

if not st.session_state.rooms:
    st.info("👈 왼쪽 사이드바에서 공간을 추가하세요.")
    st.stop()

# ── 메인 탭 ────────────────────────────────────────────────────────────────────
tabs = st.tabs([r["name"] for r in st.session_state.rooms] + ["📄 PPT 생성"])

for ri, (tab, room) in enumerate(zip(tabs[:-1], st.session_state.rooms)):
    with tab:
        st.markdown(
            f'<div class="room-header">'
            f'<span style="font-size:1rem;font-weight:700">{room["name"]}</span>'
            f'<span style="font-size:.75rem;color:#9A8F86;margin-left:8px">{room["name_en"]}</span>'
            f'</div>', unsafe_allow_html=True)

        # ── 좌우 분할: 검색(왼) / 스펙북 목록(오) ──────────────────────────
        left, right = st.columns([3, 2], gap="large")

        with left:
            # 카테고리 선택
            st.markdown('<p class="sec-label">카테고리 선택</p>', unsafe_allow_html=True)
            cat_key = f"cat_{ri}"
            if cat_key not in st.session_state:
                st.session_state[cat_key] = CAT_KEYS[0]

            # 카테고리 버튼 그리드 (3열)
            cat_cols = st.columns(3)
            for ci, ck in enumerate(CAT_KEYS):
                cat = CATEGORIES[ck]
                is_active = st.session_state[cat_key] == ck
                with cat_cols[ci % 3]:
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(
                        f"{cat['icon']} {ck}",
                        key=f"catbtn_{ri}_{ck}",
                        use_container_width=True,
                        type=btn_type,
                    ):
                        st.session_state[cat_key] = ck
                        st.rerun()

            sel_cat = st.session_state[cat_key]
            sel_cat_info = CATEGORIES[sel_cat]

            st.markdown(f"**{sel_cat_info['icon']} {sel_cat}** — {sel_cat_info['name_en']}")
            st.caption(f"검색 예시: {', '.join(sel_cat_info['include'][:4])}")

            # 검색창
            q_col, b_col = st.columns([5, 1])
            with q_col:
                query = st.text_input(
                    "검색어",
                    placeholder=f"예: {sel_cat_info['include'][0]}, {sel_cat_info['include'][1]}",
                    key=f"q_{ri}_{sel_cat}",
                    label_visibility="collapsed",
                )
            with b_col:
                do_search = st.button("검색", key=f"sb_{ri}_{sel_cat}",
                                      use_container_width=True, type="primary")

            # 검색 실행
            result_key = f"results_{ri}_{sel_cat}"
            if do_search and query:
                with st.spinner(f"'{query}' 검색 중..."):
                    products = search_products(query, sel_cat, count=8, sort="sim")
                st.session_state[result_key] = products

            # 검색 결과 표시
            products = st.session_state.get(result_key, [])
            if products:
                st.markdown(f"**검색 결과 {len(products)}개**")
                for pi, prod in enumerate(products):
                    with st.container():
                        # 중복 체크
                        existing_urls = [
                            it["source_url"]
                            for items in room["specbook"].values()
                            for it in items
                        ]
                        is_dup = prod["url"] in existing_urls

                        img_c, info_c = st.columns([1, 4])
                        with img_c:
                            if prod["image"]:
                                st.image(prod["image"], use_container_width=True)
                        with info_c:
                            st.markdown(
                                f'<div class="pcard-title">{prod["title"]}</div>'
                                f'<div class="pcard-price">{prod["price"]}</div>'
                                f'<div class="pcard-meta">브랜드: {prod["brand"] or "정보 없음"}'
                                f' &nbsp;|&nbsp; 판매처: {prod["mall"] or "정보 없음"}</div>'
                                f'<span class="pcard-cat">{prod["category"] or sel_cat}</span>',
                                unsafe_allow_html=True,
                            )
                            if prod["url"]:
                                st.markdown(f"[🔗 상품 페이지]({prod['url']})")

                        if is_dup:
                            st.caption("✓ 이미 스펙북에 추가된 자재입니다.")
                        else:
                            if st.button(f"+ 스펙북 추가", key=f"add_{ri}_{sel_cat}_{pi}",
                                         use_container_width=True):
                                new_item = {
                                    "id":          str(uuid.uuid4())[:8],
                                    "category":    sel_cat,
                                    "name":        prod["title"],
                                    "brand":       prod["brand"] or "",
                                    "maker":       prod["maker"] or "",
                                    "supplier":    prod["mall"] or "",
                                    "price":       prod["price"],
                                    "price_int":   prod["price_int"],
                                    "image_url":   prod["image"],
                                    "source_url":  prod["url"],
                                    "material":    "",
                                    "color":       "",
                                    "size":        "",
                                    "model_number":"",
                                    "unit":        "",
                                    "location":    "",
                                    "memo":        "",
                                    "item_code":   sel_cat_info["item_code"],
                                    "source":      "naver",
                                    "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
                                }
                                room["specbook"][sel_cat].append(new_item)
                                st.session_state[result_key] = []
                                st.success(f"✓ '{prod['title'][:25]}' 추가됨!")
                                st.rerun()

                        st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>",
                                    unsafe_allow_html=True)

            elif do_search and query and not products:
                st.warning("검색 결과가 없습니다. 자재명·브랜드·품번을 좀 더 구체적으로 입력해주세요.")

        # ── 오른쪽: 카테고리별 스펙북 목록 ────────────────────────────────
        with right:
            st.markdown('<p class="sec-label">추가된 자재</p>', unsafe_allow_html=True)
            total_room = sum(len(v) for v in room["specbook"].values())
            if total_room == 0:
                st.caption("왼쪽에서 자재를 검색해 추가하세요.")
            else:
                for ck in CAT_KEYS:
                    items = room["specbook"][ck]
                    if not items:
                        continue
                    cat_info = CATEGORIES[ck]
                    st.markdown(f"**{cat_info['icon']} {ck}** ({len(items)})")
                    for ii, item in enumerate(items):
                        with st.expander(f"{item['name'][:30]}  |  {item['price']}", expanded=False):
                            # 수정 가능 폼
                            e1, e2 = st.columns(2)
                            with e1:
                                item["name"]     = st.text_input("제품명",    item["name"],    key=f"e_name_{ri}_{ck}_{ii}")
                                item["brand"]    = st.text_input("브랜드",    item["brand"],   key=f"e_brand_{ri}_{ck}_{ii}")
                                item["maker"]    = st.text_input("제조사",    item["maker"],   key=f"e_maker_{ri}_{ck}_{ii}")
                                item["supplier"] = st.text_input("판매처",    item["supplier"],key=f"e_sup_{ri}_{ck}_{ii}")
                                item["price"]    = st.text_input("가격",      item["price"],   key=f"e_price_{ri}_{ck}_{ii}")
                            with e2:
                                item["size"]         = st.text_input("규격",     item["size"],        key=f"e_size_{ri}_{ck}_{ii}")
                                item["color"]        = st.text_input("색상",     item["color"],       key=f"e_color_{ri}_{ck}_{ii}")
                                item["material"]     = st.text_input("재질",     item["material"],    key=f"e_mat_{ri}_{ck}_{ii}")
                                item["model_number"] = st.text_input("품번",     item["model_number"],key=f"e_model_{ri}_{ck}_{ii}")
                                item["unit"]         = st.text_input("단위",     item["unit"],        key=f"e_unit_{ri}_{ck}_{ii}")
                            item["location"] = st.text_input("적용 위치",
                                item["location"], placeholder="예: 거실 벽, 안방 바닥",
                                key=f"e_loc_{ri}_{ck}_{ii}")
                            item["memo"] = st.text_area("비고", item["memo"],
                                key=f"e_memo_{ri}_{ck}_{ii}", height=60)
                            if item.get("image_url"):
                                st.image(item["image_url"], width=120)
                            if item.get("source_url"):
                                st.markdown(f"[🔗 상품 페이지]({item['source_url']})")
                            st.caption(f"추가일: {item['created_at']}")
                            if st.button("🗑 삭제", key=f"del_{ri}_{ck}_{ii}"):
                                room["specbook"][ck].pop(ii)
                                st.rerun()

# ── PPT 생성 탭 ─────────────────────────────────────────────────────────────────
with tabs[-1]:
    st.markdown('<p class="sec-label">Export Summary</p>', unsafe_allow_html=True)

    total_all = sum(
        len(items)
        for room in st.session_state.rooms
        for items in room["specbook"].values()
    )
    m1, m2 = st.columns(2)
    m1.metric("공간 수", len(st.session_state.rooms))
    m2.metric("총 자재 수", total_all)

    # 요약표
    for room in st.session_state.rooms:
        room_total = sum(len(v) for v in room["specbook"].values())
        if not room_total:
            continue
        st.markdown(f"**{room['name']}** ({room_total}개)")
        for ck, items in room["specbook"].items():
            if items:
                cat = CATEGORIES[ck]
                names = " · ".join(it["name"][:18] for it in items[:3])
                st.markdown(
                    f'&nbsp;&nbsp;<span class="badge badge-{ck}">{cat["icon"]} {ck}</span>'
                    f'&nbsp;{names}{"..." if len(items)>3 else ""}',
                    unsafe_allow_html=True)

    # JSON 내보내기
    st.markdown("---")
    export_data = [
        {
            "room": room["name"],
            "room_en": room["name_en"],
            "items": [it for items in room["specbook"].values() for it in items],
        }
        for room in st.session_state.rooms
    ]
    st.download_button(
        "📊 JSON 데이터 내보내기",
        data=json.dumps(export_data, ensure_ascii=False, indent=2),
        file_name=f"{st.session_state.project['name']}_specbook.json",
        mime="application/json",
    )

    # PPT 생성
    st.markdown("---")
    col, _ = st.columns([2, 3])
    with col:
        if st.button("🎨 PPT 스펙북 생성", type="primary",
                     use_container_width=True, disabled=total_all == 0):
            # PPT용 room 구조로 변환
            ppt_rooms = []
            for room in st.session_state.rooms:
                all_items = []
                for ck, items in room["specbook"].items():
                    for it in items:
                        all_items.append({
                            "item_code":  it["item_code"],
                            "item_label": it["name"],
                            "tier":       it.get("location", ck),
                            "product":    it["name"],
                            "spec":       it.get("size",""),
                            "finish":     it.get("material","") or it.get("color",""),
                            "vendor":     it.get("supplier",""),
                            "price":      it["price"],
                            "image_url":  it["image_url"],
                            "source_url": it["source_url"],
                        })
                if all_items:
                    ppt_rooms.append({
                        "name":    room["name"],
                        "name_en": room["name_en"],
                        "items":   all_items,
                    })

            with st.spinner("PPT 생성 중..."):
                pptx_bytes = generate_pptx(st.session_state.project, ppt_rooms)

            st.download_button(
                "⬇️ PPT 다운로드",
                data=pptx_bytes,
                file_name=f"{st.session_state.project['name']}_스펙북.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
            st.success("생성 완료!")

    if total_all == 0:
        st.caption("각 공간 탭에서 자재를 추가한 뒤 생성하세요.")
