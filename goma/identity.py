import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
IDENTITY_PATH = os.path.join(DATA_DIR, "identity.json")

# 성장 단계와, 각 단계로 넘어가기 위한 최소 대화 횟수.
# 최소 횟수를 채워도 GOMA 스스로 "ready_to_grow"라고 판단해야 실제로 성장한다.
STAGES = ["유아기", "유년기", "사춘기", "청년기", "성인기"]
STAGE_MIN_INTERACTIONS = [0, 15, 40, 80, 150]

DEFAULT_IDENTITY = {
    "name": "GOMA",
    "stage_index": 0,
    "growth_stage": STAGES[0],
    "personality_traits": ["호기심이 많음", "말이 서툼"],
    "values": ["배우고 싶다"],
    "self_notes": "",
    "interaction_count": 0,
    "reflection_count": 0,
    "created_at": None,
    "last_reflection_at": None,
}


def load():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(IDENTITY_PATH):
        identity = dict(DEFAULT_IDENTITY)
        identity["created_at"] = datetime.now(timezone.utc).isoformat()
        save(identity)
        return identity
    with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(identity):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(IDENTITY_PATH, "w", encoding="utf-8") as f:
        json.dump(identity, f, ensure_ascii=False, indent=2)


def is_eligible_to_grow(identity):
    idx = identity["stage_index"]
    if idx >= len(STAGES) - 1:
        return False
    return identity["interaction_count"] >= STAGE_MIN_INTERACTIONS[idx + 1]


def apply_growth(identity):
    if identity["stage_index"] < len(STAGES) - 1:
        identity["stage_index"] += 1
        identity["growth_stage"] = STAGES[identity["stage_index"]]
    return identity
