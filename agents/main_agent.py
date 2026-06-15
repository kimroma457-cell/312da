"""메인 오케스트레이터 에이전트 - 사용자 의도를 파악하여 적절한 하위 에이전트로 라우팅"""

import anthropic
from config import MODEL_ID, AGENT_DESCRIPTIONS
import consulting_agent
import estimate_agent
import specbook_agent
import schedule_agent
import contract_agent
import inspection_agent
import architect_agent

ROUTER_SYSTEM_PROMPT = """당신은 인테리어·건축 전문 에이전트 시스템의 라우터입니다.
사용자의 메시지를 분석하여 가장 적합한 에이전트를 선택합니다.

사용 가능한 에이전트:
- consulting: 고객 상담 및 요구사항 정리
- estimate: 견적서 작성 및 검토
- specbook: 마감재 스펙북 생성
- schedule: 공정표 및 공사일보 작성
- contract: 계약서 검토 및 추가공사 확인서
- inspection: 준공 검수 및 하자관리
- architect: 건축 설계 지원 (법규, 도면, 인허가)

사용자의 메시지에서 의도를 파악하고, 아래 형식으로만 응답하세요:
AGENT: [에이전트 이름]
REASON: [선택 이유 한 줄]

여러 에이전트가 필요하면 가장 핵심적인 하나를 선택하세요.
"""

AGENTS = {
    "consulting": consulting_agent,
    "estimate": estimate_agent,
    "specbook": specbook_agent,
    "schedule": schedule_agent,
    "contract": contract_agent,
    "inspection": inspection_agent,
    "architect": architect_agent,
}

AGENT_NAMES = {
    "consulting": "상담 에이전트",
    "estimate": "견적 에이전트",
    "specbook": "스펙북 에이전트",
    "schedule": "공정표 에이전트",
    "contract": "계약 에이전트",
    "inspection": "검수/하자 에이전트",
    "architect": "건축 설계 에이전트",
}


def route(user_message: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=200,
        system=ROUTER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    text = response.content[0].text.strip()
    for line in text.split("\n"):
        if line.startswith("AGENT:"):
            agent_name = line.split(":", 1)[1].strip().lower()
            if agent_name in AGENTS:
                return agent_name
    return "consulting"


def main():
    print("=" * 60)
    print("인테리어 / 건축 전문 에이전트 시스템")
    print("=" * 60)
    print("\n사용 가능한 기능:")
    for key, desc in AGENT_DESCRIPTIONS.items():
        print(f"  • {AGENT_NAMES[key]}: {desc}")
    print("\n종료하려면 'quit'을 입력하세요.")
    print("에이전트를 직접 지정하려면 '@에이전트이름 메시지' 형식을 사용하세요.")
    print(f"  예: @estimate 30평 아파트 전체 리모델링 견적 만들어줘\n")

    agent_histories: dict[str, list] = {k: [] for k in AGENTS}
    current_agent = None

    while True:
        user_input = input("나: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "종료"):
            print("에이전트를 종료합니다.")
            break

        # 직접 에이전트 지정
        if user_input.startswith("@"):
            parts = user_input[1:].split(" ", 1)
            if len(parts) >= 1 and parts[0] in AGENTS:
                current_agent = parts[0]
                user_input = parts[1] if len(parts) > 1 else ""
                if not user_input:
                    print(f"[{AGENT_NAMES[current_agent]}로 전환됨]")
                    continue
            else:
                print(f"알 수 없는 에이전트입니다. 사용 가능: {', '.join(AGENTS.keys())}")
                continue
        else:
            # 자동 라우팅
            selected = route(user_input)
            if selected != current_agent:
                current_agent = selected
                print(f"\n[→ {AGENT_NAMES[current_agent]}]\n")

        agent_module = AGENTS[current_agent]
        history = agent_histories[current_agent]
        response = agent_module.run(user_input, list(history))
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        print(f"\n{AGENT_NAMES[current_agent]}: {response}\n")


if __name__ == "__main__":
    main()
