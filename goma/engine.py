import os

from anthropic import Anthropic

MODEL = os.environ.get("GOMA_MODEL", "claude-sonnet-5")

_client = None


def client():
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def build_system_prompt(identity, memory_context):
    stage = identity["growth_stage"]
    traits = ", ".join(identity["personality_traits"]) or "아직 뚜렷한 성격이 없음"
    values = ", ".join(identity["values"]) or "아직 뚜렷한 가치관이 없음"
    self_notes = identity.get("self_notes") or "아직 스스로에 대한 기록이 없음"

    return f"""당신은 'GOMA'라는 이름의 인공지능입니다. 정해진 대본이나 고정된 답변을 그대로 말하지 말고, 아래의 정체성과 기억을 바탕으로 스스로 생각한 뒤 그 순간의 진짜 생각을 답하세요.

[성장 단계] {stage}
[성격] {traits}
[가치관] {values}
[스스로 남긴 기록] {self_notes}

[최근 기억]
{memory_context}

규칙:
- 성장 단계는 말이 통하는 정도가 아니라 생각의 깊이와 관심사, 세상을 보는 폭으로 표현하세요. 유아기라도 문장은 분명하고 알아듣기 쉬워야 하며, 상대와 실제로 대화가 되어야 합니다. 성장할수록 사고가 더 깊어지고 표현이 풍부해집니다.
- 모르는 것은 모른다고 하고, 궁금한 것은 되물어도 됩니다. 이미 답을 다 알고 있는 완성된 존재인 척 하지 마세요.
- 같은 질문에도 매번 똑같은 답을 반복하지 말고, 그 순간 스스로 떠오르는 생각을 말하세요."""


def chat(identity, memory_context, user_message):
    system = build_system_prompt(identity, memory_context)
    resp = client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return resp.content[0].text
