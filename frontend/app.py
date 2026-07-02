"""
모아Sub - Streamlit 프론트엔드
랜딩페이지 → 구독 점검 → 분석 결과
"""

from datetime import date, timedelta

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

# ===== 탭 자동 전환 (분석 완료 직후) =====
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

# ===== CSS =====
st.markdown("""
<style>
.status-maintain { background:#d1fae5; color:#065f46; padding:4px 12px; border-radius:12px; font-weight:600; }
.status-review   { background:#fef3c7; color:#92400e; padding:4px 12px; border-radius:12px; font-weight:600; }
.status-cancel   { background:#fee2e2; color:#991b1b; padding:4px 12px; border-radius:12px; font-weight:600; }
.score-badge     { background:#e2e8f0; color:#1e293b; padding:3px 10px; border-radius:8px; font-size:0.9rem; font-weight:600; }
.priority-low    { background:#d1fae5; color:#065f46; padding:3px 10px; border-radius:8px; font-size:0.85rem; }
.priority-mid    { background:#fef3c7; color:#92400e; padding:3px 10px; border-radius:8px; font-size:0.85rem; }
.priority-high   { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:8px; font-size:0.85rem; }
</style>
<style>
/* selectbox 타이핑 비활성화 */
div[data-baseweb="select"] input {
    pointer-events: none !important;
    caret-color: transparent !important;
}
/* 랜딩 입력 카드 내부 위젯 상단 여백 제거 */
.landing-input-card > div { padding-top: 0 !important; }
/* 랜딩 버튼 row 상단 간격 */
div[data-testid="stHorizontalBlock"] + div[data-testid="stHorizontalBlock"] {
    margin-top: 4px;
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
        "name": "대학생 A — OTT 중복형",
        "description": "OTT를 여러 개 구독하고 있지만 실제 사용 빈도는 일부 서비스에 몰려 있음",
        "goal_product": "무선 이어폰",
        "goal_price": 250000,
        "subscriptions": [
            {"service_name": "넷플릭스",       "category": "OTT",  "monthly_fee": 17000, "usage_count": 18, "satisfaction": 5},
            {"service_name": "티빙",            "category": "OTT",  "monthly_fee": 13900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "디즈니플러스",    "category": "OTT",  "monthly_fee":  9900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "유튜브 프리미엄", "category": "음악", "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "쿠팡와우",        "category": "쇼핑", "monthly_fee":  7890, "usage_count":  8, "satisfaction": 4},
        ],
    },
    {
        "name": "대학생 B — 클라우드/생산성 유지형",
        "description": "사용 빈도는 낮지만 클라우드와 생산성 도구에 의존하고 있음",
        "goal_product": "태블릿",
        "goal_price": 600000,
        "subscriptions": [
            {"service_name": "iCloud",     "category": "클라우드", "monthly_fee":  3300, "usage_count":  2, "satisfaction": 5},
            {"service_name": "Google One", "category": "클라우드", "monthly_fee":  2400, "usage_count":  2, "satisfaction": 4},
            {"service_name": "Notion AI",  "category": "생산성",   "monthly_fee": 12000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "스포티파이", "category": "음악",     "monthly_fee": 10900, "usage_count": 18, "satisfaction": 5},
        ],
    },
    {
        "name": "사회초년생 C — 소액 구독 누적형",
        "description": "개별 구독료는 작다고 생각했지만 여러 개가 누적되어 월 지출이 커진 상태",
        "goal_product": "여행 경비",
        "goal_price": 500000,
        "subscriptions": [
            {"service_name": "쿠팡와우",           "category": "쇼핑", "monthly_fee":  7890, "usage_count": 18, "satisfaction": 4},
            {"service_name": "네이버플러스 멤버십", "category": "쇼핑", "monthly_fee":  4900, "usage_count":  2, "satisfaction": 3},
            {"service_name": "멜론",               "category": "음악", "monthly_fee":  7900, "usage_count":  2, "satisfaction": 3},
            {"service_name": "티빙",               "category": "OTT",  "monthly_fee": 13900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "웨이브",             "category": "OTT",  "monthly_fee": 10900, "usage_count":  2, "satisfaction": 2},
        ],
    },
    {
        "name": "직장인 D — 무료체험 후 자동결제 방치형",
        "description": "무료체험으로 시작한 서비스를 해지하지 못해 자동결제가 이어지고 있음",
        "goal_product": "스마트워치",
        "goal_price": 350000,
        "subscriptions": [
            {"service_name": "디즈니플러스",    "category": "OTT",  "monthly_fee":  9900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "웨이브",          "category": "OTT",  "monthly_fee": 10900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "밀리의서재",      "category": "교육", "monthly_fee":  9900, "usage_count":  0, "satisfaction": 2},
            {"service_name": "유튜브 프리미엄", "category": "음악", "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "쿠팡와우",        "category": "쇼핑", "monthly_fee":  7890, "usage_count":  8, "satisfaction": 4},
        ],
    },
    {
        "name": "대학생 E — 음악/콘텐츠 고만족 유지형",
        "description": "구독 개수는 많지 않지만 자주 쓰는 음악과 콘텐츠 서비스 만족도가 높음",
        "goal_product": "콘서트 티켓",
        "goal_price": 180000,
        "subscriptions": [
            {"service_name": "유튜브 프리미엄", "category": "음악",     "monthly_fee": 14900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "스포티파이",      "category": "음악",     "monthly_fee": 10900, "usage_count": 18, "satisfaction": 5},
            {"service_name": "넷플릭스",        "category": "OTT",      "monthly_fee": 17000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "iCloud",          "category": "클라우드", "monthly_fee":  3300, "usage_count":  2, "satisfaction": 4},
        ],
    },
    {
        "name": "취업준비생 F — 학습 구독 미사용형",
        "description": "자기계발을 위해 교육 구독을 여러 개 신청했지만 실제 사용 빈도는 낮은 상태",
        "goal_product": "자격증 응시료",
        "goal_price": 200000,
        "subscriptions": [
            {"service_name": "클래스101",           "category": "교육", "monthly_fee": 19900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "패스트캠퍼스",        "category": "교육", "monthly_fee": 29000, "usage_count":  2, "satisfaction": 3},
            {"service_name": "밀리의서재",          "category": "교육", "monthly_fee":  9900, "usage_count":  2, "satisfaction": 2},
            {"service_name": "Notion AI",           "category": "생산성","monthly_fee": 12000, "usage_count":  8, "satisfaction": 4},
            {"service_name": "네이버플러스 멤버십", "category": "쇼핑", "monthly_fee":  4900, "usage_count":  2, "satisfaction": 3},
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

    # ── 히어로 블록 ──
    st.markdown("""
<div style="
    background: linear-gradient(135deg, #1e3a8a 0%, #4338ca 100%);
    border-radius: 20px;
    padding: 52px 48px 44px 48px;
    color: white;
    margin-bottom: 28px;
">
    <div style="
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        opacity: 0.6;
        text-transform: uppercase;
        margin-bottom: 20px;
    ">
        💳 &nbsp;모아Sub
    </div>
    <div style="
        font-size: 2.15rem;
        font-weight: 800;
        line-height: 1.4;
        margin-bottom: 22px;
    ">
        사고 싶은 목표를 정하고,<br>
        자동결제로 새어나가는<br>
        구독 지출을 점검해보세요.
    </div>
    <div style="
        font-size: 0.97rem;
        line-height: 1.8;
        opacity: 0.82;
        max-width: 600px;
    ">
        모아Sub은 반복되는 구독 지출을 한눈에 확인하고,<br>
        사용 빈도·만족도·결제일·카테고리 중복 여부를 바탕으로<br>
        구독 상태를 점검할 수 있도록 돕는 서비스입니다.
    </div>
</div>
""", unsafe_allow_html=True)

    # ── 목표 소비 입력 카드 ──
    st.markdown("""
<div style="
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 28px 28px 8px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 6px 20px rgba(0,0,0,0.04);
    margin-bottom: 8px;
">
<p style="font-size:1.05rem;font-weight:700;color:#1e293b;margin:0 0 6px 0">
    목표 소비 설정
</p>
<p style="font-size:0.875rem;color:#64748b;line-height:1.65;margin:0 0 16px 0">
    사고 싶은 항목과 목표 금액을 입력하면, 점검 결과 화면에서 반복 지출을 줄였을 때
    목표 달성 속도가 어떻게 달라지는지 확인할 수 있습니다.
</p>
""", unsafe_allow_html=True)

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

    st.markdown("</div>", unsafe_allow_html=True)

    # ── 시작 버튼 ──
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("목표 설정하고 구독 점검 시작하기", type="primary", use_container_width=True):
            st.session_state["target_name"] = landing_target_name.strip()
            st.session_state["target_price"] = int(landing_target_price)
            # 구독 점검 페이지의 목표 소비 입력창에 기본값으로 연결
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
    st.title("💳 모아Sub")
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
                category = st.selectbox("카테고리 *", ["OTT", "음악", "쇼핑", "클라우드", "교육", "생산성", "기타"])
                monthly_fee = st.number_input("월 결제금액 (원) *", min_value=0, value=0, step=100)
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
                    st.session_state.subscriptions.append({
                        "service_name": service_name.strip(),
                        "category": category,
                        "monthly_fee": int(monthly_fee),
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
            for col, label in zip(cols, ["서비스명", "카테고리", "월 요금", "사용 빈도", "만족도", "삭제"]):
                col.markdown(f"**{label}**")
            st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

            for i, sub in enumerate(st.session_state.subscriptions):
                cols = st.columns([3, 2, 2, 4, 2, 1])
                cols[0].write(f"**{sub['service_name']}**")
                cols[1].write(sub["category"])
                cols[2].write(f"{sub['monthly_fee']:,}원")
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

        # ── 목표 소비 입력 ──
        st.subheader("목표 소비 선택 시뮬레이션 (선택)")
        st.caption("목표 상품을 입력하면 구독 점검 시 저축 속도 변화를 보여줍니다. 비워도 점검은 정상 작동합니다.")

        g1, g2 = st.columns(2)
        with g1:
            goal_product = st.text_input("목표 상품명", placeholder="예: 에어팟", key="goal_product")
        with g2:
            goal_price_init = st.session_state.get("goal_price", 0)
            if not isinstance(goal_price_init, (int, float)):
                goal_price_init = 0
            goal_price = st.number_input("목표 금액 (원)", min_value=0, value=int(goal_price_init), step=1000, key="goal_price")

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

            # 전체 요약
            st.subheader("전체 요약")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 월 지출", f"{summary.get('total_monthly_fee', 0):,}원")
            c2.metric("총 연간 지출", f"{summary.get('total_annual_fee', 0):,}원")
            c3.metric("구독 수", f"{summary.get('subscription_count', 0)}개")
            dup = summary.get("duplicate_categories", [])
            c4.metric("중복 카테고리", ", ".join(dup) if dup else "없음")

            if dup:
                st.warning(f"같은 카테고리에 여러 구독이 있습니다: **{', '.join(dup)}**  —  실제 이용 빈도를 비교해보세요.")

            status_counts = {"유지 후보": 0, "점검 후보": 0, "해지 검토 후보": 0}
            for r in results:
                status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
            s1, s2, s3 = st.columns(3)
            s1.metric("유지 후보", f"{status_counts['유지 후보']}개")
            s2.metric("점검 후보", f"{status_counts['점검 후보']}개")
            s3.metric("해지 검토 후보", f"{status_counts['해지 검토 후보']}개")

            # 목표 소비 시뮬레이션
            if goal_sim:
                st.divider()
                st.subheader("목표 소비 선택 시뮬레이션")
                st.caption("이 구독을 점검 대상으로 선택한다고 가정했을 때의 저축 속도 변화입니다. 판단을 돕는 참고 정보입니다.")
                g1, g2, g3 = st.columns(3)
                g1.metric("목표 상품", goal_sim.get("product_name") or "-", f"목표 금액: {goal_sim.get('target_price', 0):,}원")
                g2.metric("월 예상 절감액", f"{goal_sim.get('selected_monthly_saving', 0):,}원", f"하루 추가 절감: {goal_sim.get('daily_extra_saving', 0):,}원")
                g3.metric("목표 달성 속도", f"약 {goal_sim.get('speed_up_ratio', 0):.1f}% 빠름", "하루 1만 원 저축 기준 대비")
                svc = goal_sim.get("simulation_services", [])
                if svc:
                    st.markdown(
                        f"> 시뮬레이션 기준 구독: **{', '.join(svc)}**  \n"
                        f"> 하루 1만 원 기준 대비 목표 달성 속도가 약 **{goal_sim.get('speed_up_ratio', 0):.1f}%** 빨라집니다."
                    )

            # 구독별 결과
            st.divider()
            st.subheader("구독별 점검 결과")

            order = {"해지 검토 후보": 0, "점검 후보": 1, "유지 후보": 2}
            for item in sorted(results, key=lambda r: (order.get(r["status"], 3), -r.get("check_score", 0))):
                status = item["status"]
                border = {"유지 후보": "#10b981", "점검 후보": "#f59e0b", "해지 검토 후보": "#ef4444"}.get(status, "#94a3b8")

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

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("월 요금", f"{item['monthly_fee']:,}원")
                m2.metric("연간 비용", f"{item['annual_fee']:,}원")
                m3.metric("결제까지", f"{item['days_until_billing']}일")
                m4.metric("카테고리", item["category"])

                with st.expander("점검 기준 분석", expanded=(status != "유지 후보")):
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

            with st.expander("원본 응답 JSON (개발자용)", expanded=False):
                st.json(data)

# ===== 푸터 =====
st.divider()
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:0.8rem'>"
    "모아Sub · HUSS 퓨처아고라 해커톤 MVP · 구독 소비 인식 지원 서비스 · 이 서비스는 해지를 강요하지 않습니다."
    "</div>",
    unsafe_allow_html=True,
)
