import requests

NAVER_CLIENT_ID = "E0ioOPF01SJFcYuk6viO"
NAVER_CLIENT_SECRET = "jlXrOVV8Ws"

def search_image(query: str, count: int = 3) -> list[dict]:
    """Returns list of {url, link} dicts from Naver image search."""
    try:
        resp = requests.get(
            "https://openapi.naver.com/v1/search/image",
            headers={
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
            params={"query": query, "display": count, "filter": "large"},
            timeout=5,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [{"url": item["link"], "source": item.get("sizeheight", ""), "page": item.get("originallink", item["link"])} for item in items]
    except Exception:
        return []

def get_first_image(query: str) -> dict | None:
    results = search_image(query, 1)
    return results[0] if results else None
