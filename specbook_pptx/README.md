# 인테리어 스펙북 PPT 자동 생성기

네이버 이미지 검색 API를 활용하여 자재·마감재 이미지가 포함된 인테리어 스펙북 PPT를 자동 생성합니다.

## 설치

```bash
pip install python-pptx requests
```

## 네이버 API 키 설정

[네이버 개발자 센터](https://developers.naver.com)에서 애플리케이션을 등록하고,  
`generate_specbook.py` 상단의 API 키를 본인 키로 교체하세요:

```python
NAVER_CLIENT_ID = "YOUR_CLIENT_ID"
NAVER_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
```

## 실행

```bash
python generate_specbook.py
```

실행 후 `interior_specbook.pptx` 파일이 생성됩니다.

## 슬라이드 구성

1. **표지**: 프로젝트명, 위치, 면적, 공사기간, 담당자
2. **예산 요약**: 공종별 예산 테이블
3. **공간별 스펙**: 공간당 최대 3개 자재 카드 (이미지 + 제품명 + 선택 이유 + 예상금액 + 상태)

## 데이터 구조

### project (프로젝트 정보)
```python
project = {
    "name": "○○ 아파트 리모델링",
    "location": "서울시 강남구",
    "area": "84㎡ (25.4평)",
    "period": "2026.07.01 ~ 2026.08.15",
    "designer": "홍길동",
    "date": "2026.06.17",
    "version": "1.0"
}
```

### spaces (공간별 자재 목록)
```python
spaces = {
    "거실": [
        {
            "code": "FL-01",          # 자재 코드
            "part": "바닥",           # 부위명
            "product": "LX하우시스 강마루",  # 제품명
            "search_query": "LX하우시스 강마루 거실",  # 이미지 검색어
            "reason": "선택 이유",
            "cost": "350만원",
            "status": "확정"          # 확정 / 검토 중 / 선택 필요
        },
        ...
    ]
}
```

### budget_items (예산 요약)
```python
budget_items = [
    {"name": "철거 공사", "amount": "150만원", "status": "확정"},
    ...
]
```

## 상태 배지 색상

| 상태 | 색상 |
|------|------|
| 확정 | 초록 |
| 검토 중 | 주황 |
| 선택 필요 | 빨강 |
