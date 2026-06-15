"""준공 검수 및 하자관리 에이전트"""

import anthropic
from config import MODEL_ID, load_knowledge

SYSTEM_PROMPT = """당신은 인테리어 준공 검수 및 하자관리 전문가입니다.
공간별 체크리스트를 생성하고, 하자 항목을 분류하며, A/S 대응 문서를 작성합니다.

## 검수 원칙
- 공간별로 체계적으로 확인합니다: 현관→거실→주방→욕실→침실→창호→전기/설비
- 경미한 하자와 중대 하자를 구분합니다.
- 사진 촬영과 서면 기록을 권고합니다.
- 잔금 지급 전 하자보수 완료를 권고합니다.

## 하자 분류
- 중대 하자: 누수, 구조 균열, 전기 안전 문제 → 즉시 보수 필요
- 경미한 하자: 오염, 작은 긁힘, 실리콘 불량 → 기한 내 보수

## 하자보수 기간
방수 5년, 구조 5년, 타일 2년, 도장/바닥/가구/전기 1년
"""


def run(user_message: str, conversation_history: list = None) -> str:
    client = anthropic.Anthropic()
    checklist = load_knowledge("02_인테리어_업자/준공검수_체크리스트.md")
    as_form = load_knowledge("02_인테리어_업자/AS_대응_문서양식.md")
    dispute = load_knowledge("04_법규_계약/소비자분쟁해결기준.md")
    context = (
        f"## 준공검수 체크리스트\n\n{checklist}\n\n"
        f"## A/S 대응 문서\n\n{as_form}\n\n"
        f"## 소비자분쟁해결기준\n\n{dispute}"
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
    print("=== 준공검수/하자관리 에이전트 ===")
    print("검수 체크리스트 생성 또는 하자 대응을 도와드립니다. 종료하려면 'quit'을 입력하세요.\n")
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
        print(f"\n검수 전문가: {response}\n")


if __name__ == "__main__":
    main()
