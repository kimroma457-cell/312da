"""
검색어 기반 AI 자재 추천 (최저가/보통/최고가)
Anthropic Claude를 사용하여 검색어 분석 후 3단계 자재를 추천한다.
"""
import os
import json
import anthropic
from pathlib import Path

def _load_dotenv():
    """specbook_app/.env 파일이 있으면 환경변수로 로드."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv()

SYSTEM = """당신은 한국 인테리어 전문가입니다.
사용자가 인테리어 자재/가구/조명 등의 검색어를 입력하면,
해당 품목의 최저가/보통/최고가 3가지 옵션을 JSON으로 반환하세요.

반드시 아래 JSON 형식만 출력하세요 (설명 없이):
{
  "item_label": "품목명 (예: 거실 소파)",
  "item_code": "SOFA",
  "최저가": {
    "product": "제품명",
    "brand": "브랜드",
    "spec": "규격 (mm 또는 수량)",
    "finish": "재질 / 마감",
    "price": "가격대 (예: 50~90만원)",
    "vendor": "구매처 유형 (기성품/커스텀/수입/빌트인)",
    "note": "한줄 특이사항",
    "search_query": "네이버 이미지 검색에 쓸 한국어 검색어"
  },
  "보통": { ... },
  "최고가": { ... }
}"""


def recommend(query: str) -> dict:
    """
    query: 사용자 검색어 (예: '거실 소파', '주방 수전', '펜던트 조명')
    반환:  {item_label, item_code, 최저가:{...}, 보통:{...}, 최고가:{...}}
    """
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM,
            messages=[{"role": "user", "content": f"검색어: {query}"}],
        )
        raw = msg.content[0].text.strip()
        # JSON 블록 추출
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e)}
