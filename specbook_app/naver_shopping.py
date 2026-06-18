"""
네이버 쇼핑 검색 API — 전문 인테리어 시공업자 전용 자재 필터
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
        "query_suffix": "시공용 벽지 마감재",
        "pro_queries": [
            "실크벽지 시공",
            "합지벽지 도배",
            "인테리어필름 시공",
            "LX지인 벽지",
        ],
    },
    "바닥": {
        "name_en": "Flooring",
        "icon": "🪵",
        "item_code": "FLOOR",
        "query_suffix": "시공용 바닥재",
        "pro_queries": [
            "강마루 시공",
            "강화마루 바닥재",
            "원목마루 시공",
            "LX지인 마루",
            "데코타일 상업용",
        ],
    },
    "천장": {
        "name_en": "Ceiling",
        "icon": "🔲",
        "item_code": "CEIL",
        "query_suffix": "시공용 천장재 몰딩",
        "pro_queries": [
            "석고보드 천장",
            "인테리어 몰딩 시공",
            "마이너스몰딩 걸레받이",
        ],
    },
    "조명": {
        "name_en": "Lighting",
        "icon": "💡",
        "item_code": "LIGHT",
        "query_suffix": "시공용 인테리어 조명",
        "pro_queries": [
            "매입등 다운라이트 시공",
            "마그네틱레일 조명",
            "LED 라인조명 시공",
        ],
    },
    "욕실": {
        "name_en": "Bathroom",
        "icon": "🚿",
        "item_code": "BATH",
        "query_suffix": "위생도기 시공",
        "pro_queries": [
            "세면대 욕실 시공",
            "양변기 비데 시공",
            "욕실수전 샤워기",
        ],
    },
    "주방": {
        "name_en": "Kitchen",
        "icon": "🍳",
        "item_code": "KTCH",
        "query_suffix": "주방 시공 자재",
        "pro_queries": [
            "쿼츠상판 시공",
            "렌지후드 주방",
            "주방타일 백스플래시",
        ],
    },
    "가구": {
        "name_en": "Furniture Hardware",
        "icon": "🪑",
        "item_code": "FURN",
        "query_suffix": "제작가구 하드웨어",
        "pro_queries": [
            "붙박이장 도어 힌지",
            "슬라이딩레일 가구",
            "소프트클로징 경첩",
        ],
    },
    "전기": {
        "name_en": "Electrical",
        "icon": "⚡",
        "item_code": "ELEC",
        "query_suffix": "인테리어 전기 배선기구",
        "pro_queries": [
            "배선기구 스위치 콘센트",
            "분전함 차단기 시공",
            "디밍스위치 스마트스위치",
        ],
    },
    "기타": {
        "name_en": "Others",
        "icon": "🔧",
        "item_code": "ETC",
        "query_suffix": "인테리어 시공 자재",
        "pro_queries": [
            "단열재 방수재 시공",
            "실란트 코킹 자재",
            "창호 도어 시공",
        ],
    },
}

# ── 검색어 자동 보정 (짧은 입력 → 전문 시공 쿼리) ─────────────────────────────
QUERY_CORRECTION = {
    # 벽
    "실크":    "실크벽지 시공용",
    "합지":    "합지벽지 도배",
    "도배지":  "실크벽지 합지벽지 도배",
    "벽지":    "실크벽지 합지벽지 시공",
    "필름":    "인테리어필름 시공용 LX하우시스",
    "시트지":  "인테리어필름 시공",
    # 바닥
    "마루":    "강마루 원목마루 강화마루 시공",
    "강마루":  "강마루 바닥재 시공",
    "장판":    "PVC장판 바닥재 시공용",
    "데코타일":"데코타일 상업용 PVC바닥재",
    "타일":    "포세린타일 도기타일 시공",
    # 천장·몰딩
    "몰딩":    "인테리어몰딩 마이너스몰딩 시공",
    "걸레받이":"걸레받이 MDF 시공",
    "석고":    "석고보드 건식 시공",
    # 조명
    "다운":    "다운라이트 매입등 시공",
    "매입":    "매입등 다운라이트 시공",
    "레일":    "마그네틱레일 조명 시공",
    # 욕실
    "세면대":  "세면대 위생도기 시공",
    "양변기":  "양변기 위생도기 시공",
    "수전":    "욕실수전 주방수전 시공",
    # 일반
    "단열":    "단열재 압출법단열재 시공",
    "방수":    "방수재 우레탄방수 시공",
}

# ── 전면 제외 키워드 (제목에 하나라도 있으면 즉시 제거) ──────────────────────
TITLE_EXCLUDE = [
    # DIY / 셀프 시공
    "셀프", "diy", "DIY", "초보자", "초보용", "입문용",
    "혼자", "직접시공", "직접 시공", "직접설치",
    "간편시공", "간단시공", "쉬운시공", "따라하기",
    # 소비자용 부착 제품
    "접착식", "접착형", "부착식", "부착형",
    "붙이는", "붙임식", "떼어내는", "탈부착",
    "스티커", "타일스티커", "폼스티커", "벽스티커",
    "폼블럭", "쿠션벽지", "단열벽지",
    # 소매·소량·샘플
    "샘플", "테스터", "소량", "낱장", "낱개",
    "1장", "1롤", "1개입", "체험키트",
    "시공패키지", "셀프패키지",
    # 꾸미기·소품·장식
    "인테리어소품", "장식용", "장식품", "소품",
    "벽꾸미기", "집꾸미기", "방꾸미기", "데코",
    "리폼", "리폼지", "시트지",
    "핸드메이드", "취미", "미니어처",
    # 특정 생활 용어
    "원룸", "자취방", "아이방꾸미기", "아이방 꾸미기",
    "가정용 보수", "보수용",
]

# ── 네이버 카테고리 제외 (category1~4) ────────────────────────────────────────
NAVER_CATEGORY_EXCLUDE = [
    "생활/건강", "DIY", "소품", "데코", "스티커",
    "문구/오피스", "완구/취미", "가정용품",
]

# ── 신뢰 브랜드 (있으면 가산점 — 나중에 정렬에 활용) ──────────────────────────
TRUSTED_BRANDS = {
    "LX하우시스", "LX지인", "지인", "현대L&C", "KCC", "KCC글라스",
    "한화L&C", "녹수", "동화자연마루", "구정마루", "동양강철",
    "대림바스", "아메리칸스탠다드", "로얄", "이누스", "대우루컴즈",
    "삼성SDI", "LS전선", "경동나비엔",
}


def _clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _contains_any(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords)


def _build_query(user_query: str, category_key: str) -> str:
    """사용자 입력을 전문 시공 검색어로 보정한다."""
    q = user_query.strip()
    # 단일 단어 보정
    corrected = QUERY_CORRECTION.get(q, "")
    if corrected:
        return corrected
    # 이미 전문 키워드 포함
    pro_words = ["시공", "마감재", "건축자재", "바닥재", "업체", "인테리어필름",
                 "위생도기", "배선기구", "하드웨어"]
    if any(w in q for w in pro_words):
        return q
    # 카테고리 suffix 붙이기
    return f"{q} {CATEGORIES[category_key]['query_suffix']}"


def _is_valid_title(title: str) -> bool:
    """제목에 제외 키워드가 없으면 True."""
    return not _contains_any(title, TITLE_EXCLUDE)


def _is_valid_category(item: dict) -> bool:
    """네이버 카테고리가 소비자 카테고리면 False."""
    cats = " ".join([
        item.get("category1", ""), item.get("category2", ""),
        item.get("category3", ""), item.get("category4", ""),
    ])
    return not _contains_any(cats, NAVER_CATEGORY_EXCLUDE)


def _score(item: dict) -> int:
    """신뢰 브랜드·전문 키워드 포함 여부로 가중치 계산."""
    brand = item.get("brand", "") or item.get("maker", "")
    title = item.get("title", "")
    score = 0
    if brand in TRUSTED_BRANDS or any(b in title for b in TRUSTED_BRANDS):
        score += 10
    pro_kw = ["시공", "규격", "m²", "㎡", "박스", "본", "롤단위",
               "도매", "업체", "견적", "시공용"]
    if any(k in title for k in pro_kw):
        score += 5
    return score


def _fetch_naver(query: str, count: int, sort: str) -> list[dict]:
    """네이버 쇼핑 API 단일 호출."""
    try:
        res = requests.get(
            "https://openapi.naver.com/v1/search/shop.json",
            headers={
                "X-Naver-Client-Id":     NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
            params={"query": query, "display": min(count, 100), "sort": sort},
            timeout=7,
        )
        res.raise_for_status()
        return res.json().get("items", [])
    except Exception as e:
        print(f"[쇼핑 API 오류] {e}")
        return []


def _to_result(it: dict) -> dict:
    lp = int(it.get("lprice", 0))
    hp = int(it.get("hprice", 0) or lp)
    price_str = f"{lp:,}원" if (lp == hp or hp == 0) else f"{lp:,}~{hp:,}원"
    return {
        "title":      _clean(it.get("title", "")),
        "price":      price_str,
        "price_int":  lp,
        "brand":      it.get("brand", "") or it.get("maker", ""),
        "maker":      it.get("maker", ""),
        "mall":       it.get("mallName", ""),
        "url":        it.get("link", ""),
        "image":      it.get("image", ""),
        "category":   " > ".join(filter(None, [
            it.get("category1", ""), it.get("category2", ""),
            it.get("category3", ""),
        ])),
        "product_id": it.get("productId", ""),
        "_score":     _score(it),
    }


def search_products(
    user_query: str,
    category_key: str,
    count: int = 50,
    sort: str = "sim",
) -> list[dict]:
    """
    전문 시공 자재만 반환한다.
    - 제목 제외 키워드 필터 → 네이버 카테고리 필터 → 신뢰 브랜드 가중 정렬
    - 결과가 없으면 빈 리스트 반환 (앱에서 "결과 부족" 안내)
    """
    seen_urls: set = set()
    raw_pool: list = []

    def _collect(query: str, need: int):
        raw = _fetch_naver(query, need, sort)
        for it in raw:
            title = _clean(it.get("title", ""))
            url   = it.get("link", "")
            if not url or url in seen_urls:
                continue
            if not _is_valid_title(title):
                continue
            if not _is_valid_category(it):
                continue
            seen_urls.add(url)
            raw_pool.append(it)

    # 1차: LX지인 우선 (벽·바닥·천장)
    lxzin_map = {
        "벽":  "LX지인 실크벽지 합지벽지 시공",
        "바닥": "LX지인 강마루 강화마루 시공",
        "천장": "LX지인 천장재 몰딩 시공",
    }
    if category_key in lxzin_map:
        _collect(lxzin_map[category_key], count)

    # 2차: 카테고리 pro_queries (미리 정의된 전문 쿼리들)
    for pq in CATEGORIES[category_key]["pro_queries"]:
        if len(raw_pool) >= count * 2:
            break
        _collect(f"{user_query} {pq}", count)

    # 3차: 사용자 입력 보정 쿼리
    if len(raw_pool) < count:
        _collect(_build_query(user_query, category_key), count * 2)

    # 신뢰 브랜드 우선 정렬
    raw_pool.sort(key=lambda x: _score(x), reverse=True)

    results = [_to_result(it) for it in raw_pool[:count]]
    return results
