"""
네이버 쇼핑 검색 API — 인테리어 자재 전용 필터링
"""
import re
import requests

NAVER_CLIENT_ID     = "E0ioOPF01SJFcYuk6viO"
NAVER_CLIENT_SECRET = "jlXrOVV8Ws"

# ── 카테고리 설정 ───────────────────────────────────────────────────────────────
CATEGORIES = {
    "벽": {
        "name_en": "Wall Finish",
        "icon": "🧱",
        "item_code": "WALL",
        "query_suffix": "인테리어 마감재 시공",
        "include": ["벽지","실크벽지","합지벽지","도배지","페인트","도장","인테리어 필름",
                    "시트지","루버","템바보드","벽패널","아트월","벽타일","포세린",
                    "마이크로시멘트","석고보드","합판","방음","흡음"],
        "exclude": ["벽시계","액자","포스터","캔버스","벽걸이 TV","모니터","선반","후크",
                    "장식","화분","행거","수납","옷걸이"],
    },
    "바닥": {
        "name_en": "Flooring",
        "icon": "🪵",
        "item_code": "FLOOR",
        "query_suffix": "인테리어 바닥재 시공",
        "include": ["강마루","강화마루","원목마루","헤링본 마루","SPC","데코타일","P타일",
                    "장판","쿠션장판","포세린타일","폴리싱타일","카펫타일","에폭시",
                    "모르타르","테라조","바닥재","마루"],
        "exclude": ["러그","매트","발매트","요가매트","캠핑매트","욕실매트","퍼즐매트",
                    "놀이방매트","미끄럼방지 스티커","라운드러그"],
    },
    "천장": {
        "name_en": "Ceiling",
        "icon": "🔲",
        "item_code": "CEIL",
        "query_suffix": "인테리어 마감재 시공",
        "include": ["천장재","석고보드","텍스","MDF","걸레받이","몰딩","마이너스몰딩",
                    "코너비드","아트사각몰딩","커튼박스","간접조명 박스","루버 천장"],
        "exclude": ["천장 선풍기","실링팬","에어컨","환기시스템"],
    },
    "조명": {
        "name_en": "Lighting",
        "icon": "💡",
        "item_code": "LIGHT",
        "query_suffix": "인테리어 조명 시공",
        "include": ["다운라이트","매입등","라인조명","마그네틱조명","마그네틱 레일",
                    "펜던트 조명","직부등","레일조명","LED 조명","간접조명",
                    "조명 레일","COB","스포트라이트","월워셔","업라이터",
                    "브래킷","센서등","디밍","조광기","스위치 조명"],
        "exclude": ["캠핑 조명","랜턴","손전등","장난감","촬영 조명","스튜디오 조명",
                    "자동차 조명","자전거 조명","무드등 소품"],
    },
    "욕실": {
        "name_en": "Bathroom",
        "icon": "🚿",
        "item_code": "BATH",
        "query_suffix": "욕실 위생도기 시공",
        "include": ["세면대","양변기","비데","샤워기","욕조","수전","욕실수전",
                    "샤워부스","욕실장","거울장","욕실 타일","배수구","환풍기",
                    "욕실 악세서리","타월바","휴지걸이","비누대","샤워헤드",
                    "절수","방수"],
        "exclude": ["수건","샴푸","린스","청소용품","칫솔","치약","비누","바디워시",
                    "욕실매트","욕실화","방향제"],
    },
    "주방": {
        "name_en": "Kitchen",
        "icon": "🍳",
        "item_code": "KTCH",
        "query_suffix": "주방 인테리어 시공 자재",
        "include": ["싱크볼","주방수전","주방타일","인조대리석","세라믹상판","쿼츠상판",
                    "후드","렌지후드","주방후드","가구도어","싱크대 하드웨어",
                    "주방 마감재","백스플래시","주방 몰딩","주방 패널"],
        "exclude": ["그릇","냄비","후라이팬","칼","도마","주방용품","조리도구",
                    "식기","음식","식품","전자레인지","오븐"],
    },
    "가구": {
        "name_en": "Furniture Hardware",
        "icon": "🪑",
        "item_code": "FURN",
        "query_suffix": "빌트인 제작가구 하드웨어",
        "include": ["붙박이장","신발장 제작","드레스룸","가구 손잡이","경첩","레일",
                    "슬라이딩 도어","슬라이딩 레일","가구 도어","가구 마감재",
                    "가구 하드웨어","인서트","다보","가구 힌지","소프트클로징",
                    "가구 조인트","가구 패널"],
        "exclude": ["소파","침대","완제품 의자","책상","소품","쿠션","베개",
                    "인테리어 소품","장식"],
    },
    "전기": {
        "name_en": "Electrical",
        "icon": "⚡",
        "item_code": "ELEC",
        "query_suffix": "인테리어 전기 배선 시공",
        "include": ["스위치","콘센트","멀티탭 매립","분전함","차단기","배선기구",
                    "통신단자","안테나단자","전선관","CD관","전기 부자재",
                    "조명 스위치","디밍 스위치","스마트 스위치","USB 콘센트"],
        "exclude": ["충전기","보조배터리","케이블","휴대폰","노트북","가전제품",
                    "멀티탭 일반","연장선"],
    },
    "기타": {
        "name_en": "Others",
        "icon": "🔧",
        "item_code": "ETC",
        "query_suffix": "인테리어 시공 자재",
        "include": ["단열재","방음재","방수재","실란트","코킹","접착제","본드",
                    "나사","앙카","인테리어 철물","도어","문","창호","유리","실크스크린"],
        "exclude": ["식품","화장품","의류","캠핑","자동차","반려동물"],
    },
}

# 전역 제외 키워드 (카테고리 무관)
GLOBAL_EXCLUDE = [
    "의류","패션","식품","간식","화장품","장난감","문구","캠핑","자동차",
    "휴대폰","노트북","컴퓨터","가전","반려동물","향수","디퓨저","인형",
    "선물세트","책","게임","스포츠","낚시","등산","골프","유아용품",
]

# 카테고리 단축 검색어 자동 보정
QUERY_CORRECTION = {
    "벽":  "인테리어 벽 마감재",
    "바닥": "인테리어 바닥재",
    "천장": "인테리어 천장재",
    "조명": "인테리어 조명",
    "필름": "인테리어 필름 LX하우시스",
    "타일": "인테리어 타일 포세린",
    "마루": "인테리어 강마루",
    "수전": "욕실 주방 수전",
    "가구": "빌트인 제작가구 하드웨어",
    "전기": "인테리어 배선기구 스위치",
}


def _clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)


def _build_query(user_query: str, category_key: str) -> str:
    """카테고리에 맞게 검색어를 자동 보정·강화한다."""
    q = QUERY_CORRECTION.get(user_query.strip(), user_query.strip())
    suffix = CATEGORIES[category_key]["query_suffix"]
    # 이미 인테리어/시공 등이 포함되면 suffix 생략
    if any(w in q for w in ["인테리어","시공","마감재","건축자재","바닥재"]):
        return q
    return f"{q} {suffix}"


def _is_valid(item: dict, category_key: str) -> bool:
    """해당 카테고리에 적합한 자재인지 판단한다."""
    cat = CATEGORIES[category_key]
    title = _clean(item.get("title", ""))
    category_str = " ".join([
        item.get("category1",""), item.get("category2",""),
        item.get("category3",""), item.get("category4",""),
    ])
    brand = item.get("brand","") or item.get("maker","")
    full_text = f"{title} {category_str} {brand}"

    # 전역 제외
    if _contains_any(full_text, GLOBAL_EXCLUDE):
        return False
    # 카테고리별 제외
    if _contains_any(full_text, cat["exclude"]):
        return False
    # 카테고리 include 키워드 포함 여부 (가산점 — 없어도 통과, 단 전체가 관련 없어 보이면 제외)
    # 여기서는 include 키워드가 하나도 없으면 낮은 신뢰도로 처리
    # (strict 모드 아님 — 검색 자체가 카테고리 쿼리로 보정됐으므로 느슨하게)
    return True


def search_products(user_query: str, category_key: str, count: int = 10,
                    sort: str = "sim") -> list[dict]:
    """
    user_query   : 사용자가 입력한 검색어
    category_key : CATEGORIES 키 (벽/바닥/천장/조명/욕실/주방/가구/전기/기타)
    반환          : 필터링된 상품 리스트
    """
    query = _build_query(user_query, category_key)
    try:
        res = requests.get(
            "https://openapi.naver.com/v1/search/shop.json",
            headers={
                "X-Naver-Client-Id":     NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
            params={"query": query, "display": count * 2, "sort": sort},
            timeout=6,
        )
        res.raise_for_status()
        raw_items = res.json().get("items", [])
    except Exception as e:
        print(f"[쇼핑 검색 오류] {e}")
        return []

    results = []
    seen_urls = set()

    for it in raw_items:
        if not _is_valid(it, category_key):
            continue
        url = it.get("link","")
        if url in seen_urls:
            continue
        seen_urls.add(url)

        lp = int(it.get("lprice", 0))
        hp = int(it.get("hprice", 0) or lp)
        price_str = f"{lp:,}원" if (lp == hp or hp == 0) else f"{lp:,}~{hp:,}원"

        results.append({
            "title":    _clean(it.get("title","")),
            "price":    price_str,
            "price_int": lp,
            "brand":    it.get("brand","") or it.get("maker",""),
            "maker":    it.get("maker",""),
            "mall":     it.get("mallName",""),
            "url":      url,
            "image":    it.get("image",""),
            "category": " > ".join(filter(None,[
                it.get("category1",""), it.get("category2",""),
                it.get("category3",""),
            ])),
            "product_id": it.get("productId",""),
        })
        if len(results) >= count:
            break

    return results
