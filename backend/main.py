"""
모아Sub - FastAPI 백엔드
POST /analyze 엔드포인트를 통해 구독 점검 결과를 반환합니다.

[처리 흐름]
사용자 구독 입력
  → 결제일까지 남은 일수 계산
  → 카테고리 중복 판단
  → rule-based 점검 점수 계산 및 분류
  → 점검 후보 / 해지 검토 후보에 RAG 설명 첨부
  → 목표 소비 시뮬레이션 계산
  → 결과 반환
"""

import os
import sys
from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 프로젝트 루트를 sys.path에 추가 (다양한 실행 환경 대응)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.rule_engine import analyze_subscriptions
from backend.rag.rag_stub import get_rag_explanation

# ===== FastAPI 앱 초기화 =====
app = FastAPI(
    title="모아Sub API",
    description="구독 소비 인식 지원 서비스 - rule-based 점검 엔진",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Pydantic 요청 모델 =====
class SubscriptionInput(BaseModel):
    service_name: str = Field(..., description="서비스명")
    category: str = Field(..., description="카테고리 (OTT/음악/쇼핑/클라우드/교육/생산성/기타)")
    monthly_fee: int = Field(..., ge=0, description="월 결제금액 (원)")
    usage_count: int = Field(..., ge=0, description="최근 한 달 사용 빈도 (회)")
    satisfaction: int = Field(..., ge=1, le=5, description="만족도 1~5")
    billing_date: str = Field(..., description="다음 결제일 (YYYY-MM-DD)")


class GoalInput(BaseModel):
    product_name: Optional[str] = Field(None, description="목표 상품명")
    target_price: Optional[int] = Field(None, ge=0, description="목표 금액 (원)")


class AnalyzeRequest(BaseModel):
    subscriptions: List[SubscriptionInput] = Field(..., min_length=1)
    goal: Optional[GoalInput] = None


# ===== 목표 소비 시뮬레이션 =====
def calculate_goal_simulation(
    goal: Optional[GoalInput], results: List[Dict]
) -> Optional[Dict]:
    """
    하루 1만 원 저축 기준 대비 구독 점검 시 목표 달성 속도가 몇 % 빨라지는지 계산합니다.

    선택 시뮬레이션이므로 실제 해지를 강제하지 않습니다.
    """
    if goal is None or not goal.target_price or goal.target_price <= 0:
        return None

    target_price = goal.target_price

    # 절감 대상 선택
    # 1순위: 해지 검토 후보 전체 합산
    cancel_candidates = [r for r in results if r["status"] == "해지 검토 후보"]
    if cancel_candidates:
        selected_monthly_saving = sum(r["monthly_fee"] for r in cancel_candidates)
        simulation_services = [r["service_name"] for r in cancel_candidates]
    else:
        # 2순위: 점검 후보 중 가장 비싼 1개
        review_candidates = [r for r in results if r["status"] == "점검 후보"]
        if review_candidates:
            top = max(review_candidates, key=lambda r: r["monthly_fee"])
            selected_monthly_saving = top["monthly_fee"]
            simulation_services = [top["service_name"]]
        else:
            selected_monthly_saving = 0
            simulation_services = []

    # 계산
    daily_extra_saving = round(selected_monthly_saving / 30)
    base_period = target_price / 10000
    after_daily = 10000 + daily_extra_saving
    after_period = target_price / after_daily if after_daily > 0 else base_period
    speed_up_ratio = (
        round((base_period - after_period) / base_period * 100, 2)
        if base_period > 0 else 0.0
    )

    return {
        "product_name": goal.product_name or "",
        "target_price": target_price,
        "simulation_services": simulation_services,
        "selected_monthly_saving": selected_monthly_saving,
        "daily_extra_saving": daily_extra_saving,
        "speed_up_ratio": speed_up_ratio,
    }


# ===== POST /analyze =====
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    구독 목록을 받아 점검 결과를 반환합니다.
    """
    subs_raw = [sub.model_dump() for sub in request.subscriptions]

    # rule-based 점검 엔진 실행
    results = analyze_subscriptions(subs_raw)

    # RAG 설명 첨부 (점검 후보 / 해지 검토 후보만)
    for item in results:
        if item["status"] in ("점검 후보", "해지 검토 후보"):
            rag = get_rag_explanation(item["service_name"], item["category"], item["status"])
        else:
            rag = {"rag_explanation": None, "alternatives": [], "cancel_path": "", "cautions": []}
        item["rag_explanation"] = rag.get("rag_explanation")
        item["alternatives"] = rag.get("alternatives", [])
        item["cancel_path"] = rag.get("cancel_path", "")
        item["cautions"] = rag.get("cautions", [])

    # 요약 통계
    total_monthly = sum(s["monthly_fee"] for s in subs_raw)
    from collections import Counter
    cat_counter = Counter(s["category"] for s in subs_raw)
    duplicate_categories = [c for c, n in cat_counter.items() if n >= 2]

    goal_simulation = calculate_goal_simulation(request.goal, results)

    return {
        "summary": {
            "total_monthly_fee": total_monthly,
            "total_annual_fee": total_monthly * 12,
            "subscription_count": len(subs_raw),
            "duplicate_categories": duplicate_categories,
        },
        "goal_simulation": goal_simulation,
        "results": results,
    }


# ===== GET /health =====
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "모아Sub API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
