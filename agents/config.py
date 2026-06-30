import os
from pathlib import Path

MODEL_ID = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "interior_architect_agent_knowledge"


def load_prompt(filename: str) -> str:
    path = KNOWLEDGE_BASE_DIR / "06_프롬프트" / filename
    return path.read_text(encoding="utf-8")


def load_knowledge(relative_path: str) -> str:
    path = KNOWLEDGE_BASE_DIR / relative_path
    return path.read_text(encoding="utf-8")


def load_all_in_folder(folder: str) -> str:
    folder_path = KNOWLEDGE_BASE_DIR / folder
    parts = []
    for f in sorted(folder_path.glob("*.md")):
        parts.append(f"## {f.name}\n\n{f.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(parts)


AGENT_DESCRIPTIONS = {
    "consulting": "고객 상담 및 요구사항 정리 (공사 범위, 예산, 스타일 파악)",
    "estimate": "견적서 작성 및 검토 (공종별 단가, 누락 항목 탐지)",
    "specbook": "마감재 스펙북 생성 (바닥재, 벽지, 타일, 조명, 위생기구 등)",
    "schedule": "공정표 및 공사일보 작성 (작업 순서, 일정, 투입 인원)",
    "contract": "계약서 검토 및 추가공사 확인서 작성",
    "inspection": "준공 검수 체크리스트 및 A/S 대응 문서 작성",
    "architect": "건축 설계 지원 (설계 브리프, 법규 체크, 도면 검토, 인허가)",
}
