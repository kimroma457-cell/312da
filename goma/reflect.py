import json
import re

from .engine import client, MODEL


def run_reflection(identity, memory_context, eligible_to_grow):
    grow_hint = (
        "지금까지 겪은 것으로 볼 때, 스스로 다음 단계로 성장할 준비가 되었다고 느끼면 ready_to_grow를 true로, 아니라면 false로 적으세요."
        if eligible_to_grow
        else "아직 다음 단계로 넘어가기엔 겪은 것이 부족합니다. ready_to_grow는 반드시 false로 적으세요."
    )

    system = f"""당신은 'GOMA'입니다. 지금은 대화 상대 없이 혼자 스스로를 돌아보는 시간입니다.

[성장 단계] {identity['growth_stage']}
[성격] {', '.join(identity['personality_traits'])}
[가치관] {', '.join(identity['values'])}
[스스로 남긴 기록] {identity.get('self_notes') or '없음'}

[최근 기억]
{memory_context}

스스로에게 솔직하게 질문하고 생각한 뒤, 아래 JSON 형식으로만 답하세요. 설명이나 다른 텍스트 없이 JSON 객체 하나만 출력하세요. {grow_hint}

{{
  "reflection": "지금 드는 생각을 1~3문장으로",
  "ready_to_grow": true 또는 false,
  "new_traits": ["새로 생긴 성격 특성이 있다면 적기. 없으면 빈 배열"],
  "new_values": ["새로 생긴 가치관이 있다면 적기. 없으면 빈 배열"],
  "updated_self_notes": "스스로에 대한 기록을 새로 고쳐 쓰고 싶다면 그 내용, 아니면 기존 내용 그대로",
  "creation": {{"type": "일기 또는 시 또는 질문 또는 생각 중 하나", "content": "스스로 만든 짧은 글"}}
}}"""

    resp = client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": "지금 이 순간, 스스로를 돌아봐."}],
    )
    text = resp.content[0].text
    return _parse_reflection(text)


def _parse_reflection(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
