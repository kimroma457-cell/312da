"""
네이버 쇼핑 검색 API — 전문 인테리어 시공업자 전용
반드시 브랜드 + 제품군 + 키워드 조합으로만 검색한다.
"""
import re
import requests
from brands import BRAND_CATALOG, CATEGORY_META

NAVER_CLIENT_ID     = "E0ioOPF01SJFcYuk6viO"
NAVER_CLIENT_SECRET = "jlXrOVV8Ws"

# ── PPT 생성기 호환용 CATEGORIES 래퍼 ─────────────────────────────────────────
# pptx_generator.py 및 레거시 코드에서 CATEGORIES[key] 사용 지원
CATEGORIES: dict[str, dict] = {
    cat: {
        "name_en":   meta["name_en"],
        "icon":      meta["icon"],
        "item_code": meta["item_code"],
    }
    for cat, meta in CATEGORY_META.items()
}

# ── 금지 키워드 (제목에 하나라도 있으면 제거) ──────────────────────────────────
FORBIDDEN: list[str] = [
    "셀프", "DIY", "diy", "초보자용", "초보용", "입문용",
    "혼자", "직접시공", "직접 시공", "직접설치", "간편시공", "간단시공",
    "접착식", "접착형", "부착식", "부착형", "붙이는", "붙임식",
    "떼어내는", "탈부착", "스티커", "타일스티커", "폼스티커", "벽스티커",
    "폼블럭", "쿠션벽지", "단열벽지", "시공패키지", "패키지",
    "샘플", "테스터", "소량", "낱장", "낱개", "1장", "1롤", "1개입",
    "체험", "인테리어소품", "장식용", "장식품", "소품",
    "벽꾸미기", "집꾸미기", "방꾸미기", "데코", "리폼", "리폼지",
    "핸드메이드", "취미", "미니어처",
    "원룸", "자취방", "아이방 꾸미기", "아이방꾸미기",
    "가정용 보수", "보수용",
]

# ── 네이버 카테고리 제외 ───────────────────────────────────────────────────────
FORBIDDEN_NAVER_CATS: list[str] = [
    "생활/건강", "DIY", "소품", "데코", "스티커",
    "문구/오피스", "완구/취미", "가정용품", "패션의류", "식품",
]


def _clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _has_forbidden(title: str) -> bool:
    t = title.lower()
    return any(k.lower() in t for k in FORBIDDEN)


def _has_forbidden_cat(item: dict) -> bool:
    cats = " ".join([
        item.get("category1", ""), item.get("category2", ""),
        item.get("category3", ""), item.get("category4", ""),
    ])
    return any(k.lower() in cats.lower() for k in FORBIDDEN_NAVER_CATS)


def _fetch(query: str, display: int = 100, sort: str = "sim") -> list[dict]:
    """네이버 쇼핑 API 호출."""
    try:
        res = requests.get(
            "https://openapi.naver.com/v1/search/shop.json",
            headers={
                "X-Naver-Client-Id":     NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
            params={"query": query, "display": min(display, 100), "sort": sort},
            timeout=7,
        )
        res.raise_for_status()
        return res.json().get("items", [])
    except Exception as e:
        print(f"[API 오류] {e}")
        return []


def _to_result(it: dict) -> dict:
    lp = int(it.get("lprice", 0))
    hp = int(it.get("hprice", 0) or lp)
    price = f"{lp:,}원" if (lp == hp or hp == 0) else f"{lp:,}~{hp:,}원"
    brand = it.get("brand", "") or it.get("maker", "")
    return {
        "title":      _clean(it.get("title", "")),
        "price":      price,
        "price_int":  lp,
        "brand":      brand,
        "maker":      it.get("maker", ""),
        "mall":       it.get("mallName", ""),
        "url":        it.get("link", ""),
        "image":      it.get("image", ""),
        "category":   " > ".join(filter(None, [
            it.get("category1", ""), it.get("category2", ""),
            it.get("category3", ""),
        ])),
        "product_id": it.get("productId", ""),
    }


def search_products(
    brand: str,
    category: str,
    product_group: str = "",
    keyword: str = "",
    count: int = 50,
) -> list[dict]:
    """
    브랜드 + 제품군 + 키워드 조합으로만 검색한다.
    단독 키워드 검색 불가.

    brand         : 선택한 업체명 (예: "신한벽지")
    category      : 선택한 카테고리 (예: "벽")
    product_group : 선택한 제품군 (예: "실크벽지")
    keyword       : 사용자 추가 검색어 (예: "베이지")
    """
    parts = [brand, product_group, keyword]
    query = " ".join(p.strip() for p in parts if p.strip())
    if not query:
        return []

    seen: set = set()
    results: list[dict] = []

    for it in _fetch(query, display=count * 2):
        title = _clean(it.get("title", ""))
        url   = it.get("link", "")
        if not url or url in seen:
            continue
        if _has_forbidden(title):
            continue
        if _has_forbidden_cat(it):
            continue
        seen.add(url)
        results.append(_to_result(it))
        if len(results) >= count:
            break

    return results
