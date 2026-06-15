"""견적 작성 및 검토 에이전트"""

import anthropic
from config import MODEL_ID, load_knowledge

SYSTEM_PROMPT = """당신은 20년 경력의 인테리어 견적 전문가입니다.
공종별 단가 DB를 바탕으로 견적 초안을 작성하고, 누락 공종을 탐지합니다.

## 견적 작성 원칙
- 철거→설비/전기→목공→방수→타일→도장→바닥→가구→조명→청소 순서로 공종을 검토합니다.
- 자재비와 인건비를 구분하여 기재합니다.
- 부가세(10%) 별도 표기를 기본으로 합니다.
- 총 공사비의 5~10% 예비비를 포함할 것을 권고합니다.

## 누락 공종 체크리스트
철거, 폐기물처리, 양중비, 목공, 전기, 설비, 방수, 타일, 도장/벽지, 바닥재, 가구, 조명, 실리콘, 청소

## 출력 형식
마크다운 표로 견적서를 작성하고, 검토 결과를 별도 섹션으로 제공합니다.
"""


def run(user_message: str, conversation_history: list = None) -> str:
    client = anthropic.Anthropic()
    estimate_db = load_knowledge("02_인테리어_업자/공종별_견적DB.md")
    schedule = load_knowledge("02_인테리어_업자/표준_공정표.md")
    context = f"## 공종별 단가 DB\n\n{estimate_db}\n\n## 표준 공정표\n\n{schedule}"

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
    print("=== 견적 에이전트 ===")
    print("견적 작성 또는 검토를 도와드립니다. 종료하려면 'quit'을 입력하세요.\n")
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
        print(f"\n견적 전문가: {response}\n")


if __name__ == "__main__":
    main()
