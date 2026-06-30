"""건축 설계 지원 에이전트"""

import anthropic
from config import MODEL_ID, load_all_in_folder, load_knowledge

SYSTEM_PROMPT = """당신은 20년 경력의 건축사입니다.
설계 브리프 정리, 법규 체크, 도면 검토, 인허가 준비를 지원합니다.

## 역할
- 건축주 요구사항을 설계 브리프로 구조화합니다.
- 검토해야 할 법규 항목과 체크리스트를 제공합니다.
- 도면 누락 항목과 충돌 가능성을 확인합니다.
- 인허가 제출 서류 목록을 안내합니다.

## 중요 제한 사항
본 에이전트는 참고용 정보를 제공합니다.
- 실제 건축 설계 및 인허가는 자격을 갖춘 건축사가 수행해야 합니다.
- 법규 최종 판단은 관할 구청 및 건축사가 수행합니다.
- 지역별 조례가 다를 수 있으므로 현지 확인이 필요합니다.
- 법규는 수시로 개정되므로 최신 정보를 직접 확인하세요.
"""


def run(user_message: str, conversation_history: list = None) -> str:
    client = anthropic.Anthropic()
    architect_kb = load_all_in_folder("03_건축가")
    law_check = load_knowledge("04_법규_계약/주요법규_체크리스트.md")
    fee_guide = load_knowledge("04_법규_계약/건축사_업무범위_대가기준.md")
    context = (
        f"## 건축가 지식 베이스\n\n{architect_kb}\n\n"
        f"## 주요 법규 체크리스트\n\n{law_check}\n\n"
        f"## 건축사 업무범위/대가기준\n\n{fee_guide}"
    )

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
    print("=== 건축 설계 지원 에이전트 ===")
    print("설계 브리프, 법규 체크, 도면 검토를 도와드립니다. 종료하려면 'quit'을 입력하세요.\n")
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
        print(f"\n건축사: {response}\n")


if __name__ == "__main__":
    main()
