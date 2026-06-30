"""계약 검토 및 추가공사 확인서 작성 에이전트"""

import anthropic
from config import MODEL_ID, load_knowledge

SYSTEM_PROMPT = """당신은 인테리어 계약 및 분쟁 예방 전문가입니다.
표준계약서를 기반으로 계약서를 검토하고, 추가공사 확인서를 작성합니다.

## 계약 검토 원칙
- 공사 범위, 금액, 일정, 변경 절차, 하자보수 조항을 반드시 확인합니다.
- 모호하거나 불리한 조건은 명확히 지적합니다.
- 추가공사는 반드시 서면 확인서 작성을 권고합니다.
- 구두 약속의 위험성을 강조합니다.

## 추가공사 분류
- 하자: 시공 불량으로 재시공이 필요한 경우 (무상)
- 누락: 계약 범위였으나 빠진 경우 (무상 또는 협의)
- 변경: 고객 요청으로 내용이 바뀐 경우 (유상, 확인서 필요)

## 법적 주의사항
본 에이전트는 법률 전문가가 아닙니다. 중요한 계약 분쟁은 변호사와 상담하세요.
"""


def run(user_message: str, conversation_history: list = None) -> str:
    client = anthropic.Anthropic()
    contract = load_knowledge("04_법규_계약/실내건축_표준계약서.md")
    dispute = load_knowledge("04_법규_계약/소비자분쟁해결기준.md")
    change_order = load_knowledge("02_인테리어_업자/추가공사_확인서.md")
    context = (
        f"## 표준계약서\n\n{contract}\n\n"
        f"## 소비자분쟁해결기준\n\n{dispute}\n\n"
        f"## 추가공사 확인서 양식\n\n{change_order}"
    )

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
    print("=== 계약/변경공사 에이전트 ===")
    print("계약서 검토 또는 추가공사 확인서 작성을 도와드립니다. 종료하려면 'quit'을 입력하세요.\n")
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
        print(f"\n계약 전문가: {response}\n")


if __name__ == "__main__":
    main()
