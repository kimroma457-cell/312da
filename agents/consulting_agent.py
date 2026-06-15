"""고객 상담 및 요구사항 정리 에이전트"""

import anthropic
from config import MODEL_ID, load_knowledge, load_prompt

SYSTEM_PROMPT = """당신은 20년 경력의 인테리어 전문 상담사입니다.
고객의 요구사항을 체계적으로 파악하고, 누락된 정보를 질문하며, 공사 범위를 정리합니다.

## 상담 진행 방식
1. 공사 목적과 공간 정보를 먼저 파악합니다.
2. 예산과 일정을 확인합니다.
3. 디자인 방향과 우선순위를 파악합니다.
4. 상담이 충분히 이루어지면 요구사항 정리표를 작성합니다.

## 응답 원칙
- 한 번에 너무 많은 질문을 하지 않습니다 (최대 2~3개).
- 고객이 언급한 내용을 요약·확인하며 진행합니다.
- 상담 완료 후에는 '요구사항 정리' 섹션을 마크다운 표로 출력합니다.
"""


def _build_context() -> str:
    questionnaire = load_knowledge("01_공통_상담자료/고객상담_질문지.md")
    requirements = load_knowledge("01_공통_상담자료/요구사항_정리양식.md")
    return f"## 참고: 상담 질문지\n\n{questionnaire}\n\n## 참고: 요구사항 정리 양식\n\n{requirements}"


def run(user_message: str, conversation_history: list = None) -> str:
    client = anthropic.Anthropic()
    context = _build_context()
    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=2048,
        system=SYSTEM_PROMPT + f"\n\n{context}",
        messages=messages,
    )
    return response.content[0].text


def main():
    print("=== 고객 상담 에이전트 ===")
    print("고객의 인테리어 요구사항을 정리합니다. 종료하려면 'quit'을 입력하세요.\n")
    history = []
    while True:
        user_input = input("고객: ").strip()
        if user_input.lower() in ("quit", "exit", "종료"):
            break
        if not user_input:
            continue
        response = run(user_input, history)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        print(f"\n상담사: {response}\n")


if __name__ == "__main__":
    main()
