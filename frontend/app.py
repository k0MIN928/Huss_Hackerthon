"""
모아Sub - Streamlit 프론트엔드
랜딩페이지 → 구독 점검 → 분석 결과
"""

import base64
import os
from datetime import date, timedelta

import altair as alt
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="모아Sub - 구독 소비 인식 지원",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===== 세션 상태 초기화 =====
if "page" not in st.session_state:
    st.session_state["page"] = "landing"
if "target_name" not in st.session_state:
    st.session_state["target_name"] = ""
if "target_price" not in st.session_state:
    st.session_state["target_price"] = 0
if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "switch_to_result" not in st.session_state:
    st.session_state.switch_to_result = False
if "switch_to_detail" not in st.session_state:
    st.session_state["switch_to_detail"] = False
if "detail_service" not in st.session_state:
    st.session_state["detail_service"] = ""

# ===== 탭 자동 전환 =====
if st.session_state.switch_to_result:
    st.session_state.switch_to_result = False
    components.html(
        """
        <script>
            setTimeout(function() {
                var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                if (tabs.length > 1) { tabs[1].click(); }
            }, 300);
        </script>
        """,
        height=0,
    )

if st.session_state.switch_to_detail:
    st.session_state.switch_to_detail = False
    components.html(
        """
        <script>
            setTimeout(function() {
                // 전체 탭: [구독입력, 점검결과, 대시보드, 우선점검대상, 전체목록, 상세설명, 목표시뮬레이션]
                var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                if (tabs.length > 5) { tabs[5].click(); }
            }, 300);
        </script>
        """,
        height=0,
    )

# ===== CSS =====
st.markdown("""
<style>
/* ── 상태 배지 ── */
.status-maintain { background:#d1fae5; color:#065f46; padding:4px 12px; border-radius:12px; font-weight:600; }
.status-review   { background:#fef3c7; color:#92400e; padding:4px 12px; border-radius:12px; font-weight:600; }
.status-cancel   { background:#fee2e2; color:#991b1b; padding:4px 12px; border-radius:12px; font-weight:600; }
.score-badge     { background:#e2e8f0; color:#1e293b; padding:3px 10px; border-radius:8px; font-size:0.9rem; font-weight:600; }
.priority-low    { background:#d1fae5; color:#065f46; padding:3px 10px; border-radius:8px; font-size:0.85rem; }
.priority-mid    { background:#fef3c7; color:#92400e; padding:3px 10px; border-radius:8px; font-size:0.85rem; }
.priority-high   { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:8px; font-size:0.85rem; }

/* ── 앱 이름 그라디언트 텍스트 ── */
.brand-name {
    background: linear-gradient(135deg, #F97066 0%, #FB923C 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: inline-block;
}

/* ── 메트릭 칸 구분 ── */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px !important;
}

/* ── selectbox 타이핑 비활성화 ── */
div[data-baseweb="select"] input {
    pointer-events: none !important;
    caret-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ===== 사용 빈도 범위 =====
USAGE_RANGES = {
    "0회 — 사용 안 함":       0,   # 아예 안 씀
    "1~4회 — 가끔":           2,   # 한 달에 1~4회, 주 1회 미만
    "5~12회 — 보통":          8,   # 한 달에 5~12회, 주 1~3회
    "13~25회 — 자주":        18,   # 한 달에 13~25회, 거의 매일
    "26회 이상 — 매우 자주":  30,  # 하루 1회 이상
}
USAGE_LABELS = {v: k for k, v in USAGE_RANGES.items()}

# ===== 페르소나 데이터 =====
BILLING_OFFSETS = [2, 5, 10, 20, 15]

PERSONAS = [
    {
        "name": "대학생 A — OTT 중복 + AI 입문형",
        "description": "넷플릭스를 중심으로 OTT를 여러 개 구독하다 AI도 추가했지만 중복 지출이 쌓인 상태",
        "goal_product": "무선 이어폰",
        "goal_price": 250000,
        "subscriptions": [
            {"service_name": "넷플릭스",       "category": "OTT",    "monthly_fee": 17000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "티빙",            "category": "OTT",    "monthly_fee": 13900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "디즈니플러스",    "category": "OTT",    "monthly_fee":  9900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "유튜브 프리미엄", "category": "음악",   "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "ChatGPT Plus",   "category": "AI/LLM", "monthly_fee": 28000, "usage_count":  8, "satisfaction": 4},
        ],
    },
    {
        "name": "사회초년생 B — 생활 구독 + 클라우드 중복형",
        "description": "직장 생활 시작 후 편의 서비스를 하나씩 추가했지만 클라우드가 두 개로 겹쳐 있음",
        "goal_product": "태블릿",
        "goal_price": 600000,
        "subscriptions": [
            {"service_name": "스포티파이",      "category": "음악",     "monthly_fee": 10900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "쿠팡와우",        "category": "쇼핑",     "monthly_fee":  7890, "usage_count": 18, "satisfaction": 4},
            {"service_name": "iCloud",          "category": "클라우드", "monthly_fee":  3300, "usage_count":  2, "satisfaction": 5},
            {"service_name": "Google One",      "category": "클라우드", "monthly_fee":  2400, "usage_count":  2, "satisfaction": 4},
            {"service_name": "Notion AI",       "category": "AI 생산성","monthly_fee": 14000, "usage_count":  8, "satisfaction": 4},
        ],
    },
    {
        "name": "대학생 C — 소액 구독 누적 + AI 방치형",
        "description": "개별 구독료는 작다고 생각했지만 AI 포함 여러 개가 쌓여 월 지출이 커진 상태",
        "goal_product": "여행 경비",
        "goal_price": 500000,
        "subscriptions": [
            {"service_name": "쿠팡와우",           "category": "쇼핑",   "monthly_fee":  7890, "usage_count": 18, "satisfaction": 4},
            {"service_name": "멜론",               "category": "음악",   "monthly_fee":  7900, "usage_count":  2, "satisfaction": 3},
            {"service_name": "티빙",               "category": "OTT",    "monthly_fee": 13900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "웨이브",             "category": "OTT",    "monthly_fee": 10900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "Perplexity Pro",     "category": "AI/LLM", "monthly_fee": 28000, "usage_count":  0, "satisfaction": 2},
        ],
    },
    {
        "name": "직장인 D — 무료체험 방치 + AI 자동결제형",
        "description": "무료체험으로 시작한 서비스 여러 개가 자동결제로 이어지는 중, AI도 포함",
        "goal_product": "스마트워치",
        "goal_price": 350000,
        "subscriptions": [
            {"service_name": "유튜브 프리미엄", "category": "음악", "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "쿠팡와우",        "category": "쇼핑", "monthly_fee":  7890, "usage_count":  8, "satisfaction": 4},
            {"service_name": "디즈니플러스",    "category": "OTT",  "monthly_fee":  9900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "밀리의서재",      "category": "교육", "monthly_fee":  9900, "usage_count":  0, "satisfaction": 2},
            {"service_name": "Claude Pro",      "category": "AI/LLM","monthly_fee": 28000, "usage_count":  0, "satisfaction": 2},
        ],
    },
    {
        "name": "대학생 E — 콘텐츠+AI 고만족 유지형",
        "description": "OTT·음악과 AI를 함께 구독하지만 모두 자주 쓰고 만족도가 높은 상태",
        "goal_product": "콘서트 티켓",
        "goal_price": 180000,
        "subscriptions": [
            {"service_name": "넷플릭스",        "category": "OTT",    "monthly_fee": 17000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "유튜브 프리미엄", "category": "음악",   "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "ChatGPT Plus",   "category": "AI/LLM", "monthly_fee": 28000, "usage_count":  8, "satisfaction": 5},
            {"service_name": "iCloud",          "category": "클라우드","monthly_fee":  3300, "usage_count":  2, "satisfaction": 4},
        ],
    },
    {
        "name": "취업준비생 F — 학습+AI 미사용 누적형",
        "description": "자기계발 목적으로 교육·AI 구독을 여러 개 시작했지만 실제 사용 빈도가 낮은 상태",
        "goal_product": "자격증 응시료",
        "goal_price": 200000,
        "subscriptions": [
            {"service_name": "클래스101",           "category": "교육",    "monthly_fee": 19900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "패스트캠퍼스",        "category": "교육",    "monthly_fee": 29000, "usage_count":  2, "satisfaction": 3},
            {"service_name": "밀리의서재",          "category": "교육",    "monthly_fee":  9900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "Notion AI",           "category": "AI 생산성","monthly_fee": 14000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "네이버플러스 멤버십", "category": "쇼핑",    "monthly_fee":  4900, "usage_count":  2, "satisfaction": 3},
        ],
    },
    {
        "name": "대학생 G — AI 학습도구 중복 + OTT 혼합형",
        "description": "과제·글쓰기용 AI를 여러 개 구독했지만 실제 사용은 한두 개에 집중, OTT도 함께 이용 중",
        "goal_product": "노트북",
        "goal_price": 1200000,
        "subscriptions": [
            {"service_name": "ChatGPT Plus",  "category": "AI/LLM",  "monthly_fee": 28000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "Claude Pro",    "category": "AI/LLM",  "monthly_fee": 28000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "Perplexity Pro","category": "AI/LLM",  "monthly_fee": 28000, "usage_count":  2, "satisfaction": 3},
            {"service_name": "넷플릭스",      "category": "OTT",     "monthly_fee": 17000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "유튜브 프리미엄","category": "음악",   "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
        ],
    },
    {
        "name": "개발자 준비생 H — 코딩 AI + 생활 구독 혼합형",
        "description": "코딩 AI를 여러 개 구독 중이며, 쇼핑·음악 서비스도 함께 이용하는 현실적인 구독 구성",
        "goal_product": "맥북",
        "goal_price": 1500000,
        "subscriptions": [
            {"service_name": "ChatGPT Plus",  "category": "AI/LLM",   "monthly_fee": 28000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "Cursor Pro",    "category": "AI 생산성", "monthly_fee": 28000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "GitHub Copilot","category": "AI 생산성", "monthly_fee": 14000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "쿠팡와우",      "category": "쇼핑",      "monthly_fee":  7890, "usage_count": 18, "satisfaction": 4},
            {"service_name": "유튜브 프리미엄","category": "음악",     "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
        ],
    },
    {
        "name": "콘텐츠 제작자 I — AI 제작도구 + 콘텐츠 소비 혼합형",
        "description": "이미지·음성 AI 도구를 활용하면서 OTT·음악도 함께 구독, 프로젝트 없는 달엔 미사용 도구 발생",
        "goal_product": "카메라",
        "goal_price": 800000,
        "subscriptions": [
            {"service_name": "Canva Pro",     "category": "AI 콘텐츠 제작", "monthly_fee": 21000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "Midjourney",    "category": "AI 콘텐츠 제작", "monthly_fee": 42000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "ElevenLabs",    "category": "AI 콘텐츠 제작", "monthly_fee": 30000, "usage_count":  0, "satisfaction": 2},
            {"service_name": "넷플릭스",      "category": "OTT",            "monthly_fee": 17000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "유튜브 프리미엄","category": "음악",          "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
        ],
    },
    {
        "name": "직장인 J — 생산성 AI 누적 + 일상 구독 혼합형",
        "description": "업무용 AI 구독을 여러 개 늘렸지만 기능이 겹치고, 쇼핑·클라우드도 함께 이용 중",
        "goal_product": "해외여행",
        "goal_price": 600000,
        "subscriptions": [
            {"service_name": "ChatGPT Plus",         "category": "AI/LLM",   "monthly_fee": 28000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "Microsoft Copilot Pro", "category": "AI 생산성","monthly_fee": 28000, "usage_count":  2, "satisfaction": 3},
            {"service_name": "쿠팡와우",             "category": "쇼핑",     "monthly_fee":  7890, "usage_count": 18, "satisfaction": 4},
            {"service_name": "유튜브 프리미엄",      "category": "음악",     "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "Google One",            "category": "클라우드", "monthly_fee":  3400, "usage_count":  8, "satisfaction": 5},
        ],
    },
    {
        "name": "취업준비생 K — AI 방치 + 교육·음악 혼합형",
        "description": "면접 준비로 시작한 AI 구독 중 일부는 미사용, 교육·음악 서비스도 같이 이어지고 있음",
        "goal_product": "자격증 응시료",
        "goal_price": 200000,
        "subscriptions": [
            {"service_name": "Claude Pro",     "category": "AI/LLM", "monthly_fee": 28000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "Perplexity Pro", "category": "AI/LLM", "monthly_fee": 28000, "usage_count":  0, "satisfaction": 2},
            {"service_name": "패스트캠퍼스",   "category": "교육",   "monthly_fee": 29000, "usage_count":  2, "satisfaction": 3},
            {"service_name": "클래스101",      "category": "교육",   "monthly_fee": 19900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "멜론",           "category": "음악",   "monthly_fee":  7900, "usage_count":  8, "satisfaction": 4},
        ],
    },
    {
        "name": "대학원생 L — 연구 AI + 클라우드 혼합형",
        "description": "논문 작성·자료 탐색에 AI를 활용하고 클라우드 두 개로 연구 자료를 관리 중",
        "goal_product": "연구 장비",
        "goal_price": 500000,
        "subscriptions": [
            {"service_name": "ChatGPT Plus",  "category": "AI/LLM",  "monthly_fee": 28000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "Claude Pro",    "category": "AI/LLM",  "monthly_fee": 28000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "Perplexity Pro","category": "AI/LLM",  "monthly_fee": 28000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "Google One",    "category": "클라우드", "monthly_fee":  3400, "usage_count":  8, "satisfaction": 5},
            {"service_name": "iCloud",        "category": "클라우드", "monthly_fee":  3300, "usage_count":  2, "satisfaction": 4},
        ],
    },
]


def build_persona_subscriptions(persona: dict) -> list:
    today = date.today()
    return [
        {**sub, "billing_date": (today + timedelta(days=BILLING_OFFSETS[i % len(BILLING_OFFSETS)])).strftime("%Y-%m-%d")}
        for i, sub in enumerate(persona["subscriptions"])
    ]


# ===== 배지 헬퍼 =====
def status_badge(status: str) -> str:
    cls = {"유지 후보": "status-maintain", "점검 후보": "status-review", "해지 검토 후보": "status-cancel"}
    return f'<span class="{cls.get(status, "status-maintain")}">{status}</span>'


def priority_badge(priority_level: str) -> str:
    cls = {"안정": "priority-low", "주의": "priority-mid", "높음": "priority-high"}
    return f'<span class="{cls.get(priority_level, "priority-low")}">점검 우선순위: {priority_level}</span>'


# ============================================================
# 페이지 분기: 랜딩 vs 구독 점검
# ============================================================

if st.session_state["page"] == "landing":

    # ============================================================
    # 랜딩페이지
    # ============================================================

    # ── 히어로 오른쪽 콘텐츠 결정 (이미지 or 미니 대시보드) ──
    _img_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "assets", "landing_main.png"
    )
    if os.path.exists(_img_path):
        with open(_img_path, "rb") as _f:
            _img_b64 = base64.b64encode(_f.read()).decode()
        _hero_right = f'<img src="data:image/png;base64,{_img_b64}" style="width:100%;border-radius:14px;object-fit:cover;max-height:280px;" />'
    else:
        _hero_right = (
            '<div style="background:rgba(255,255,255,0.15);border-radius:16px;padding:24px;border:1px solid rgba(255,255,255,0.25);">'
            '<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;opacity:0.65;margin-bottom:14px;text-transform:uppercase;">구독 현황 예시</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
            '<div style="background:rgba(255,255,255,0.18);border-radius:10px;padding:14px 12px;">'
            '<div style="font-size:0.68rem;opacity:0.8;margin-bottom:6px;">월 구독 수</div>'
            '<div style="font-size:1.55rem;font-weight:800;line-height:1;">5개</div></div>'
            '<div style="background:rgba(255,255,255,0.18);border-radius:10px;padding:14px 12px;">'
            '<div style="font-size:0.68rem;opacity:0.8;margin-bottom:6px;">월 반복 지출</div>'
            '<div style="font-size:1.3rem;font-weight:800;line-height:1;">66,000원</div></div>'
            '<div style="background:rgba(255,255,255,0.18);border-radius:10px;padding:14px 12px;">'
            '<div style="font-size:0.68rem;opacity:0.8;margin-bottom:6px;">다음 결제</div>'
            '<div style="font-size:1.55rem;font-weight:800;line-height:1;">D-3</div></div>'
            '<div style="background:#fbbf24;border-radius:10px;padding:14px 12px;color:#1e293b;">'
            '<div style="font-size:0.68rem;font-weight:600;margin-bottom:6px;">카테고리 중복</div>'
            '<div style="font-size:1rem;font-weight:800;line-height:1.35;">OTT<br>2개 이용 중</div></div>'
            '</div></div>'
        )

    # ── 히어로 블록 (2열) ──
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#3B82F6 0%,#6366F1 100%);'
        f'border-radius:20px;padding:52px 48px 44px;color:white;margin-bottom:28px;'
        f'display:flex;align-items:center;gap:48px;">'
        f'<div style="flex:3;min-width:0;">'
        f'<div style="font-size:1.4rem;font-weight:800;letter-spacing:0.06em;margin-bottom:20px;">💳 &nbsp;<span style="background:linear-gradient(135deg,#F97066,#FB923C);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">모아Sub</span></div>'
        f'<div style="font-size:2.1rem;font-weight:800;line-height:1.38;margin-bottom:20px;">'
        f'사고 싶은 목표를 정하고,<br>자동결제로 새어나가는<br>구독 지출을 점검해보세요.</div>'
        f'<div style="font-size:0.97rem;line-height:1.78;opacity:0.85;">'
        f'모아Sub은 반복되는 구독 지출을 한눈에 확인하고,<br>'
        f'사용 빈도·만족도·결제일·카테고리 중복 여부를 바탕으로<br>'
        f'구독 상태를 점검할 수 있도록 돕는 서비스입니다.</div>'
        f'</div>'
        f'<div style="flex:2;min-width:0;">{_hero_right}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── 목표 소비 입력 카드 ──
    with st.container(border=True):
        st.markdown(
            '<p style="font-size:1.05rem;font-weight:700;color:#1e293b;margin:0 0 6px 0;">목표 소비 설정</p>'
            '<p style="font-size:0.875rem;color:#64748b;line-height:1.65;margin:0 0 4px 0;">'
            '사고 싶은 항목과 목표 금액을 입력하면, 구독 점검 결과에서 목표 달성 속도 변화를 확인할 수 있습니다.</p>',
            unsafe_allow_html=True,
        )

        l1, l2 = st.columns(2)
        with l1:
            landing_target_name = st.text_input(
                "사고 싶은 항목명",
                placeholder="예: 무선 이어폰, 여행 경비, 콘서트 티켓",
                value=st.session_state["target_name"],
            )
        with l2:
            landing_target_price = st.number_input(
                "목표 금액 (원)",
                min_value=0,
                value=int(st.session_state["target_price"]),
                step=1000,
            )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("목표 설정하고 구독 점검 시작하기", type="primary", use_container_width=True):
                st.session_state["target_name"] = landing_target_name.strip()
                st.session_state["target_price"] = int(landing_target_price)
                st.session_state["goal_product"] = landing_target_name.strip()
                st.session_state["goal_price"] = int(landing_target_price)
                st.session_state["page"] = "check"
                st.rerun()
        with btn_col2:
            if st.button("목표 없이 구독 점검 시작하기", type="secondary", use_container_width=True):
                st.session_state["target_name"] = ""
                st.session_state["target_price"] = 0
                st.session_state["page"] = "check"
                st.rerun()

else:

    # ============================================================
    # 구독 점검 페이지
    # ============================================================

    # ── 처음으로 돌아가기 ──
    if st.button("← 처음으로 돌아가기"):
        st.session_state["page"] = "landing"
        st.rerun()

    # ── 헤더 ──
    st.markdown(
        '💳 <span class="brand-name" style="font-size:2rem;font-weight:800;">모아Sub</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "자동결제 시대에 흩어진 구독 지출을 한눈에 확인하고, "
        "유지·점검·해지 검토 여부를 스스로 선택할 수 있도록 돕는 구독 소비 인식 지원 서비스입니다."
    )

    # ── 탭 ──
    tab_input, tab_result = st.tabs(["구독 입력", "점검 결과"])

    # ==========================================================
    # TAB 1: 구독 입력
    # ==========================================================
    with tab_input:

        # ── 페르소나 불러오기 ──
        st.subheader("예시 페르소나 불러오기")
        st.caption("시연을 위해 대표 사용자 유형을 불러올 수 있습니다. 각 페르소나는 구독 소비 문제 상황을 보여주기 위한 예시입니다.")

        persona_options = ["선택 안 함"] + [p["name"] for p in PERSONAS]
        selected_name = st.selectbox("페르소나 선택", persona_options, key="persona_select")

        if selected_name != "선택 안 함":
            idx = persona_options.index(selected_name) - 1
            persona = PERSONAS[idx]
            st.info(f"{persona['description']}")
            if st.button("이 페르소나로 불러오기", type="primary"):
                st.session_state.subscriptions = build_persona_subscriptions(persona)
                st.session_state.analysis_result = None
                st.rerun()

        st.divider()

        # ── 직접 입력 ──
        st.subheader("구독 서비스 직접 입력")

        with st.form("subscription_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                service_name = st.text_input("서비스명 *", placeholder="예: 넷플릭스")
                category = st.selectbox("카테고리 *", ["OTT", "음악", "쇼핑", "클라우드", "교육", "생산성", "AI/LLM", "AI 생산성", "AI 콘텐츠 제작", "기타"])
                billing_cycle = st.selectbox("결제 주기 *", ["월별", "연간"])
                fee_input = st.number_input(
                    "결제금액 (원) *",
                    min_value=0, value=0, step=100,
                    help="월별: 월 결제금액 입력 / 연간: 연간 총액 입력 (월 환산 자동 계산)",
                )
            with col_b:
                usage_label = st.selectbox("최근 한 달 사용 빈도 *", list(USAGE_RANGES.keys()))
                usage_count = USAGE_RANGES[usage_label]
                satisfaction = st.slider("만족도 *", min_value=1, max_value=5, value=3)
                billing_date = st.date_input(
                    "다음 결제일 *",
                    value=date.today() + timedelta(days=7),
                    min_value=date.today(),
                )
            if st.form_submit_button("구독 추가", use_container_width=True):
                if not service_name.strip():
                    st.error("서비스명을 입력해주세요.")
                else:
                    monthly_fee = int(fee_input) // 12 if billing_cycle == "연간" else int(fee_input)
                    st.session_state.subscriptions.append({
                        "service_name": service_name.strip(),
                        "category": category,
                        "monthly_fee": monthly_fee,
                        "billing_cycle": billing_cycle,
                        "usage_count": int(usage_count),
                        "satisfaction": int(satisfaction),
                        "billing_date": billing_date.strftime("%Y-%m-%d"),
                    })
                    st.session_state.analysis_result = None
                    st.success(f"**{service_name}** 추가됨!")

        st.divider()

        # ── 현재 구독 목록 ──
        if st.session_state.subscriptions:
            st.subheader(f"현재 구독 목록 ({len(st.session_state.subscriptions)}개)")

            cols = st.columns([3, 2, 2, 4, 2, 1])
            for col, label in zip(cols, ["서비스명", "카테고리", "결제금액", "사용 빈도", "만족도", "삭제"]):
                col.markdown(f"**{label}**")
            st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

            for i, sub in enumerate(st.session_state.subscriptions):
                cols = st.columns([3, 2, 2, 4, 2, 1])
                cols[0].write(f"**{sub['service_name']}**")
                cols[1].write(sub["category"])
                cycle = sub.get("billing_cycle", "월별")
                if cycle == "연간":
                    cols[2].write(f"{sub['monthly_fee'] * 12:,}원/년")
                else:
                    cols[2].write(f"{sub['monthly_fee']:,}원/월")
                cols[3].write(USAGE_LABELS.get(sub["usage_count"], f"{sub['usage_count']}회"))
                cols[4].write("★" * sub["satisfaction"] + "☆" * (5 - sub["satisfaction"]))
                if cols[5].button("삭제", key=f"del_{i}"):
                    st.session_state.subscriptions.pop(i)
                    st.session_state.analysis_result = None
                    st.rerun()

            total = sum(s["monthly_fee"] for s in st.session_state.subscriptions)
            st.info(f"총 월 지출: **{total:,}원** / 연간 **{total * 12:,}원**")

            if st.button("전체 초기화", type="secondary"):
                st.session_state.subscriptions = []
                st.session_state.analysis_result = None
                st.rerun()
        else:
            st.info("페르소나를 선택하거나 구독 서비스를 직접 추가해주세요.")

        st.divider()

        # ── 점검 실행 ──
        if st.button(
            "구독 점검하기",
            type="primary",
            use_container_width=True,
            disabled=len(st.session_state.subscriptions) == 0,
        ):
            payload = {"subscriptions": st.session_state.subscriptions}
            if int(st.session_state.get("goal_price", 0)) > 0:
                payload["goal"] = {
                    "product_name": st.session_state.get("goal_product", ""),
                    "target_price": int(st.session_state.get("goal_price", 0)),
                }
            with st.spinner("점검 기준 분석 중..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/analyze", json=payload, timeout=30)
                    if resp.status_code == 200:
                        st.session_state.analysis_result = resp.json()
                        st.session_state.switch_to_result = True
                        st.rerun()
                    else:
                        st.error(f"점검 오류 ({resp.status_code}): {resp.text}")
                except requests.exceptions.ConnectionError:
                    st.error(
                        "백엔드에 연결할 수 없습니다.  \n"
                        "`python -m uvicorn backend.main:app --reload --port 8000` 을 먼저 실행해주세요."
                    )
                except Exception as e:
                    st.error(f"오류: {e}")

    # ==========================================================
    # TAB 2: 점검 결과
    # ==========================================================
    with tab_result:

        if not st.session_state.analysis_result:
            st.info("구독 입력 탭에서 구독 서비스를 추가한 뒤 '구독 점검하기' 버튼을 눌러주세요.")
        else:
            data = st.session_state.analysis_result
            summary = data.get("summary", {})
            goal_sim = data.get("goal_simulation")
            results = data.get("results", [])
            dup = summary.get("duplicate_categories", [])

            status_counts = {"유지 후보": 0, "점검 후보": 0, "해지 검토 후보": 0}
            for r in results:
                status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

            _order = {"해지 검토 후보": 0, "점검 후보": 1, "유지 후보": 2}
            sorted_results = sorted(results, key=lambda r: (_order.get(r["status"], 3), -r.get("check_score", 0)))
            _USD_CATS = {"AI/LLM", "AI 생산성", "AI 콘텐츠 제작"}
            _sub_map = {s["service_name"]: s for s in st.session_state.subscriptions}

            # ── 목표 소비 시뮬레이션 + 상태 도넛 ───────────────────────
            _gs_left, _gs_right = st.columns([5, 3])

            with _gs_left:
                if goal_sim:
                    g1, g2, g3 = st.columns(3)
                    g1.metric(
                        "목표 상품",
                        goal_sim.get("product_name") or "-",
                        f"목표 금액: {goal_sim.get('target_price', 0):,}원",
                    )
                    g2.metric(
                        "월 예상 절감액",
                        f"{goal_sim.get('selected_monthly_saving', 0):,}원",
                        f"하루 추가 절감: {goal_sim.get('daily_extra_saving', 0):,}원",
                    )
                    g3.metric(
                        "목표 달성 속도",
                        f"약 {goal_sim.get('speed_up_ratio', 0):.1f}% 빠름",
                        "하루 1만 원 저축 기준 대비",
                    )
                    _svc_sim = goal_sim.get("simulation_services", [])
                    if _svc_sim:
                        st.caption(
                            f"시뮬레이션 기준 구독: **{', '.join(_svc_sim)}** — "
                            f"하루 1만 원 기준 대비 목표 달성 속도가 약 **{goal_sim.get('speed_up_ratio', 0):.1f}%** 빨라집니다."
                        )
                else:
                    _c_monthly = sum(r["monthly_fee"] for r in results if r["status"] == "해지 검토 후보")
                    _r_monthly = sum(r["monthly_fee"] for r in results if r["status"] == "점검 후보")
                    _sv_monthly = _c_monthly + _r_monthly // 2
                    if _sv_monthly > 0:
                        _sv_annual = _sv_monthly * 12
                        def _ql(a):
                            if a >= 600000: return "국내 여행 한 번 또는 취미 장비 구입"
                            if a >= 300000: return "콘서트·공연 관람 또는 자격증 도전"
                            if a >= 150000: return "외식·카페·소소한 취미 활동"
                            return "한 달 커피값 이상의 여유"
                        q1, q2, q3 = st.columns(3)
                        q1.metric("월 잠재 절감액", f"{_sv_monthly:,}원", "해지 검토 후보 기준")
                        q2.metric("연간으로 환산하면", f"{_sv_annual:,}원")
                        q3.metric("이만큼으로", _ql(_sv_annual))
                        st.caption(
                            "목표 상품이 있다면 랜딩 페이지에서 목표를 설정해 달성 속도를 확인해보세요. "
                            "점검 결과는 사용자가 입력한 월 결제금액을 기준으로 계산됩니다."
                        )

            with _gs_right:
                st.markdown("**상태별 구독 현황**")
                _status_df_top = pd.DataFrame([
                    {"상태": k, "개수": v}
                    for k, v in status_counts.items() if v > 0
                ])
                _donut_top = (
                    alt.Chart(_status_df_top)
                    .mark_arc(innerRadius=0, outerRadius=90)
                    .encode(
                        theta=alt.Theta("개수:Q"),
                        color=alt.Color(
                            "상태:N",
                            scale=alt.Scale(
                                domain=["유지 후보", "점검 후보", "해지 검토 후보"],
                                range=["#10b981", "#f59e0b", "#ef4444"],
                            ),
                            legend=alt.Legend(title="상태", orient="right"),
                        ),
                        tooltip=["상태", "개수"],
                    )
                    .properties(height=200)
                )
                st.altair_chart(_donut_top, use_container_width=True)

            st.divider()

            r_tab1, r_tab2, r_tab3, r_tab4 = st.tabs([
                "대시보드", "우선 점검 대상", "전체 구독 목록", "상세 설명"
            ])

            # ── 1. 대시보드 ──────────────────────────────────────────
            with r_tab1:
                # 핵심 지표
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("총 월 지출", f"{summary.get('total_monthly_fee', 0):,}원")
                c2.metric("총 연간 지출", f"{summary.get('total_annual_fee', 0):,}원")
                c3.metric("구독 수", f"{summary.get('subscription_count', 0)}개")
                c4.metric("중복 카테고리", ", ".join(dup) if dup else "없음")

                s1, s2, s3 = st.columns(3)
                s1.metric("유지 후보", f"{status_counts['유지 후보']}개")
                s2.metric("점검 후보", f"{status_counts['점검 후보']}개")
                s3.metric("해지 검토 후보", f"{status_counts['해지 검토 후보']}개")

                if dup:
                    st.warning(f"같은 카테고리에 여러 구독이 있습니다: **{', '.join(dup)}** — 실제 이용 빈도를 비교해보세요.")

                st.divider()

                # ── 차트 행 1: 카테고리 막대 + 구독별 막대 (2열) ──
                ch1, ch2 = st.columns(2)

                with ch1:
                    st.markdown("**카테고리별 월 지출**")
                    _cat_df = (
                        pd.DataFrame([{"카테고리": r["category"], "월 요금": r["monthly_fee"]} for r in results])
                        .groupby("카테고리", as_index=False)["월 요금"].sum()
                        .sort_values("월 요금", ascending=False)
                    )
                    _cat_chart = (
                        alt.Chart(_cat_df)
                        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                        .encode(
                            x=alt.X("월 요금:Q", title="원", axis=alt.Axis(format=",.0f", tickCount=5)),
                            y=alt.Y("카테고리:N", sort="-x", title=""),
                            color=alt.value("#3B82F6"),
                            tooltip=["카테고리", alt.Tooltip("월 요금:Q", format=",.0f", title="월 요금(원)")],
                        )
                        .properties(height=max(200, len(_cat_df) * 36))
                    )
                    st.altair_chart(_cat_chart, use_container_width=True)

                with ch2:
                    st.markdown("**구독별 월 요금 비교**")
                    _svc_df = pd.DataFrame([
                        {"서비스명": r["service_name"], "월 요금": r["monthly_fee"], "상태": r["status"]}
                        for r in results
                    ]).sort_values("월 요금", ascending=False)
                    _svc_chart = (
                        alt.Chart(_svc_df)
                        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                        .encode(
                            x=alt.X("월 요금:Q", title="원", axis=alt.Axis(format=",.0f", tickCount=5)),
                            y=alt.Y("서비스명:N", sort="-x", title=""),
                            color=alt.Color(
                                "상태:N",
                                scale=alt.Scale(
                                    domain=["유지 후보", "점검 후보", "해지 검토 후보"],
                                    range=["#10b981", "#f59e0b", "#ef4444"],
                                ),
                                legend=alt.Legend(title="상태"),
                            ),
                            tooltip=["서비스명", "상태", alt.Tooltip("월 요금:Q", format=",.0f", title="월 요금(원)")],
                        )
                        .properties(height=max(200, len(_svc_df) * 34))
                    )
                    st.altair_chart(_svc_chart, use_container_width=True)

                st.divider()

                # 우선 확인할 항목
                st.subheader("우선 확인할 항목")
                _priority_preview = [r for r in sorted_results if r["status"] in ("점검 후보", "해지 검토 후보")][:3]
                if _priority_preview:
                    for _item in _priority_preview:
                        _st = _item["status"]
                        _bd = {"점검 후보": "#f59e0b", "해지 검토 후보": "#ef4444"}.get(_st, "#94a3b8")
                        st.markdown(
                            f"<div style='border-left:4px solid {_bd};padding:10px 16px;"
                            f"background:#f8fafc;border-radius:0 8px 8px 0;margin-bottom:6px;'>",
                            unsafe_allow_html=True,
                        )
                        _pa, _pb, _pc, _pd, _pe = st.columns([3, 2, 2, 2, 1])
                        _pa.markdown(
                            f"**{_item['service_name']}** &nbsp;"
                            f"<small style='color:#64748b;'>{_item['category']}</small>",
                            unsafe_allow_html=True,
                        )
                        _pb.markdown(status_badge(_st), unsafe_allow_html=True)
                        _pc.markdown(f"월 **{_item['monthly_fee']:,}원**")
                        _pd.markdown(f"다음 결제 **D-{_item['days_until_billing']}**")
                        if _pe.button("상세 →", key=f"goto_detail_{_item['service_name']}"):
                            st.session_state["detail_service"] = _item["service_name"]
                            st.session_state["switch_to_detail"] = True
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    if len([r for r in sorted_results if r["status"] in ("점검 후보", "해지 검토 후보")]) > 3:
                        st.caption("더 많은 항목은 '우선 점검 대상' 탭에서 확인하세요.")
                else:
                    st.info("현재 우선 점검 대상은 없습니다. 다만 중복 카테고리나 결제일이 가까운 구독은 확인해볼 수 있습니다.")

                with st.expander("원본 응답 JSON (개발자용)", expanded=False):
                    st.json(data)

            # ── 2. 우선 점검 대상 ────────────────────────────────────
            with r_tab2:
                _priority_all = [r for r in sorted_results if r["status"] in ("점검 후보", "해지 검토 후보")]
                if not _priority_all:
                    st.success("현재 점검 후보 또는 해지 검토 후보 구독이 없습니다.")
                else:
                    for item in _priority_all:
                        status = item["status"]
                        border = {"점검 후보": "#f59e0b", "해지 검토 후보": "#ef4444"}.get(status, "#94a3b8")

                        st.markdown(
                            f"<div style='border-left:4px solid {border};padding:12px 16px;"
                            f"background:#f8fafc;border-radius:0 8px 8px 0;margin-bottom:8px'>",
                            unsafe_allow_html=True,
                        )
                        h1, h2 = st.columns([6, 2])
                        h1.markdown(
                            f"### {item['service_name']} "
                            f"<small style='color:#64748b'>{item['category']}</small>",
                            unsafe_allow_html=True,
                        )
                        h2.markdown(status_badge(status), unsafe_allow_html=True)

                        p1, p2, p3 = st.columns(3)
                        p1.metric("월 요금", f"{item['monthly_fee']:,}원")
                        p2.metric("다음 결제", f"D-{item['days_until_billing']}")
                        p3.metric("카테고리", item["category"])

                        if item.get("category") in _USD_CATS:
                            st.caption("💱 해외 구독 서비스는 환율과 카드사 수수료에 따라 실제 원화 청구액이 달라질 수 있습니다. 점검 결과는 사용자가 입력한 월 결제금액을 기준으로 계산됩니다.")

                        if item.get("rule_reasons"):
                            st.markdown(
                                " ".join(
                                    f"<span style='background:#f1f5f9;border:1px solid #cbd5e1;"
                                    f"border-radius:6px;padding:2px 8px;font-size:0.8rem;"
                                    f"color:#475569;margin-right:4px;'>{reason}</span>"
                                    for reason in item["rule_reasons"]
                                ),
                                unsafe_allow_html=True,
                            )
                            st.markdown("")

                        if item.get("rag_explanation"):
                            with st.expander("판단을 돕는 참고 정보", expanded=False):
                                st.markdown(f"> {item['rag_explanation']}")
                                rc1, rc2 = st.columns(2)
                                with rc1:
                                    if item.get("alternatives"):
                                        st.markdown("**비교해볼 서비스**")
                                        st.markdown(" · ".join(item["alternatives"]))
                                    if item.get("cancel_path"):
                                        st.markdown("**해지 경로**")
                                        st.markdown(f"`{item['cancel_path']}`")
                                with rc2:
                                    if item.get("cautions"):
                                        st.markdown("**확인해볼 사항**")
                                        for c in item["cautions"]:
                                            st.markdown(f"- {c}")

                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("")

            # ── 3. 전체 구독 목록 ────────────────────────────────────
            with r_tab3:
                _table_rows = []
                for item in sorted_results:
                    _sub = _sub_map.get(item["service_name"], {})
                    _usage = _sub.get("usage_count", item.get("usage_count"))
                    _sat = _sub.get("satisfaction", item.get("satisfaction"))
                    _usage_label = USAGE_LABELS.get(_usage, f"{_usage}회") if isinstance(_usage, int) else "-"
                    _sat_label = ("★" * _sat + "☆" * (5 - _sat)) if isinstance(_sat, int) else "-"
                    _table_rows.append({
                        "서비스명": item["service_name"],
                        "카테고리": item["category"],
                        "월 요금": f"{item['monthly_fee']:,}원",
                        "연간 비용": f"{item['annual_fee']:,}원",
                        "사용 빈도": _usage_label,
                        "만족도": _sat_label,
                        "다음 결제": f"D-{item['days_until_billing']}",
                        "상태": item["status"],
                    })
                st.dataframe(
                    pd.DataFrame(_table_rows),
                    use_container_width=True,
                    hide_index=True,
                    height=min(600, 56 + len(_table_rows) * 35),
                    column_config={
                        "서비스명":  st.column_config.TextColumn("서비스명",  width="medium"),
                        "카테고리":  st.column_config.TextColumn("카테고리",  width="small"),
                        "월 요금":   st.column_config.TextColumn("월 요금",   width="small"),
                        "연간 비용": st.column_config.TextColumn("연간 비용", width="small"),
                        "사용 빈도": st.column_config.TextColumn("사용 빈도", width="medium"),
                        "만족도":    st.column_config.TextColumn("만족도",    width="small"),
                        "다음 결제": st.column_config.TextColumn("다음 결제", width="small"),
                        "상태":      st.column_config.TextColumn("상태",      width="medium"),
                    },
                )

            # ── 4. 상세 설명 ─────────────────────────────────────────
            with r_tab4:
                _focused = st.session_state.get("detail_service", "")
                # 포커스 항목을 최상단으로 재정렬
                _detail_order = sorted(
                    sorted_results,
                    key=lambda r: (0 if r["service_name"] == _focused else 1, _order.get(r["status"], 3))
                )
                for item in _detail_order:
                    status = item["status"]
                    _is_focused = item["service_name"] == _focused
                    border = {"유지 후보": "#10b981", "점검 후보": "#f59e0b", "해지 검토 후보": "#ef4444"}.get(status, "#94a3b8")
                    _bg = "#fffbeb" if _is_focused else "#f8fafc"

                    st.markdown(
                        f"<div style='border-left:4px solid {border};padding:12px 16px;"
                        f"background:{_bg};border-radius:0 8px 8px 0;margin-bottom:8px;"
                        f"{'box-shadow:0 0 0 2px #f59e0b33;' if _is_focused else ''}'>",
                        unsafe_allow_html=True,
                    )
                    h1, h2 = st.columns([6, 2])
                    h1.markdown(
                        f"### {item['service_name']} "
                        f"<small style='color:#64748b'>{item['category']}</small>",
                        unsafe_allow_html=True,
                    )
                    h2.markdown(status_badge(status), unsafe_allow_html=True)

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("월 요금", f"{item['monthly_fee']:,}원")
                    m2.metric("연간 비용", f"{item['annual_fee']:,}원")
                    m3.metric("다음 결제", f"D-{item['days_until_billing']}")
                    m4.metric("카테고리", item["category"])

                    if item.get("category") in _USD_CATS:
                        st.caption("💱 해외 구독 서비스는 환율과 카드사 수수료에 따라 실제 원화 청구액이 달라질 수 있습니다. 점검 결과는 사용자가 입력한 월 결제금액을 기준으로 계산됩니다.")

                    with st.expander("점검 기준 분석", expanded=(_is_focused or status != "유지 후보")):
                        sc, rc = st.columns([1, 2])
                        with sc:
                            score = item.get("check_score", 0)
                            priority = item.get("priority_level", "")
                            st.markdown("**점검 점수**")
                            st.markdown(
                                f"<span class='score-badge'>{score}점</span>&nbsp;"
                                f"{priority_badge(priority)}",
                                unsafe_allow_html=True,
                            )
                            st.markdown("")
                            st.caption("유지 후보: 0-2점  |  점검 후보: 3-5점  |  해지 검토 후보: 6점 이상")
                        with rc:
                            st.markdown("**점검 기준 항목**")
                            for reason in item.get("rule_reasons", []):
                                st.markdown(f"- {reason}")

                    if status in ("점검 후보", "해지 검토 후보") and item.get("rag_explanation"):
                        with st.expander("판단을 돕는 참고 정보", expanded=True):
                            st.markdown(f"> {item['rag_explanation']}")
                            rc1, rc2 = st.columns(2)
                            with rc1:
                                if item.get("alternatives"):
                                    st.markdown("**비교해볼 서비스**")
                                    st.markdown(" · ".join(item["alternatives"]))
                                if item.get("cancel_path"):
                                    st.markdown("**해지 경로**")
                                    st.markdown(f"`{item['cancel_path']}`")
                            with rc2:
                                if item.get("cautions"):
                                    st.markdown("**확인해볼 사항**")
                                    for c in item["cautions"]:
                                        st.markdown(f"- {c}")

                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("")


# ===== 푸터 =====
st.divider()
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:0.8rem'>"
    "모아Sub · HUSS 퓨처아고라 해커톤 MVP · 구독 소비 인식 지원 서비스 · 이 서비스는 해지를 강요하지 않습니다."
    "</div>",
    unsafe_allow_html=True,
)
