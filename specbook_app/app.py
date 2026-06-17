"""
인테리어 스펙북 자동 생성기
Streamlit app — 프로젝트 정보 입력 → 공간별 자재 등급 선택 → PPT 자동 생성
"""
import streamlit as st
from image_search import search_image
from materials_db import DB, SPACE_ITEMS, TIERS
from pptx_generator import generate_pptx

st.set_page_config(page_title="인테리어 스펙북 생성기", page_icon="🏠", layout="wide")

st.title("🏠 인테리어 스펙북 자동 생성기")
st.caption("공간별 자재 등급(최저가/보통/최고가)을 선택하면 AI가 제품을 추천하고 PPT를 생성합니다.")

# ── 1. 프로젝트 기본 정보 ──────────────────────────────────────────────────────
with st.expander("📋 프로젝트 정보 입력", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        proj_name = st.text_input("프로젝트명", "○○ 아파트 리모델링")
        proj_location = st.text_input("위치", "서울시 강남구")
        proj_area = st.text_input("면적", "84㎡ (25.4평)")
    with c2:
        proj_period = st.text_input("공사기간", "2026.07.01 ~ 2026.08.15")
        proj_designer = st.text_input("담당자", "홍길동")
        proj_date = st.text_input("작성일", "2026.06.17")

project = {
    "name": proj_name, "location": proj_location, "area": proj_area,
    "period": proj_period, "designer": proj_designer, "date": proj_date,
}

st.divider()

# ── 2. 공간 선택 ────────────────────────────────────────────────────────────────
spaces = list(SPACE_ITEMS.keys())
selected_spaces = st.multiselect("적용할 공간 선택", spaces, default=spaces[:3])

st.divider()

# ── 3. 공간별 자재 등급 선택 + 미리보기 ─────────────────────────────────────────
if "selections" not in st.session_state:
    st.session_state.selections = {}  # {space: {item: {tier, product, ...}}}

if "images" not in st.session_state:
    st.session_state.images = {}      # {space_item_key: [{url, page}]}

TIER_EMOJI = {"최저가": "🟢", "보통": "🟡", "최고가": "🟣"}
TIER_DESC  = {"최저가": "합리적 가격대", "보통": "중급 품질", "최고가": "프리미엄"}

for space in selected_spaces:
    st.subheader(f"🏡 {space}")
    items = SPACE_ITEMS[space]
    if space not in st.session_state.selections:
        st.session_state.selections[space] = {}

    for item in items:
        key = f"{space}_{item}"
        st.markdown(f"**{item}**")
        cols = st.columns([1, 1, 1, 5])

        chosen_tier = st.session_state.selections[space].get(item, {}).get("tier")

        for ti, tier in enumerate(TIERS):
            with cols[ti]:
                btn_label = f"{TIER_EMOJI[tier]} {tier}"
                clicked = st.button(btn_label, key=f"btn_{key}_{tier}",
                                    use_container_width=True,
                                    type="primary" if chosen_tier == tier else "secondary")
                if clicked:
                    mat = DB[space][item][tier]
                    imgs = search_image(mat["search_query"], count=3)
                    st.session_state.selections[space][item] = {
                        "tier": tier, **mat,
                        "image_url": imgs[0]["url"] if imgs else "",
                        "source_url": imgs[0]["page"] if imgs else "",
                    }
                    st.session_state.images[key] = imgs
                    st.rerun()

        # Show selected material info
        sel = st.session_state.selections[space].get(item)
        if sel:
            with cols[3]:
                info_cols = st.columns([1, 2])
                imgs = st.session_state.images.get(key, [])
                with info_cols[0]:
                    if imgs:
                        st.image(imgs[0]["url"], width=140)
                        if imgs[0].get("page"):
                            st.caption(f"[출처 링크]({imgs[0]['page']})")
                with info_cols[1]:
                    st.markdown(f"**{sel['product']}**  \n"
                                f"브랜드: {sel['brand']}  \n"
                                f"사양: {sel['spec']}  \n"
                                f"마감: {sel.get('finish', '-')}  \n"
                                f"💰 {sel['price']}  \n"
                                f"💡 {sel.get('note', '')}")

                # Show additional image options
                if len(imgs) > 1:
                    with st.expander("다른 이미지 보기"):
                        img_cols = st.columns(len(imgs))
                        for ii, img in enumerate(imgs):
                            with img_cols[ii]:
                                st.image(img["url"], width=120)
                                if img.get("page"):
                                    st.caption(f"[출처]({img['page']})")
                                if st.button("이 이미지 선택", key=f"imgsel_{key}_{ii}"):
                                    st.session_state.selections[space][item]["image_url"] = img["url"]
                                    st.session_state.selections[space][item]["source_url"] = img["page"]
                                    st.rerun()

        st.markdown("---")

st.divider()

# ── 4. PPT 생성 ─────────────────────────────────────────────────────────────────
st.subheader("📄 스펙북 PPT 생성")

total_selected = sum(
    len(items) for items in st.session_state.selections.values()
)
st.info(f"현재 {len(st.session_state.selections)}개 공간, {total_selected}개 자재 선택됨")

if st.button("🎨 PPT 스펙북 생성하기", type="primary", use_container_width=True):
    if not st.session_state.selections:
        st.warning("최소 1개 자재를 선택해주세요.")
    else:
        with st.spinner("PPT 생성 중... 이미지를 불러오고 있습니다."):
            space_data = {}
            for space, items in st.session_state.selections.items():
                rows = []
                for item, sel in items.items():
                    rows.append({"item": item, **sel})
                if rows:
                    space_data[space] = rows

            pptx_bytes = generate_pptx(project, space_data)

        filename = f"{proj_name}_스펙북.pptx"
        st.download_button(
            label="⬇️ PPT 다운로드",
            data=pptx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
        st.success("PPT가 생성되었습니다! 위 버튼을 클릭하여 다운로드하세요.")
