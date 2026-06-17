"""
인테리어 스펙북 생성기 — 네이버 쇼핑 검색 기반
"""
import streamlit as st
from naver_shopping import search_products
from pptx_generator import generate_pptx

st.set_page_config(page_title="스펙북 생성기", page_icon="🏠",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;}
.stApp{background:#F7F5F2;}
#MainMenu,footer,header{visibility:hidden;}

.top-bar{background:#1A1816;padding:20px 28px;margin:-1rem -1rem 1.5rem -1rem;}
.top-bar h1{color:#fff;font-size:1.4rem;font-weight:700;margin:0;letter-spacing:1px;}
.top-bar .sub{color:#8C7F74;font-size:0.78rem;margin:3px 0 0;}
.gold{color:#C8A97E;}

.product-card{background:#fff;border:1.5px solid #E8E2DC;border-radius:10px;
              padding:14px;margin-bottom:8px;transition:.15s;}
.product-card:hover{border-color:#C8A97E;box-shadow:0 2px 10px rgba(0,0,0,.07);}
.product-card.selected{border-color:#1A1816;background:#F7F5F2;}
.prod-title{font-size:.92rem;font-weight:700;color:#1A1816;margin-bottom:4px;}
.prod-price{font-size:1rem;font-weight:700;color:#C8A97E;}
.prod-brand{font-size:.75rem;color:#9A8F86;}
.prod-mall{font-size:.72rem;color:#B8AFA8;}

.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:700;}
.badge-최저가{background:#E8F5E9;color:#2E7D32;}
.badge-보통  {background:#FFF8E1;color:#F57F17;}
.badge-최고가{background:#F3E5F5;color:#7B1FA2;}

.sec-label{font-size:.65rem;font-weight:700;letter-spacing:2px;
           text-transform:uppercase;color:#C8A97E;margin-bottom:8px;}
.room-header{border-bottom:2px solid #1A1816;padding-bottom:8px;margin-bottom:16px;}

section[data-testid="stSidebar"]{background:#1A1816!important;}
section[data-testid="stSidebar"] *{color:#E8E2DC!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:#2C2A28!important;border:1px solid #3C3A38!important;
  color:#C8A97E!important;border-radius:6px!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:#C8A97E!important;color:#1A1816!important;}
section[data-testid="stSidebar"] input{
  background:#2C2A28!important;border-color:#3C3A38!important;color:#E8E2DC!important;}

.stTabs [data-baseweb="tab-list"]{background:#EEEBE6;padding:4px;border-radius:10px;gap:3px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:600;font-size:.83rem;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1A1816!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-bar">
  <h1>INTERIOR <span class="gold">SPEC BOOK</span> GENERATOR</h1>
  <div class="sub">네이버 쇼핑 검색으로 실제 제품 · 가격 · 업체를 찾아 스펙북을 만듭니다</div>
</div>
""", unsafe_allow_html=True)

# ── 세션 ────────────────────────────────────────────────────────────────────────
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
TIERS = ["최저가","보통","최고가"]
TIER_SORT = {"최저가":"asc","보통":"sim","최고가":"dsc"}

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
    st.caption("같은 공간 여러 번 추가 가능")
    preset = st.selectbox("공간 선택", list(ROOM_PRESETS.keys()) + ["직접 입력"])
    if preset == "직접 입력":
        add_ko = st.text_input("공간명 (한글)", key="cko")
        add_en = st.text_input("공간명 (영어)", key="cen")
    else:
        add_ko, add_en = preset, ROOM_PRESETS[preset]
    same = sum(1 for r in st.session_state.rooms if r["name"].startswith(add_ko))
    disp = f"{add_ko}{same+1}" if same else add_ko
    if st.button("＋ 공간 추가", use_container_width=True):
        if add_ko:
            st.session_state.rooms.append({"id":len(st.session_state.rooms),
                "name":disp,"name_en":add_en,"items":[]})
            st.rerun()
    if st.session_state.rooms:
        st.markdown("---")
        st.markdown("**추가된 공간**")
        for i,room in enumerate(st.session_state.rooms):
            c1,c2 = st.columns([4,1])
            c1.markdown(f"• {room['name']}")
            if c2.button("✕",key=f"dr{i}"):
                st.session_state.rooms.pop(i); st.rerun()

if not st.session_state.rooms:
    st.info("👈 왼쪽 사이드바에서 공간을 추가하세요.")
    st.stop()

tabs = st.tabs([r["name"] for r in st.session_state.rooms] + ["📄 PPT 생성"])

# ── 공간별 탭 ───────────────────────────────────────────────────────────────────
for ti, (tab, room) in enumerate(zip(tabs[:-1], st.session_state.rooms)):
    with tab:
        st.markdown(f'<div class="room-header"><span style="font-size:1rem;font-weight:700">'
                    f'{room["name"]}</span> <span style="font-size:.75rem;color:#9A8F86">'
                    f'{room["name_en"]}</span></div>', unsafe_allow_html=True)

        with st.expander("🔍 자재 검색", expanded=len(room["items"])==0):
            q_col, t_col, b_col = st.columns([4, 2, 1])
            with q_col:
                query = st.text_input("검색어", placeholder="예: 오크 강마루, 펜던트 조명, 패브릭 소파",
                                      key=f"q{ti}", label_visibility="collapsed")
            with t_col:
                tier_filter = st.selectbox("가격대", TIERS, index=1,
                                           key=f"tf{ti}", label_visibility="collapsed")
            with b_col:
                do_search = st.button("검색", key=f"sb{ti}",
                                      use_container_width=True, type="primary")

            if do_search and query:
                sort = TIER_SORT[tier_filter]
                with st.spinner(f"네이버 쇼핑에서 '{query}' 검색 중..."):
                    products = search_products(query, count=10, sort=sort)

                if not products:
                    st.warning("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
                else:
                    st.markdown(f"**{len(products)}개 상품** — 원하는 상품을 선택하세요")
                    for pi, prod in enumerate(products):
                        with st.container():
                            img_c, info_c, btn_c = st.columns([1, 5, 1])
                            with img_c:
                                if prod["image"]:
                                    st.image(prod["image"], use_container_width=True)
                            with info_c:
                                st.markdown(
                                    f'<div class="prod-title">{prod["title"]}</div>'
                                    f'<div class="prod-price">{prod["price"]}</div>'
                                    f'<div class="prod-brand">{prod["brand"]} &nbsp;|&nbsp; '
                                    f'<span class="prod-mall">{prod["mall"]}</span></div>'
                                    f'<div style="font-size:.72rem;color:#9A8F86">{prod["category"]}</div>',
                                    unsafe_allow_html=True)
                                if prod["url"]:
                                    st.markdown(f'[🔗 상품 페이지 바로가기]({prod["url"]})')
                            with btn_c:
                                if st.button("선택", key=f"sel{ti}_{pi}",
                                             use_container_width=True, type="primary"):
                                    room["items"].append({
                                        "item_code":  query[:8].upper().replace(" ",""),
                                        "item_label": prod["title"],
                                        "tier":       tier_filter,
                                        "product":    prod["title"],
                                        "spec":       prod["category"],
                                        "finish":     prod["brand"],
                                        "price":      prod["price"],
                                        "vendor":     prod["mall"],
                                        "image_url":  prod["image"],
                                        "source_url": prod["url"],
                                    })
                                    st.success(f"✓ 추가됨: {prod['title'][:30]}")
                                    st.rerun()
                        st.markdown("<hr style='border:none;border-top:1px solid #F0EBE4;margin:4px 0'>",
                                    unsafe_allow_html=True)

        # ── 선택된 자재 ────────────────────────────────────────────────────────
        if room["items"]:
            st.markdown(f'<p class="sec-label">선택된 자재 {len(room["items"])}개</p>',
                        unsafe_allow_html=True)
            for ii, item in enumerate(room["items"]):
                c1, c2, c3 = st.columns([1, 5, 1])
                with c1:
                    if item.get("image_url"):
                        st.image(item["image_url"], use_container_width=True)
                with c2:
                    badge = f'<span class="badge badge-{item["tier"]}">{item["tier"]}</span>'
                    st.markdown(
                        f'{badge}<br><strong>{item["product"]}</strong><br>'
                        f'<span style="font-size:.78rem;color:#9A8F86">{item.get("finish","")} · {item.get("vendor","")}</span><br>'
                        f'<span style="font-size:.9rem;font-weight:700;color:#C8A97E">{item.get("price","")}</span>',
                        unsafe_allow_html=True)
                    if item.get("source_url"):
                        st.caption(f"[🔗 상품 페이지]({item['source_url']})")
                with c3:
                    if st.button("삭제", key=f"del{ti}_{ii}"):
                        room["items"].pop(ii); st.rerun()
                st.markdown("<hr style='border:none;border-top:1px solid #EDE8E2;margin:6px 0'>",
                            unsafe_allow_html=True)
        else:
            st.caption("검색 후 상품을 선택하면 여기에 표시됩니다.")

# ── PPT 생성 탭 ─────────────────────────────────────────────────────────────────
with tabs[-1]:
    total = sum(len(r["items"]) for r in st.session_state.rooms)
    m1,m2 = st.columns(2)
    m1.metric("공간 수", len(st.session_state.rooms))
    m2.metric("자재 수", total)

    for room in st.session_state.rooms:
        if room["items"]:
            st.markdown(f"**{room['name']}**")
            for item in room["items"]:
                st.markdown(
                    f'<span class="badge badge-{item["tier"]}">{item["tier"]}</span> '
                    f'{item["product"][:40]} — {item["price"]}',
                    unsafe_allow_html=True)

    st.markdown("---")
    col,_ = st.columns([2,3])
    with col:
        if st.button("🎨 PPT 스펙북 생성", type="primary",
                     use_container_width=True, disabled=total==0):
            with st.spinner("PPT 생성 중..."):
                pptx_bytes = generate_pptx(st.session_state.project,
                                           st.session_state.rooms)
            st.download_button("⬇️ PPT 다운로드", data=pptx_bytes,
                file_name=f"{st.session_state.project['name']}_스펙북.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True)
            st.success("생성 완료!")
    if total==0:
        st.caption("각 공간 탭에서 상품을 선택한 뒤 생성하세요.")
