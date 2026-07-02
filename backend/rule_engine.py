"""
모아Sub - rule-based 점검 엔진

실제 사용자 행동 데이터가 없는 MVP 단계에서
학습 기반 모델 대신 설명 가능한 규칙 기반 점검 기준을 사용합니다.

[점검 기준]
- 사용 빈도 (usage_count)
- 만족도 (satisfaction)
- 월 결제금액 (monthly_fee)
- 결제일 임박 여부 (days_until_billing)
- 카테고리 중복 여부 (category_count)
- 카테고리별 예외 패턴

[분류 결과]
- 유지 후보:      점검 점수 0~2
- 점검 후보:      점검 점수 3~5
- 해지 검토 후보: 점검 점수 6 이상

[중요]
- "해지 추천"이라는 표현은 사용하지 않습니다.
- 점검 결과는 정답이 아닌 사용자의 판단을 돕는 참고 정보입니다.
"""

from collections import Counter
from datetime import date, datetime
from typing import Dict, List, Tuple


# ===== 결제일까지 남은 일수 =====

def calculate_days_until_billing(billing_date: str) -> int:
    """오늘 날짜 기준 결제일까지 남은 일수를 반환합니다."""
    try:
        billing = datetime.strptime(billing_date, "%Y-%m-%d").date()
        delta = (billing - date.today()).days
        return max(0, delta)
    except (ValueError, TypeError):
        return 30


# ===== 카테고리 중복 집계 =====

def analyze_category_duplicates(subscriptions: List[Dict]) -> Counter:
    """구독 목록에서 카테고리별 개수를 집계합니다."""
    return Counter(sub["category"] for sub in subscriptions)


# ===== 점검 점수 계산 =====

def calculate_check_score(
    subscription: Dict,
    category_count: int,
    days_until_billing: int,
) -> int:
    """
    구독별 점검 점수를 계산합니다.

    [기본 점수 기준]
    - usage_count <= 2          : +2
    - usage_count <= 5          : +1
    - satisfaction <= 2         : +2
    - satisfaction == 3         : +1
    - monthly_fee >= 15000      : +2
    - monthly_fee >= 10000      : +1
    - category_count >= 2       : +1
    - category_count >= 3       : +1 추가
    - days_until_billing <= 3   : +2
    - days_until_billing <= 7   : +1

    [카테고리별 예외]
    - 클라우드: 만족도 높으면 사용 빈도 낮아도 점수 감소 (백업/저장공간 특성)
    - 생산성:   만족도 보통 이상이면 점수 감소 (학업/업무 도구 특성)
    - OTT:      중복 + 저사용이면 추가 점수
    - 쇼핑:     고빈도 사용이면 사용 빈도 페널티 없음 (멤버십 혜택 활용)
    - 음악:     만족도 높으면 점수 감소 (습관적·정서적 서비스 특성)
    - 교육:     저사용 + 저만족 + 중복이면 추가 점수 (guilt subscription)
    """
    usage = subscription["usage_count"]
    satisfaction = subscription["satisfaction"]
    fee = subscription["monthly_fee"]
    category = subscription["category"]

    score = 0

    # ① 사용 빈도
    if category == "쇼핑" and usage >= 10:
        pass  # 멤버십 고빈도 이용 → 페널티 없음
    elif usage <= 2:
        score += 2
    elif usage <= 5:
        score += 1

    # ② 만족도
    if satisfaction <= 2:
        score += 2
    elif satisfaction == 3:
        score += 1

    # ③ 월 결제금액
    if fee >= 15000:
        score += 2
    elif fee >= 10000:
        score += 1

    # ④ 카테고리 중복
    if category_count >= 2:
        score += 1
    if category_count >= 3:
        score += 1

    # ⑤ OTT 중복 + 저사용 추가 페널티
    if category == "OTT" and category_count >= 2 and usage <= 5:
        score += 1

    # ⑥ 교육 저사용 + 저만족 + 중복 추가 페널티
    if category == "교육" and usage <= 2 and satisfaction <= 2 and category_count >= 2:
        score += 1

    # ⑦ 결제일 임박
    if days_until_billing <= 3:
        score += 2
    elif days_until_billing <= 7:
        score += 1

    # ⑧ 카테고리 예외: 점수 감소
    if category == "클라우드" and satisfaction >= 4:
        # 저장공간·백업 목적 → 사용 빈도가 낮아도 유지 필요성 인정
        score = max(0, score - 1)

    if category == "생산성" and satisfaction >= 3:
        # 학업·업무 도구 → 자주 열지 않아도 필요한 서비스일 수 있음
        score = max(0, score - 1)

    if category == "음악" and satisfaction >= 4:
        # 습관적·정서적 서비스 → 만족도 높으면 유지 가능성 높음
        score = max(0, score - 1)

    return score


# ===== 상태 분류 =====

def classify_subscription(score: int) -> Tuple[str, str]:
    """
    점검 점수에 따라 상태와 우선순위 레벨을 반환합니다.

    Returns:
        (status, priority_level)
    """
    if score <= 2:
        return "유지 후보", "안정"
    elif score <= 5:
        return "점검 후보", "주의"
    else:
        return "해지 검토 후보", "높음"


# ===== 점검 사유 생성 =====

def generate_rule_reasons(
    subscription: Dict,
    category_count: int,
    days_until_billing: int,
    score: int,
) -> List[str]:
    """
    점검 기준에 따른 사유 문장 목록을 생성합니다.
    사용자가 스스로 인식하고 판단할 수 있도록 설명형으로 작성합니다.
    """
    reasons = []
    usage = subscription["usage_count"]
    satisfaction = subscription["satisfaction"]
    fee = subscription["monthly_fee"]
    category = subscription["category"]

    # 카테고리 중복
    if category_count >= 3:
        reasons.append(f"같은 {category} 카테고리에 {category_count}개의 구독이 있습니다.")
    elif category_count >= 2:
        reasons.append(f"같은 {category} 카테고리에 여러 구독이 있습니다.")

    # 사용 빈도
    if category == "쇼핑" and usage >= 10:
        reasons.append("사용 빈도가 높아 멤버십 혜택을 충분히 활용하고 있습니다.")
    elif usage <= 2:
        reasons.append("최근 한 달 사용 빈도가 매우 낮습니다.")
    elif usage <= 5:
        reasons.append("최근 한 달 사용 빈도가 낮은 편입니다.")

    # 만족도
    if satisfaction <= 2:
        reasons.append(f"만족도가 낮습니다 ({satisfaction}/5).")
    elif satisfaction == 3:
        reasons.append(f"만족도가 보통 수준입니다 ({satisfaction}/5).")
    elif satisfaction >= 4:
        reasons.append(f"만족도가 높습니다 ({satisfaction}/5).")

    # 요금
    if fee >= 15000:
        reasons.append(f"월 결제금액이 {fee:,}원으로 높은 편입니다.")
    elif fee >= 10000:
        reasons.append(f"월 결제금액이 {fee:,}원입니다.")

    # OTT 중복 + 저사용 보충 설명
    if category == "OTT" and category_count >= 2 and usage <= 5:
        reasons.append("OTT 구독이 여러 개이고 사용 빈도가 낮아 점검이 필요합니다.")

    # 교육 저사용 + 저만족
    if category == "교육" and usage <= 2 and satisfaction <= 2:
        reasons.append("학습 빈도와 만족도가 모두 낮습니다. 실제 이용 여부를 확인해보세요.")

    # 클라우드 특성 안내
    if category == "클라우드" and satisfaction >= 4:
        reasons.append("저장공간·백업 목적으로 이용 빈도가 낮아도 유지 필요성이 있을 수 있습니다.")

    # 결제일 임박
    if days_until_billing <= 3:
        reasons.append(f"결제일까지 {days_until_billing}일 남았습니다. 결제 전 점검을 권장합니다.")
    elif days_until_billing <= 7:
        reasons.append(f"결제일까지 {days_until_billing}일 남았습니다.")

    # 기본 문구 (해당 사항 없을 때)
    if not reasons:
        reasons.append("사용 빈도, 만족도, 금액 기준 모두 양호합니다.")

    return reasons


# ===== 전체 분석 =====

def analyze_subscriptions(subscriptions: List[Dict]) -> List[Dict]:
    """
    구독 목록 전체를 분석하여 각 구독의 점검 결과를 반환합니다.

    Args:
        subscriptions: service_name, category, monthly_fee, usage_count,
                       satisfaction, billing_date 를 포함하는 딕셔너리 목록
    Returns:
        각 구독의 점검 결과 딕셔너리 목록
    """
    category_counter = analyze_category_duplicates(subscriptions)
    results = []

    for sub in subscriptions:
        days = calculate_days_until_billing(sub["billing_date"])
        cat_count = category_counter[sub["category"]]
        score = calculate_check_score(sub, cat_count, days)
        status, priority_level = classify_subscription(score)
        reasons = generate_rule_reasons(sub, cat_count, days, score)

        results.append({
            "service_name": sub["service_name"],
            "category": sub["category"],
            "monthly_fee": sub["monthly_fee"],
            "annual_fee": sub["monthly_fee"] * 12,
            "days_until_billing": days,
            "status": status,
            "check_score": score,
            "priority_level": priority_level,
            "rule_reasons": reasons,
        })

    return results
