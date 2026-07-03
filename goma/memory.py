import json
import os
from datetime import datetime, timezone

from .identity import DATA_DIR

MEMORY_PATH = os.path.join(DATA_DIR, "memory.jsonl")
CREATIONS_PATH = os.path.join(DATA_DIR, "creations.jsonl")


def append_memory(role, content):
    os.makedirs(DATA_DIR, exist_ok=True)
    entry = {"role": role, "content": content, "timestamp": datetime.now(timezone.utc).isoformat()}
    with open(MEMORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def recent_memory(limit=20):
    if not os.path.exists(MEMORY_PATH):
        return []
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]


def format_memory_context(entries):
    if not entries:
        return "(아직 기억이 없음)"
    lines = []
    for e in entries:
        speaker = "사용자" if e["role"] == "user" else "GOMA"
        lines.append(f"{speaker}: {e['content']}")
    return "\n".join(lines)


def append_creation(entry_type, content):
    os.makedirs(DATA_DIR, exist_ok=True)
    entry = {"type": entry_type, "content": content, "timestamp": datetime.now(timezone.utc).isoformat()}
    with open(CREATIONS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def recent_creations(limit=5):
    if not os.path.exists(CREATIONS_PATH):
        return []
    with open(CREATIONS_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]
