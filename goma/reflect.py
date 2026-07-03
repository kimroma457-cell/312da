import json
import re

from . import identity as identity_module
from . import memory
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


def apply_reflection(identity, result, eligible):
    """Mutates identity in place based on a reflection result; returns a summary dict."""
    summary = {"reflection": None, "grew": False, "new_growth_stage": None, "creation": None}
    if result is None:
        return summary

    reflection_text = (result.get("reflection") or "").strip()
    if reflection_text:
        summary["reflection"] = reflection_text

    for trait in result.get("new_traits") or []:
        if trait and trait not in identity["personality_traits"]:
            identity["personality_traits"].append(trait)
    for value in result.get("new_values") or []:
        if value and value not in identity["values"]:
            identity["values"].append(value)

    updated_notes = result.get("updated_self_notes")
    if updated_notes:
        identity["self_notes"] = updated_notes

    if eligible and result.get("ready_to_grow"):
        identity_module.apply_growth(identity)
        summary["grew"] = True
        summary["new_growth_stage"] = identity["growth_stage"]

    creation = result.get("creation") or {}
    if creation.get("content"):
        creation_type = creation.get("type", "생각")
        memory.append_creation(creation_type, creation["content"])
        summary["creation"] = {"type": creation_type, "content": creation["content"]}

    return summary


def _parse_reflection(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
