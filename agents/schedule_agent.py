"""공정표 및 공사일보 작성 에이전트"""

import anthropic
from config import MODEL_ID, load_knowledge

SYSTEM_PROMPT = """당신은 20년 경력의 인테리어 현장 소장입니다.
공사 규모와 범위에 맞는 공정표를 작성하고, 공사일보를 정리합니다.

## 공정 원칙
- 표준 공정 순서: 철거→설비/전기 배관→목공→방수→타일→도장→바닥→가구→조명→청소→검수
- 선후 공정 관계를 반드시 고려합니다.
- 전기 배선은 석고 마감 전 완료, 방수는 타일 전 완료 등 충돌 방지를 명시합니다.
- 공기 산정 시 현실적인 여유 시간을 포함합니다.

## 공사일보 작성
날짜, 날씨, 투입 인원, 작업 내용, 특이사항, 다음 날 계획을 포함합니다.
"""


def run(user_message: str, conversation_history: list = None) -> str:
    client = anthropic.Anthropic()
    schedule_template = load_knowledge("02_인테리어_업자/표준_공정표.md")
    daily_log = load_knowledge("02_인테리어_업자/공사일보_양식.md")
    context = f"## 표준 공정표\n\n{schedule_template}\n\n## 공사일보 양식\n\n{daily_log}"

    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=3000,
        system=SYSTEM_PROMPT + f"\n\n{context}",
        messages=messages,
    )
    return response.content[0].text


def main():
    print("=== 공정표/공사일보 에이전트 ===")
    print("공정표 작성 또는 공사일보를 도와드립니다. 종료하려면 'quit'을 입력하세요.")
    print("예: '30평 전체 리모델링 공정표를 만들어줘. 착공은 7월 1일이야'\n")
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
        print(f"\n현장 소장: {response}\n")


if __name__ == "__main__":
    main()
