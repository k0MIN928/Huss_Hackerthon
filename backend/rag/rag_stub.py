"""
모아Sub - RAG 모듈

[우선순위]
1순위: subservice/rag_service.py (SUBSCRIPTION_DB 직접 조회, 16개 서비스)
2순위: service_info.csv 서비스명 정확 매칭
3순위: service_info.csv 카테고리 매칭
4순위: 카테고리 기반 CATEGORY_FALLBACK

함수 인터페이스(입력/출력 형식)는 고정합니다.
  - 함수 시그니처: get_rag_explanation(service_name, category, status) → dict
  - 반환 키: rag_explanation, alternatives, cancel_path, cautions
"""

import os
import pandas as pd
from typing import Dict, List

# service_info.csv 경로 (현재 파일 기준)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "service_info.csv")

# 카테고리별 기본 fallback 설명 (CSV에 없는 서비스 대응)
CATEGORY_FALLBACK = {
    "OTT": {
        "rag_explanation": "이 서비스는 OTT 카테고리의 스트리밍 서비스입니다. 현재 다른 OTT 서비스와 함께 이용 중이라면 실제 시청 빈도를 비교해보세요. 유지 여부는 본인의 콘텐츠 소비 패턴을 기준으로 결정하는 것이 가장 좋습니다.",
        "alternatives": ["넷플릭스", "티빙", "웨이브", "디즈니플러스"],
        "cancel_path": "해당 서비스 앱 → 마이페이지 → 구독 관리 → 해지",
        "cautions": ["남은 이용 기간 확인", "할인 혜택 종료 여부 확인", "연간 결제 여부 확인"],
    },
    "음악": {
        "rag_explanation": "이 서비스는 음악 스트리밍 카테고리입니다. 다른 음악 서비스와 중복으로 이용 중이라면 사용 빈도를 비교해 우선순위를 정해보세요. 통신사 제휴 할인 여부도 확인하는 것이 좋습니다.",
        "alternatives": ["멜론", "스포티파이", "유튜브 프리미엄", "애플뮤직"],
        "cancel_path": "해당 서비스 앱 → 마이페이지 → 이용권 관리 → 해지",
        "cautions": ["통신사 제휴 할인 여부 확인", "남은 이용 기간 확인", "가족 플랜 이용 여부 확인"],
    },
    "쇼핑": {
        "rag_explanation": "이 서비스는 쇼핑 카테고리의 멤버십입니다. 월 구독료 대비 실제로 받은 혜택(배송비 절감, 포인트 적립 등)을 계산해보면 유지 여부 판단에 도움이 됩니다.",
        "alternatives": ["쿠팡와우", "네이버플러스 멤버십"],
        "cancel_path": "해당 서비스 앱 → 마이페이지 → 멤버십 관리 → 해지",
        "cautions": ["포인트 잔액 확인", "남은 혜택 기간 확인", "자동 갱신 일정 확인"],
    },
    "클라우드": {
        "rag_explanation": "이 서비스는 클라우드 스토리지 카테고리입니다. 실제 사용 중인 저장 용량을 확인하고, 무료 플랜으로 전환 가능한지 먼저 검토해보세요. 데이터 이전 계획이 있다면 충분한 준비 시간을 두는 것이 좋습니다.",
        "alternatives": ["iCloud", "구글 원", "원드라이브", "드롭박스"],
        "cancel_path": "해당 서비스 설정 → 구독 관리 → 해지 또는 다운그레이드",
        "cautions": ["저장 데이터 백업 여부 확인", "다른 기기 동기화 여부 확인", "무료 플랜 전환 가능 여부 확인"],
    },
    "교육": {
        "rag_explanation": "이 서비스는 교육 카테고리의 학습 플랫폼입니다. 실제 학습 완료율이나 콘텐츠 소비 빈도를 점검해보세요. 강의를 완료할 계획이 있다면 일정을 확정한 뒤 유지 여부를 결정하는 것이 좋습니다.",
        "alternatives": ["클래스101", "패스트캠퍼스", "유데미", "코세라"],
        "cancel_path": "해당 서비스 홈페이지 → 마이페이지 → 구독 관리 → 해지",
        "cautions": ["완료하지 못한 강의 일정 확인", "다운로드 콘텐츠 접근 여부 확인", "할인 이벤트 기간 여부 확인"],
    },
    "생산성": {
        "rag_explanation": "이 서비스는 생산성 카테고리의 구독 앱입니다. 업무나 일상에서 실제로 활용하는 빈도를 점검해보세요. 무료 플랜 또는 대체 도구로 전환 가능한지 비교해보는 것도 좋습니다.",
        "alternatives": ["노션", "구글 워크스페이스", "마이크로소프트 365"],
        "cancel_path": "해당 서비스 홈페이지 → 계정 설정 → 구독 취소",
        "cautions": ["데이터 내보내기 여부 확인", "팀 또는 공유 작업 여부 확인", "무료 플랜 기능 범위 확인"],
    },
    "기타": {
        "rag_explanation": "이 구독 서비스의 이용 패턴을 점검해보세요. 월 요금 대비 실제 활용도를 직접 계산해보면 유지 여부 결정에 도움이 됩니다. 해지 전에는 남은 이용 기간과 자동 갱신 일정을 반드시 확인하세요.",
        "alternatives": [],
        "cancel_path": "해당 서비스 앱 또는 홈페이지에서 구독 해지 가능",
        "cautions": ["남은 이용 기간 확인", "자동 갱신 일정 확인", "환불 정책 확인"],
    },
}

# CSV 데이터 캐싱 (최초 1회 로드)
_service_df = None


def _load_service_info() -> pd.DataFrame:
    """service_info.csv를 로드합니다. (캐싱)"""
    global _service_df
    if _service_df is None:
        try:
            _service_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        except Exception:
            _service_df = pd.DataFrame()
    return _service_df


def get_rag_explanation(service_name: str, category: str, status: str) -> Dict:
    """
    서비스명 또는 카테고리를 기반으로 RAG 설명 정보를 반환합니다.

    [우선순위]
    1순위: subservice/rag_service.py (성단아 RAG - LLM + SUBSCRIPTION_DB 11종)
    2순위: service_info.csv 정확 매칭
    3순위: 카테고리 기반 CATEGORY_FALLBACK

    Args:
        service_name: 구독 서비스명 (예: "티빙")
        category: 카테고리 (예: "OTT")
        status: ML 예측 상태 (예: "점검 후보" / "해지 검토 후보")

    Returns:
        {
            "rag_explanation": str,
            "alternatives": List[str],
            "cancel_path": str,
            "cautions": List[str],
        }
    """
    # 1순위: SUBSCRIPTION_DB 직접 조회 (subservice/rag_service.py)
    try:
        from subservice.rag_service import generate_rag_response
        result = generate_rag_response(service_name, status)
        if result is not None:
            return {
                "rag_explanation": result.get("rag_explanation", ""),
                "alternatives": result.get("alternatives", []),
                "cancel_path": result.get("cancel_path", ""),
                "cautions": result.get("cautions", []),
            }
    except Exception:
        pass

    # 2순위: service_info.csv 정확 매칭
    df = _load_service_info()
    matched = None
    if not df.empty:
        row = df[df["service_name"] == service_name]
        if not row.empty:
            matched = row.iloc[0]

    # 3순위: 카테고리로 첫 번째 항목 매칭 (CSV)
    if matched is None and not df.empty:
        row = df[df["category"] == category]
        if not row.empty:
            matched = row.iloc[0]

    if matched is not None:
        alternatives_raw = str(matched.get("alternatives", ""))
        cautions_raw = str(matched.get("cautions", ""))
        return {
            "rag_explanation": str(matched.get("rag_explanation", "")),
            "alternatives": [
                a.strip() for a in alternatives_raw.split("|") if a.strip()
            ],
            "cancel_path": str(matched.get("cancel_path", "서비스 앱 또는 홈페이지 확인")),
            "cautions": [
                c.strip() for c in cautions_raw.split("|") if c.strip()
            ],
        }

    # 4순위: 카테고리 기반 CATEGORY_FALLBACK
    fallback = CATEGORY_FALLBACK.get(category, CATEGORY_FALLBACK["기타"])
    explanation = fallback["rag_explanation"]
    if service_name and service_name not in explanation:
        explanation = f"{service_name}은(는) {explanation[explanation.find('는')+1:].strip()}"

    return {
        "rag_explanation": explanation,
        "alternatives": fallback["alternatives"],
        "cancel_path": fallback["cancel_path"],
        "cautions": fallback["cautions"],
    }
