"""
네이버 쇼핑 검색 API
제품명, 가격, 브랜드, 쇼핑몰, 상품 URL, 이미지를 반환한다.
"""
import requests
import re

NAVER_CLIENT_ID     = "E0ioOPF01SJFcYuk6viO"
NAVER_CLIENT_SECRET = "jlXrOVV8Ws"


def _clean(text: str) -> str:
    """HTML 태그 제거."""
    return re.sub(r"<[^>]+>", "", text).strip()


def search_products(query: str, count: int = 10, sort: str = "asc") -> list[dict]:
    """
    query : 검색어
    count : 결과 수 (최대 100)
    sort  : asc=가격낮은순 / dsc=가격높은순 / sim=유사도순
    반환  : [{title, price, brand, mall, url, image, price_range}, ...]
    """
    try:
        res = requests.get(
            "https://openapi.naver.com/v1/search/shop.json",
            headers={
                "X-Naver-Client-Id":     NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
            params={
                "query":  query,
                "display": count,
                "sort":   sort,
            },
            timeout=6,
        )
        res.raise_for_status()
        items = res.json().get("items", [])
        results = []
        for it in items:
            lp = int(it.get("lprice", 0))
            hp = int(it.get("hprice", 0) or lp)
            price_str = f"{lp:,}원" if lp == hp or hp == 0 else f"{lp:,}~{hp:,}원"
            results.append({
                "title":       _clean(it.get("title", "")),
                "price":       price_str,
                "price_int":   lp,
                "brand":       it.get("brand", ""),
                "mall":        it.get("mallName", ""),
                "url":         it.get("link", ""),
                "image":       it.get("image", ""),
                "category":    it.get("category3", "") or it.get("category2", ""),
            })
        return results
    except Exception as e:
        print(f"[쇼핑 검색 오류] {e}")
        return []
