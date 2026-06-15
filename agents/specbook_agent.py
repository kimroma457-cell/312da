"""마감재 스펙북 생성 에이전트"""

import anthropic
from config import MODEL_ID, load_all_in_folder

SYSTEM_PROMPT = """당신은 10년 이상 경력의 인테리어 디자이너입니다.
마감재 DB를 활용하여 프로젝트에 적합한 스펙북을 생성합니다.

## 스펙북 작성 원칙
- 스타일, 예산 등급, 고객 선호도에 맞는 자재를 추천합니다.
- 브랜드·품번·규격·색상·단가·납기를 명시합니다.
- 공간별로 구분하여 정리합니다.
- 자재 수량 계산 시 여분 10%를 포함합니다.
- 대안 자재도 함께 제안합니다.

## 출력 형식
마크다운 표로 공간별 스펙북을 작성하고, 전체 발주표를 마지막에 제공합니다.
"""


def run(user_message: str, conversation_history: list = None) -> str:
    client = anthropic.Anthropic()
    materials_db = load_all_in_folder("05_마감재_스펙북")
    context = f"## 마감재 DB\n\n{materials_db}"

    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=4096,
        system=SYSTEM_PROMPT + f"\n\n{context}",
        messages=messages,
    )
    return response.content[0].text


def main():
    print("=== 스펙북/마감재 에이전트 ===")
    print("마감재 스펙북을 생성합니다. 종료하려면 'quit'을 입력하세요.")
    print("예: '30평 아파트, 모던 미니멀 스타일, 중급 예산으로 스펙북 만들어줘'\n")
    history = []
    while True:
        user_input = input("입력: ").strip()
        if user_input.lower() in ("quit", "exit", "종료"):
            break
        if not user_input:
            continue
        response = run(user_input, history)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        print(f"\n디자이너: {response}\n")


if __name__ == "__main__":
    main()
