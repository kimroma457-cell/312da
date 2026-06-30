# 인테리어 / 건축 전문 에이전트 시스템

인테리어 업자 및 건축가를 위한 AI 에이전트 시스템입니다.
상담부터 견적, 스펙북, 공정표, 계약, 검수, 하자관리, 건축 설계까지 실무를 지원합니다.

## 설치

```bash
pip install anthropic
```

## 실행 방법

### 환경 변수 설정

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 메인 에이전트 (통합 실행)

```bash
cd agents
python main_agent.py
```

메인 에이전트는 사용자의 의도를 파악하여 자동으로 적절한 하위 에이전트로 라우팅합니다.

### 에이전트 직접 지정

메인 에이전트 실행 중 `@에이전트이름 메시지` 형식으로 직접 지정 가능합니다:

```
나: @estimate 30평 아파트 전체 리모델링 견적서 만들어줘
나: @specbook 모던 미니멀 스타일, 중급 예산으로 스펙북 생성해줘
나: @architect 서울 종로구 대지 200평, 근린생활시설 건축허가 체크리스트 알려줘
```

### 개별 에이전트 실행

```bash
cd agents
python consulting_agent.py   # 고객 상담
python estimate_agent.py     # 견적 작성/검토
python specbook_agent.py     # 마감재 스펙북
python schedule_agent.py     # 공정표/공사일보
python contract_agent.py     # 계약 검토
python inspection_agent.py   # 준공 검수/하자
python architect_agent.py    # 건축 설계 지원
```

## 에이전트 목록

| 에이전트 | 파일 | 주요 기능 |
|---------|------|----------|
| 메인 오케스트레이터 | `main_agent.py` | 의도 파악 및 라우팅 |
| 상담 에이전트 | `consulting_agent.py` | 고객 요구사항 정리 |
| 견적 에이전트 | `estimate_agent.py` | 견적서 작성 및 누락 탐지 |
| 스펙북 에이전트 | `specbook_agent.py` | 마감재 스펙북 생성 |
| 공정표 에이전트 | `schedule_agent.py` | 공정표 및 공사일보 |
| 계약 에이전트 | `contract_agent.py` | 계약 검토, 변경공사 확인서 |
| 검수/하자 에이전트 | `inspection_agent.py` | 준공 체크리스트, A/S |
| 건축 설계 에이전트 | `architect_agent.py` | 설계 브리프, 법규, 도면 |

## 지식 베이스 구조

```
interior_architect_agent_knowledge/
├── 01_공통_상담자료/      고객 상담 질문지, 현장조사 체크리스트
├── 02_인테리어_업자/      견적DB, 공정표, 공사일보, 검수 체크리스트
├── 03_건축가/            설계 브리프, 공간 프로그램, 인허가 목록
├── 04_법규_계약/         표준계약서, 법규 체크리스트, 분쟁해결기준
├── 05_마감재_스펙북/      바닥재, 타일, 조명, 위생기구, 가구 DB
└── 06_프롬프트/          각 에이전트 시스템 프롬프트 및 작업별 프롬프트
```

## 모델 변경

기본 모델은 `claude-sonnet-4-6`입니다. 변경하려면:

```bash
export CLAUDE_MODEL="claude-opus-4-8"
```

## 주의사항

- 법규 관련 최종 판단은 건축사 및 관할 구청에서 확인하세요.
- 단가 정보는 2024년 수도권 기준이며 실제와 차이가 있을 수 있습니다.
- 계약 분쟁 시 변호사 또는 한국소비자원에 상담하세요.
