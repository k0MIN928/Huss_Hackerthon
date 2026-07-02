import re

# ===== 구독 서비스 마스터 데이터 (31개) =====
#
# [monthly_fee 필드 안내]
# - KRW 결제 서비스: 원화 금액 문자열 (규칙 엔진과 무관, 참고용)
# - USD 결제 서비스: None — 실제 원화 청구액은 사용자 직접 입력값 기준
#   (환율·카드사 수수료·세금에 따라 달라지므로 DB에 추정치를 기재하지 않음)
#   대신 monthly_fee_usd / pricing_note 필드 참고
#
# [규칙 엔진 계산 기준]
# rule_engine.py는 DB의 monthly_fee가 아니라
# 사용자가 직접 입력한 monthly_fee(정수)를 기준으로 계산합니다.

SUBSCRIPTION_DB = {
    # ===== 기존 서비스 (KRW 결제) =====
    "네이버플러스 멤버십": {
        "category": "Shopping, OTT",
        "monthly_fee": "4,900원",
        "price_currency": "KRW",
        "plan_info": "일반 요금제",
        "cheaper_plan": "연간 멤버십 이용 시 할인 (월 3900원)",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 46800원)",
        "alternative_services": ["쿠팡 와우 멤버십", "컬리멤버스"],
        "cancel_path": "네이버플러스 멤버십 MY → 설정 → 네이버플러스 멤버십 해지",
        "caution": ["남은 기간 유지 여부", "적립된 포인트 회수 조건 확인"],
        "document": "네이버플러스 멤버십은 Shopping 및 OTT 카테고리에 속하는 구독 서비스이다. 쿠팡 와우 멤버십이나 컬리멤버스와 같은 쇼핑 결합 서비스들과 대체 관계에 있으므로 중복 구독 여부를 점검할 필요가 있다. 월 요금은 4,900원이며 연간 멤버십을 이용할 경우 월 3,900원 꼴로 절감하여 이용할 수 있다. 해지하려는 경우 네이버플러스 멤버십 MY의 설정 메뉴에서 멤버십 해지를 진행할 수 있으며, 해지 전에는 남은 기간 유지 조건과 그동안 적립된 네이버페이 포인트의 회수 조건이 있는지 반드시 확인해야 한다.",
        "checked_at": "",
    },
    "icloud": {
        "category": "DRIVE",
        "monthly_fee": "1100, 3300, 11100",
        "price_currency": "KRW",
        "plan_info": "50GB, 200GB, 2TB",
        "cheaper_plan": "무료 5GB 요금제 다운그레이드",
        "ad_plan": "해당 없음",
        "annual_discount": "없음",
        "alternative_services": ["구글 원", "마이크로소프트 365", "드롭박스"],
        "cancel_path": "iPhone 설정 → Apple ID → iCloud → 저장 공간 관리 → 요금제 변경",
        "caution": ["다운그레이드 시 초과된 용량의 데이터 삭제 위험 확인"],
        "document": "iCloud는 Apple의 대표적인 클라우드 스토리지(DRIVE) 구독 서비스이다. 구글 원, 마이크로소프트 365, 드롭박스 등과 같은 대체재가 존재하므로 타 클라우드와 중복 사용 여부를 점검해야 한다. 용량에 따라 월 1,100원부터 11,100원까지 요금제가 나뉘며, 더 낮은 용량이나 무료 5GB 요금제로 다운그레이드가 가능하다. 해지 및 요금제 변경은 iPhone 설정의 Apple ID 메뉴 내 iCloud 저장 공간 관리에서 진행할 수 있다. 이때 용량을 줄이면 초과된 용량만큼의 데이터가 영구 삭제될 위험이 있으므로 백업 상태를 반드시 확인해야 한다.",
        "checked_at": "",
    },
    "넷플릭스": {
        "category": "OTT",
        "monthly_fee": "5500, 13500, 17000",
        "price_currency": "KRW",
        "plan_info": "광고형 스탠다드, 스탠다드, 프리미엄",
        "cheaper_plan": "광고형 스탠다드 요금제 선택",
        "ad_plan": "있음 (광고형 스탠다드)",
        "annual_discount": "없음",
        "alternative_services": ["웨이브", "디즈니+", "티빙"],
        "cancel_path": "계정 → 멤버십 해지",
        "caution": ["해지 후에도 이번 결제 주기가 끝날 때까지 시청 가능"],
        "document": "넷플릭스는 전 세계에서 가장 널리 쓰이는 OTT 구독 서비스이다. 티빙, 웨이브, 디즈니플러스 등 국내외 다양한 OTT 플랫폼들과 카테고리가 겹치므로 여러 OTT를 중복 구독 중이라면 이용 빈도를 점검하는 것이 좋다. 요금제는 광고형 스탠다드(5,500원)부터 프리미엄(17,000원)까지 제공되며, 비용을 아끼려면 광고형 요금제로 전환하는 방법이 있다. 해지는 서비스 내 계정 메뉴에서 멤버십 해지를 선택하면 된다. 해지 신청을 하더라도 이미 결제된 이번 주기의 만료일까지는 추가 요금 없이 정상 시청이 가능하다.",
        "checked_at": "",
    },
    "티빙": {
        "category": "OTT",
        "monthly_fee": "5500, 9500, 13500, 17000",
        "price_currency": "KRW",
        "plan_info": "광고형 요금제, 베이직, 스탠다드, 프리미엄",
        "cheaper_plan": "광고형 요금제 또는 연간 결제 확인",
        "ad_plan": "있음 (광고형 스탠다드)",
        "annual_discount": "있음 (연간 결제 시 약 25% 할인)",
        "alternative_services": ["넷플릭스", "웨이브", "디즈니+"],
        "cancel_path": "마이페이지 → 이용권/결제관리 → 정기결제 해지",
        "caution": ["연간 이용권은 중도 해지 시 환불 규정 까다로움"],
        "document": "티빙은 국내 예능 및 드라마 콘텐츠가 강점인 OTT 구독 서비스이다. 넷플릭스, 웨이브 등 동종 카테고리의 타 서비스들과 동시에 구독 중이라면 실사용량 대비 고정 지출을 점검할 필요가 있다. 광고요금제를 선택하거나 연간 결제를 활용하면 비용을 아낄 수 있다. 해지 경로는 마이페이지의 이용권/결제관리에서 정기결제 해지를 선택하면 된다. 단, 연간 이용권의 경우 중도 해지 시 환불 위약금 및 조건이 까다로우므로 결제 형태를 미리 확인하는 것이 권장된다.",
        "checked_at": "",
    },
    "웨이브": {
        "category": "OTT",
        "monthly_fee": "7900, 10900, 13900",
        "price_currency": "KRW",
        "plan_info": "베이직, 스탠다드, 프리미엄",
        "cheaper_plan": "통신사(SKT) 결합 요금제 확인",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 16% 할인)",
        "alternative_services": ["넷플릭스", "티빙", "디즈니+"],
        "cancel_path": "MY → 이용권 내역 → 자동결제 해지",
        "caution": ["제휴 이용권은 해당 제휴사에서 해지해야 할 수 있음"],
        "document": "웨이브는 지상파 및 다양한 방송 콘텐츠를 제공하는 OTT 구독 서비스이다. 다른 OTT 플랫폼과 중복 결제되고 있지는 않은지 사용 빈도를 기준으로 점검해볼 수 있다. 기본 요금제 외에도 SKT 통신사 결합 요금제나 제휴 할인이 있는지 확인하면 비용을 낮출 수 있다. 해지는 MY 메뉴의 이용권 내역에서 자동결제 해지를 누르면 된다. 만약 통신사나 타 제휴사를 통해 가입한 이용권이라면 웨이브 앱이 아닌 해당 제휴사에서 해지 절차를 밟아야 할 수 있으니 유의해야 한다.",
        "checked_at": "",
    },
    "디즈니+": {
        "category": "OTT",
        "monthly_fee": "9900, 13900",
        "price_currency": "KRW",
        "plan_info": "스탠다드, 프리미엄",
        "cheaper_plan": "연간 결제 할인 확인",
        "ad_plan": "없음 (국내 기준)",
        "annual_discount": "있음 (연간 결제 시 약 16% 할인)",
        "alternative_services": ["넷플릭스", "티빙", "웨이브"],
        "cancel_path": "프로필 → 계정 → 멤버십 → 멤버십 취소",
        "caution": ["결제 주기 만료일까지 서비스 이용 가능"],
        "document": "디즈니플러스는 디즈니, 마블, 픽사 등의 IP를 독점 제공하는 OTT 구독 서비스이다. 넷플릭스나 티빙 등과 카테고리가 겹치므로 특정 시즌에만 이용하는 유저라면 상시 구독 유지 여부를 판단해볼 수 있다. 연간 결제 시 약 16% 할인이 적용된다. 해지 경로는 프로필의 계정 설정 내 멤버십 메뉴에서 멤버십 취소를 선택하면 된다. 해지 이후에도 남은 결제 주기 만료일까지는 콘텐츠를 계속해서 시청할 수 있다.",
        "checked_at": "",
    },
    "유튜브 프리미엄": {
        "category": "OTT, MUSIC",
        "monthly_fee": "14900 (iOS 결제 시 19500)",
        "price_currency": "KRW",
        "plan_info": "일반 요금제",
        "cheaper_plan": "PC/웹 브라우저에서 결제하여 수수료 절감",
        "ad_plan": "없음",
        "annual_discount": "없음 (국내는 개인 연간 요금제 미지원)",
        "alternative_services": ["넷플릭스", "티빙", "우주패스 결합 상품"],
        "cancel_path": "프로필 → 구매 항목 및 멤버십 → 멤버십 취소",
        "caution": ["iOS 결제 건은 애플 앱스토어 구독에서 해지 필요"],
        "document": "유튜브 프리미엄은 광고 없는 영상 시청(OTT)과 유튜브 뮤직(MUSIC)을 동시에 제공하는 결합 구독 서비스이다. 넷플릭스나 멜론 등 동종 카테고리 앱을 각각 따로 사용 중이라면 이중 지출 여부를 점검할 만하다. 아이폰(iOS) 인앱 결제 시 가격이 비싸지므로, PC 웹 브라우저에서 우회 결제하면 요금을 절감할 수 있다. 해지는 앱 내 프로필 메뉴의 구매 항목 및 멤버십에서 취소할 수 있으나, iOS 앱스토어 결제 건은 반드시 아이폰 자체 설정의 '구독 관리'에서 해지해야 정상 처리된다.",
        "checked_at": "",
    },
    "유튜브 프리미엄 라이트": {
        "category": "OTT",
        "monthly_fee": "8500 (iOS 결제 시 10900)",
        "price_currency": "KRW",
        "plan_info": "라이트 요금제",
        "cheaper_plan": "PC/웹 브라우저에서 결제 유도",
        "ad_plan": "일부 광고 포함 (음악 및 비디오 일부 스폰서 광고)",
        "annual_discount": "없음",
        "alternative_services": ["넷플릭스", "티빙", "디즈니+"],
        "cancel_path": "프로필 → 구매 항목 및 멤버십 → 멤버십 취소",
        "caution": ["유튜브 뮤직 이용 불가 기능 숙지"],
        "document": "유튜브 프리미엄 라이트는 음원 스트리밍을 제외하고 핵심 영상 광고만 제거해주는 실속형 OTT 구독 서비스이다. 타 OTT 구독 목록과 비교하여 유지 실익을 점검할 수 있다. 이 요금제 또한 PC나 웹 브라우저 결제가 수수료 측면에서 저렴하다. 해지 경로는 일반 프리미엄과 동일하게 프로필의 구매 항목 및 멤버십에서 가능하다. 해당 요금제는 유튜브 뮤직 백그라운드 재생 혜택이 미포함되어 있으므로 음악 스트리밍 기능 필요 여부를 미리 숙지해야 한다.",
        "checked_at": "",
    },
    "멜론": {
        "category": "MUSIC",
        "monthly_fee": "7900~10900",
        "price_currency": "KRW",
        "plan_info": "스트리밍 클럽 등 다양",
        "cheaper_plan": "통신사(SKT) 할인 및 첫 달 프로모션 활용",
        "ad_plan": "없음",
        "annual_discount": "없음",
        "alternative_services": ["유튜브 뮤직", "스포티파이", "애플뮤직"],
        "cancel_path": "내 정보 → 이용권/쿠폰/캐시 → 변경/해지",
        "caution": ["프로모션 중도 해지 시 할인 혜택 소멸"],
        "document": "멜론은 국내 최대 음원 보유량을 자랑하는 전통적인 음악(MUSIC) 스트리밍 구독 서비스이다. 유튜브 프리미엄이나 스포티파이 등 다른 음악 서비스를 다중 이용하고 있다면 하나로 통합하는 방안을 고려해볼 수 있다. SKT 통신사 결합 혜택이나 첫 달 100원 등의 특가 프로모션을 챙기면 경제적이다. 해지는 내 정보 탭의 이용권/쿠폰/캐시 메뉴에서 변경/해지를 클릭하면 된다. 다만 특가 프로모션 도중 중도 해지 시 기존 할인 혜택이 즉시 소멸되거나 패널티가 있을 수 있어 주의해야 한다.",
        "checked_at": "",
    },
    "스포티파이": {
        "category": "MUSIC",
        "monthly_fee": "10900, 16350",
        "price_currency": "KRW",
        "plan_info": "베이직, 개인, 듀오",
        "cheaper_plan": "오프라인 재생이 제외된 베이직(7,900원) 요금제 확인",
        "ad_plan": "없음 (국내는 무료 광고 요금제 미지원)",
        "annual_discount": "없음",
        "alternative_services": ["유튜브 뮤직", "애플뮤직", "멜론"],
        "cancel_path": "계정 페이지 → 요금제 변경 → 프리미엄 취소",
        "caution": ["타사 결합 상품으로 가입 시 해당 플랫폼에서 해지"],
        "document": "스포티파이는 개인화 큐레이션 알고리즘이 뛰어난 글로벌 음악(MUSIC) 구독 서비스이다. 유튜브 뮤직이나 멜론 등과 기능이 겹치므로 실사용 횟수를 기준으로 점검해볼 수 있다. 다운로드 오프라인 재생 기능이 빠진 베이직 요금제(7,900원)를 선택하면 고정비를 낮출 수 있다. 해지는 웹 계정 페이지의 요금제 변경 메뉴에서 프리미엄 취소를 선택하면 된다. 타 커머스나 통신사 결합 상품으로 가입한 경우에는 스포티파이가 아닌 해당 원가입 플랫폼에서 구독을 종료해야 한다.",
        "checked_at": "",
    },
    "쿠팡 와우": {
        "category": "SHOPPING, OTT",
        "monthly_fee": "7890",
        "price_currency": "KRW",
        "plan_info": "일반 요금제",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "없음",
        "alternative_services": ["컬리멤버스", "네이버플러스 멤버십"],
        "cancel_path": "마이쿠팡 → 와우 멤버십 → 해지하기",
        "caution": ["해지 즉시 로켓배송 무료 혜택", "쿠팡플레이 시청 제한 구역 발생 가능"],
        "document": "쿠팡 와우 멤버십은 로켓배송 무료 혜택(SHOPPING)과 쿠팡플레이(OTT) 서비스를 결합한 라이프스타일 구독 서비스이다. 네이버플러스 멤버십 등 다른 쇼핑 서비스와 동시에 쓰고 있다면 실사용 이점을 비교해볼 필요가 있다. 별도의 저가 요금제나 연간 할인은 존재하지 않는다. 해지 경로는 마이쿠팡의 와우 멤버십 관리 탭 하단에서 해지하기 버튼을 누르면 된다. 주의할 점은 해지 처리가 완료되는 즉시 무료 반품 혜택 및 쿠팡플레이 비디오 시청 권한이 차단될 수 있으므로 배송 중인 상품 유무를 확인해야 한다.",
        "checked_at": "",
    },
    "Google One": {
        "category": "클라우드 스토리지",
        "monthly_fee": "3,400원",
        "price_currency": "KRW",
        "plan_info": "100GB 베이직 플랜",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 결제 시 34,000원, 약 17% 절감)",
        "alternative_services": ["iCloud+", "Microsoft 365", "NAVER MYBOX"],
        "cancel_path": "Google Play 스토어 → 프로필 → 결제 및 정기 결제 → 정기 결제 취소",
        "caution": ["해지 시 무료 제공량 15GB로 축소", "용량 초과 시 Gmail 수발신 및 구글 드라이브 동기화 중단"],
        "document": "Google One은 구글 드라이브, Gmail, 구글 포토의 통합 저장 공간을 제공하는 구독 서비스입니다. iCloud+나 마이크로소프트 365와 같은 타사 스토리지와 기능이 겹치는지 중복 구독 여부를 점검해볼 수 있습니다. 현재 사용 중인 클라우드 저장 용량을 확인하고, 타 서비스의 용량당 가격과 비교해볼 수 있습니다.",
        "checked_at": "",
    },
    "밀리의서재": {
        "category": "콘텐츠 / 도서",
        "monthly_fee": "11,900원",
        "price_currency": "KRW",
        "plan_info": "전자책 정기구독 요금제",
        "cheaper_plan": "통신사 제휴 요금제 (KT, LGU+ 등 부가서비스 확인)",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 구독 시 약 16% 할인된 119,000원)",
        "alternative_services": ["리디셀렉트", "예스24 크레마클럽", "교보문고 SAM"],
        "cancel_path": "앱 하단 관리 → 나의 밀리 → 구독 관리 → 자동결제 해지",
        "caution": ["해지 신청 후에도 다음 결제 예정일까지는 콘텐츠 이용 가능", "다운로드 도서는 해지 후 열람 불가"],
        "document": "밀리의서재는 수만 권의 전자책과 오디오북을 무제한으로 감상할 수 있는 도서 구독 서비스입니다. 리디셀렉트나 크레마클럽 등 타 플랫폼과의 도서 보유량을 비교해볼 수 있습니다. 월평균 독서량과 완독률을 점검해보고, 해지 전에는 남은 이용 기간과 할인 혜택을 확인하는 것이 좋습니다.",
        "checked_at": "",
    },
    "클래스101": {
        "category": "교육 / 온라인 강의",
        "monthly_fee": "19,900원",
        "price_currency": "KRW",
        "plan_info": "101패스 정기구독 (연간 구독의 월 환산가 기준)",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (프로모션별 연간 결제 할인 적용)",
        "alternative_services": ["패스트캠퍼스", "인프런", "유데미"],
        "cancel_path": "마이페이지 → 구독 관리 → 구독 취소",
        "caution": ["구독 취소 시 수강 중이던 클래스 진도율 및 학습 자료 접근 권한 상실"],
        "document": "클래스101은 취미, 재테크, 커리어 등 다양한 카테고리의 영상 강의를 제공하는 구독형 교육 플랫폼입니다. 인프런이나 패스트캠퍼스 등 타 플랫폼과 교육 콘텐츠의 도메인을 비교해볼 수 있습니다. 현재 수강 중인 강의의 주간 시청 시간 및 학습 계획 달성률을 확인해볼 수 있습니다.",
        "checked_at": "",
    },
    "패스트캠퍼스": {
        "category": "교육 / 온라인 강의",
        "monthly_fee": "29,000원",
        "price_currency": "KRW",
        "plan_info": "구독형 온라인 패스",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "해당 없음",
        "alternative_services": ["클래스101", "인프런", "코드잇"],
        "cancel_path": "마이페이지 → 나의 구독 → 구독 해지 신청",
        "caution": ["중도 해지 시 일할 계산 환불 규정은 이용 약관의 별도 확인 필요"],
        "document": "패스트캠퍼스는 IT 커리어, 디자인, 마케팅 등 실무 역량 강화에 초점을 맞춘 교육 구독 서비스입니다. 코드잇이나 인프런 등 개발/실무 중심 플랫폼과 커리큘럼을 비교해볼 수 있습니다. 학습 중인 카테고리의 실무 적용도를 기반으로 유지 여부를 다시 판단해볼 수 있습니다. 해지 전에는 남은 이용 기간과 할인 혜택을 확인하는 것이 좋습니다.",
        "checked_at": "",
    },

    # ===== AI/LLM (USD 결제) =====
    "Notion AI": {
        "category": "AI 생산성",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 10,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다. (연간 결제 시 USD $8/월)",
        "plan_info": "Notion AI 추가 기능 플랜 (Notion 기본 구독과 별도)",
        "cheaper_plan": "연간 결제 전환 시 약 20% 절감",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 결제 시 월 USD $8 상당)",
        "alternative_services": ["ChatGPT Plus", "Claude Pro", "Microsoft Copilot Pro"],
        "cancel_path": "설정 및 멤버 → 요금제 → 요금제 변경 또는 취소",
        "caution": ["해지 시 AI 블록 생성·번역·자동화 기능 이용 제한", "기존 워크스페이스 문서 데이터는 유지됨", "팀 워크스페이스의 경우 팀 전체에 영향"],
        "document": "Notion AI는 노션 워크스페이스 내에서 텍스트 생성, 요약, 번역, 데이터 분석을 돕는 AI 생산성 구독 서비스입니다. ChatGPT Plus나 Claude Pro 등 다른 LLM 기반 서비스와 기능이 겹칠 수 있으므로, 노션 워크스페이스 내 AI 활용 빈도를 기준으로 중복 여부를 점검해볼 수 있습니다. 사용 목적이 노션 내 문서 작업에 집중된 경우라면 유지 실익이 있을 수 있습니다. 해지 전에는 AI 기능으로 생성한 자동화 블록·데이터베이스 연동 여부, 팀 공유 워크스페이스에서의 영향, 연간 결제 여부를 먼저 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "ChatGPT Plus": {
        "category": "AI/LLM",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 20,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "ChatGPT Plus 개인 요금제 (GPT-4o, DALL-E 등 포함)",
        "cheaper_plan": "무료 플랜으로 다운그레이드 가능 (GPT-4o mini 등 기본 모델 무료 제공)",
        "ad_plan": "없음",
        "annual_discount": "없음 (월별 결제만 지원)",
        "alternative_services": ["Claude Pro", "Gemini Advanced", "Perplexity Pro", "Poe"],
        "cancel_path": "chatgpt.com → 우측 상단 계정 아이콘 → 내 플랜 → 구독 취소",
        "caution": [
            "해지 시 GPT-4o, DALL-E 이미지 생성 등 유료 기능 즉시 제한",
            "저장된 대화 기록은 해지 후에도 계정에 유지됨",
            "연결된 GPT Actions 및 외부 서비스 연동 상태 사전 확인 필요",
        ],
        "document": "ChatGPT Plus는 OpenAI의 GPT-4o 등 최신 대형언어모델(LLM) 접근과 이미지 생성, 코드 실행 기능을 제공하는 AI/LLM 구독 서비스입니다. Claude Pro, Gemini Advanced, Perplexity Pro 등 유사 AI 구독과 중복으로 이용 중이라면 사용 목적과 실제 활용 빈도를 함께 확인해볼 수 있습니다. 사용 빈도가 낮은 경우 무료 플랜으로도 기본 모델 이용이 가능하므로 다운그레이드 여부를 점검해볼 수 있습니다. 해지 전에는 저장된 대화 기록 보존 여부, 연결된 외부 서비스 연동 상태, 업무·학습에 활용 중인 자료가 있는지 먼저 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "ChatGPT Team": {
        "category": "AI/LLM",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 25,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $25/user(월별) 또는 USD $20/user(연간). 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "ChatGPT Business(구 Team), 최소 2명 이상",
        "cheaper_plan": "연간 결제 전환 시 월 USD $20/user로 절감 가능",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 약 20% 절감)",
        "alternative_services": ["Claude Team", "Microsoft Copilot Pro", "Notion AI"],
        "cancel_path": "chatgpt.com → 관리자 콘솔 → Billing → 구독 관리 → 취소",
        "caution": [
            "팀 계정 해지 시 전체 팀원 접근 권한 즉시 중단",
            "팀 프로젝트 및 공유 GPT 데이터 사전 백업 필요",
            "연간 결제 중도 해지 시 환불 정책 별도 확인 필요",
        ],
        "document": "ChatGPT Business(구 Team)는 조직 내 여러 구성원이 GPT-4o 등 최신 모델을 함께 이용할 수 있는 팀용 AI/LLM 구독 서비스입니다. 최소 2인 이상 구성이 필요하며, 실제 팀 내 활성 사용자 수와 구독 좌석 수를 비교해볼 수 있습니다. Claude Team, Microsoft Copilot Pro 등 팀용 AI 서비스와 중복 도입 여부도 점검 대상이 될 수 있습니다. 해지 또는 인원 조정 시 팀 내 프로젝트 데이터, 공유 GPT 자산, 연간 결제 여부를 미리 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Claude Pro": {
        "category": "AI/LLM",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 20,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "Claude Pro 개인 요금제 (최신 Claude 모델 + 확장 사용량 + Projects)",
        "cheaper_plan": "무료 플랜으로 다운그레이드 가능 (Claude 기본 기능 무료 제공)",
        "ad_plan": "없음",
        "annual_discount": "없음 (월별 결제만 지원)",
        "alternative_services": ["ChatGPT Plus", "Gemini Advanced", "Perplexity Pro", "Poe"],
        "cancel_path": "claude.ai → 우측 상단 계정 아이콘 → 설정 → 구독 → 구독 취소",
        "caution": [
            "해지 시 현재 결제 기간 만료까지 사용 가능",
            "Projects 기능 및 확장 컨텍스트 접근 제한",
            "저장된 대화 기록 및 Projects 데이터 보존 여부 확인 필요",
        ],
        "document": "Claude Pro는 Anthropic의 Claude 최신 모델에 확장된 사용량과 Projects 기능을 제공하는 AI/LLM 구독 서비스입니다. ChatGPT Plus, Gemini Advanced 등 다른 LLM 구독과 중복 이용 중이라면 사용 목적과 실제 활용 빈도를 함께 점검해볼 수 있습니다. 사용 빈도가 낮은 경우 무료 플랜으로도 Claude 기본 기능 이용이 가능합니다. 해지 전에는 저장된 대화 기록 및 Projects 데이터, 연동된 외부 서비스, 업무·학습에 활용 중인 자료가 있는지 먼저 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Claude Team": {
        "category": "AI/LLM",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 25,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $25/user(월별) 또는 USD $20/user(연간). 최소 5인 이상 구성 필요. 실제 원화 청구액은 환율·카드사 수수료에 따라 달라질 수 있습니다.",
        "plan_info": "Claude Team, 최소 5명 이상",
        "cheaper_plan": "연간 결제 전환 시 월 USD $20/user로 절감 가능",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 약 20% 절감)",
        "alternative_services": ["ChatGPT Business", "Microsoft Copilot Pro", "Notion AI"],
        "cancel_path": "claude.ai → 관리자 설정 → Billing → 구독 관리 → 취소",
        "caution": [
            "팀 계정 해지 시 전체 팀원 접근 즉시 중단",
            "팀 내 공유 Projects 및 대화 기록 사전 백업 필요",
            "연간 결제 중도 해지 시 환불 정책 별도 확인 필요",
        ],
        "document": "Claude Team은 조직 구성원이 Claude 최신 모델을 함께 활용할 수 있는 팀용 AI/LLM 구독 서비스입니다. 최소 5인 이상 좌석이 필요하며, 실제 활성 사용 인원과 구독 좌석 수를 비교해볼 수 있습니다. ChatGPT Business, Notion AI 등 팀 협업용 AI 서비스와 중복 도입 여부도 점검 대상이 될 수 있습니다. 해지 전에는 팀 내 공유 Projects, 대화 기록, 연동된 외부 서비스, 연간 결제 여부를 사전에 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Gemini Advanced": {
        "category": "AI/LLM",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 19.99,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $19.99/월 (Google AI Pro 요금제). 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "Google AI Pro (구 Gemini Advanced / Google One AI Premium)",
        "cheaper_plan": "Google AI Plus (USD $7.99/월)로 다운그레이드 가능",
        "ad_plan": "없음",
        "annual_discount": "없음 (월별 결제)",
        "alternative_services": ["ChatGPT Plus", "Claude Pro", "Perplexity Pro"],
        "cancel_path": "one.google.com → 멤버십 관리 → 구독 취소",
        "caution": [
            "해지 시 Gemini 고급 기능 및 추가 Google Drive 용량 제한",
            "Google Workspace와 연동된 경우 작업 환경 영향 확인 필요",
            "저장된 대화 기록 및 Gems 설정 보존 여부 확인 필요",
        ],
        "document": "Google AI Pro(구 Gemini Advanced)는 Google의 Gemini 최신 모델과 Google Workspace 통합, 추가 클라우드 저장 공간을 함께 제공하는 AI/LLM 구독 서비스입니다. ChatGPT Plus, Claude Pro 등 다른 LLM 구독과 중복 이용 중이라면 실제 사용 목적과 빈도를 기준으로 점검해볼 수 있습니다. 하위 요금제인 Google AI Plus(USD $7.99/월)로 다운그레이드하는 방법도 있습니다. 해지 전에는 Google Drive 추가 용량 사용 여부, Workspace 연동 기능, 저장된 대화 기록과 Gems 설정을 먼저 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Perplexity Pro": {
        "category": "AI/LLM",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 20,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $20/월 또는 USD $200/년. 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "Perplexity Pro 개인 요금제 (웹 검색 + AI 답변 결합)",
        "cheaper_plan": "무료 플랜으로 다운그레이드 가능 (일별 사용 횟수 제한)",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 USD $200, 약 17% 절감)",
        "alternative_services": ["ChatGPT Plus", "Claude Pro", "Google AI Pro"],
        "cancel_path": "perplexity.ai → 프로필 → 설정 → 구독 → 구독 취소",
        "caution": [
            "연간 결제 중도 해지 시 환불 정책 별도 확인 필요",
            "저장된 검색 히스토리 및 스페이스(Space) 데이터 보존 여부 확인",
        ],
        "document": "Perplexity Pro는 웹 검색과 AI 답변을 결합한 AI/LLM 기반 검색 구독 서비스입니다. ChatGPT Plus, Claude Pro 등 범용 LLM 구독과 사용 목적이 겹치는 경우가 있어, 실제 활용 방식(검색 중심 vs. 대화·작성 중심)을 기준으로 중복 여부를 점검해볼 수 있습니다. 무료 플랜에서도 기본 검색 기능을 이용할 수 있으므로 사용 빈도가 낮다면 다운그레이드를 고려해볼 수 있습니다. 연간 결제의 경우 중도 해지 시 환불 정책을 별도로 확인해야 합니다.",
        "checked_at": "2026-07-02",
    },
    "Poe": {
        "category": "AI/LLM",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 19.99,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $19.99/월. 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "Poe 월 구독 (GPT, Claude, Gemini 등 다중 AI 모델 접근)",
        "cheaper_plan": "무료 플랜으로 다운그레이드 가능 (일별 사용 횟수 제한)",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 약 17% 절감)",
        "alternative_services": ["ChatGPT Plus", "Claude Pro", "Gemini Advanced"],
        "cancel_path": "poe.com → 프로필 → 설정 → 구독 관리 → 취소",
        "caution": [
            "ChatGPT Plus·Claude Pro 등 개별 AI 구독과 중복 이용 시 기능 중복 여부 확인",
            "연간 결제 중도 해지 시 환불 정책 별도 확인 필요",
        ],
        "document": "Poe는 ChatGPT, Claude, Gemini 등 다수의 AI 모델을 하나의 구독으로 이용할 수 있는 AI/LLM 멀티모델 플랫폼 서비스입니다. 이미 ChatGPT Plus, Claude Pro 등 개별 AI 구독을 별도로 이용 중이라면 Poe와 기능이 중복되는지 사용 목적과 빈도를 함께 점검해볼 수 있습니다. 무료 플랜에서도 일별 제한 내에서 여러 모델을 이용할 수 있으므로 사용 빈도에 따라 다운그레이드를 고려해볼 수 있습니다. 해지 전에는 연간 결제 여부와 Poe를 통해 생성한 봇·자동화 설정이 있는지 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Cursor Pro": {
        "category": "AI 생산성",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 20,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $20/월 또는 USD $16/월(연간). 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "Cursor Pro 개인 개발자 요금제 (AI 코드 완성, 리팩토링, 채팅 포함)",
        "cheaper_plan": "무료 플랜으로 다운그레이드 가능 (기본 코드 완성 기능 제공)",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 USD $192, 약 20% 절감)",
        "alternative_services": ["GitHub Copilot", "Codeium", "Amazon CodeWhisperer"],
        "cancel_path": "cursor.com → 계정 설정 → Billing → 구독 취소",
        "caution": [
            "해지 시 고급 AI 모델(GPT-4o, Claude 등) 접근 및 에디터 AI 기능 제한",
            "연간 결제 중도 해지 시 환불 정책 별도 확인 필요",
        ],
        "document": "Cursor Pro는 AI 기반 코드 자동완성, 리팩토링, 채팅 기능을 통합 제공하는 코딩 특화 AI 생산성 구독 서비스입니다. GitHub Copilot 등 다른 코딩 AI 도구와 중복으로 이용 중이라면 사용 목적과 실제 활용 빈도를 함께 점검해볼 수 있습니다. 무료 플랜에서도 기본 코드 완성 기능 이용이 가능하므로, 고급 AI 모델 접근이 실제로 필요한지 다시 확인해볼 수 있습니다. 코딩 업무나 학습에 적극적으로 활용 중이라면 사용 목적이 명확한 구독입니다. 해지 전에는 에디터 설정 및 워크스페이스 연동 상태를 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "GitHub Copilot": {
        "category": "AI 생산성",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 10,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $10/월 또는 USD $100/년. 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "GitHub Copilot Pro 개인 요금제",
        "cheaper_plan": "학생 및 오픈소스 유지관리자는 무료 제공 (자격 확인 필요)",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 USD $100, 약 17% 절감)",
        "alternative_services": ["Cursor Pro", "Codeium", "Amazon CodeWhisperer"],
        "cancel_path": "github.com → 계정 설정 → Billing and plans → Copilot → Cancel plan",
        "caution": [
            "IDE 플러그인과 연동되어 있어 해지 후 코드 완성 기능 비활성화",
            "GitHub 학생팩 사용자는 별도 관리 필요",
        ],
        "document": "GitHub Copilot Pro는 Visual Studio Code, JetBrains 등 주요 IDE에서 AI 코드 자동완성을 제공하는 개발자 특화 AI 생산성 구독 서비스입니다. Cursor Pro 등 다른 코딩 AI 도구와 중복으로 이용 중이라면 실제 활용 빈도와 주력 IDE를 기준으로 점검해볼 수 있습니다. 학생 인증 또는 오픈소스 기여자 자격이 있다면 무료로 이용할 수 있으니 자격 여부를 먼저 확인해보는 것도 좋습니다. 코딩 업무나 학습에 직접 활용 중이라면 사용 목적이 명확한 구독입니다. 해지 전에는 현재 사용 중인 IDE 플러그인 연동 상태와 진행 중인 개발 프로젝트 환경을 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Microsoft Copilot Pro": {
        "category": "AI 생산성",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 20,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $20/월. 2026년 8월 이후 단독 플랜 지원 종료 예정. 실제 원화 청구액은 환율·카드사 수수료에 따라 달라질 수 있습니다.",
        "plan_info": "Copilot Pro 개인 요금제 (Word, Excel, PowerPoint 내 AI 기능 포함)",
        "cheaper_plan": "Microsoft 365 Personal(USD $6.99/월)에 Copilot 기능 일부 포함",
        "ad_plan": "없음",
        "annual_discount": "없음 (월별 결제만 지원)",
        "alternative_services": ["ChatGPT Plus", "Claude Pro", "Google AI Pro"],
        "cancel_path": "microsoft.com/account → 서비스 및 구독 → Copilot Pro → 취소",
        "caution": [
            "2026년 8월 이후 단독 플랜 지원 종료 예정, Microsoft 365 구독 상태 확인 필요",
            "Word·Excel·PowerPoint 내 Copilot 기능 비활성화",
        ],
        "document": "Microsoft Copilot Pro는 Word, Excel, PowerPoint 등 Microsoft 365 앱 내에서 AI 지원 기능을 제공하는 AI 생산성 구독 서비스입니다. 단, 2026년 8월 이후 단독 플랜 지원이 종료될 예정으로, Microsoft 365 Personal/Family 구독에 Copilot 기능이 통합되고 있습니다. ChatGPT Plus, Claude Pro 등 범용 LLM과 중복 이용 중이라면 Office 앱 내 AI 기능의 실제 활용 여부를 기준으로 점검해볼 수 있습니다. 해지 전에는 Microsoft 365 구독 상태, Copilot 기능의 업무 연동 여부, 플랜 종료 일정을 먼저 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Canva Pro": {
        "category": "AI 콘텐츠 제작",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 15,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. USD $15/월 또는 USD $10/월(연간). 실제 원화 청구액은 환율·카드사 수수료·세금 여부에 따라 달라질 수 있습니다.",
        "plan_info": "Canva Pro 개인 요금제 (프리미엄 템플릿, AI 이미지 생성, 브랜드 킷 포함)",
        "cheaper_plan": "무료 플랜으로 다운그레이드 가능 (기본 디자인 기능 유지)",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 USD $120, 월 환산 USD $10으로 약 33% 절감)",
        "alternative_services": ["Adobe Express", "Figma", "Microsoft Designer"],
        "cancel_path": "canva.com → 계정 → 요금제 및 결제 → Pro 취소",
        "caution": [
            "해지 시 Pro 전용 템플릿·폰트·사진 등 프리미엄 에셋 접근 제한",
            "Pro 에셋으로 제작된 디자인 파일은 해지 전 내보내기(export) 권장",
            "연간 결제 중도 해지 시 환불 가능 여부 별도 확인 필요",
        ],
        "document": "Canva Pro는 디자인 템플릿, 프리미엄 에셋, AI 이미지 생성 기능을 포함한 그래픽 디자인 특화 AI 콘텐츠 제작 구독 서비스입니다. Adobe Express, Figma 등 다른 디자인 도구와 중복으로 이용 중이라면 실제 활용 빈도와 주력 작업 환경을 기준으로 점검해볼 수 있습니다. 무료 플랜으로도 기본 디자인 기능은 이용 가능하므로, Pro 전용 기능의 실제 사용 빈도를 확인해볼 수 있습니다. 해지 전에는 Pro 전용 에셋으로 제작된 디자인 파일을 내보내거나 별도 저장하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Midjourney": {
        "category": "AI 콘텐츠 제작",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 30,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. Basic USD $10/월, Standard USD $30/월, Pro USD $60/월, Mega USD $120/월. 실제 원화 청구액은 환율·카드사 수수료에 따라 달라질 수 있습니다.",
        "plan_info": "Basic($10), Standard($30), Pro($60), Mega($120) 요금제 — 참고 기준: Standard($30/월)",
        "cheaper_plan": "Basic 플랜(USD $10/월)으로 다운그레이드 가능",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 약 20% 절감)",
        "alternative_services": ["DALL-E (ChatGPT Plus 포함)", "Adobe Firefly", "Stable Diffusion"],
        "cancel_path": "midjourney.com → 계정 → Manage Plan → Cancel Plan",
        "caution": [
            "해지 시 이미지 생성 기능 즉시 중단",
            "생성된 이미지는 계정에 보관되나 신규 생성 불가",
            "연간 결제 중도 해지 시 환불 정책 별도 확인 필요",
        ],
        "document": "Midjourney는 텍스트 프롬프트로 고품질 이미지를 생성하는 AI 이미지 생성 구독 서비스입니다. DALL-E(ChatGPT Plus 포함), Adobe Firefly, Stable Diffusion 등 다른 이미지 생성 AI와 중복으로 이용 중이라면 실제 사용 목적과 생성 빈도를 기준으로 점검해볼 수 있습니다. Basic 요금제(USD $10/월)로 다운그레이드하거나, 사용량이 적은 달에는 월별 결제로 전환해 필요한 달만 구독하는 방법도 있습니다. 해지 전에는 생성된 이미지 자산의 다운로드 여부와 진행 중인 상업적 활용 계약이 있는지 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "Runway": {
        "category": "AI 콘텐츠 제작",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 12,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. Standard USD $12/월(연간) 또는 약 USD $15/월(월별), Pro USD $28/월(연간). 실제 원화 청구액은 환율·카드사 수수료에 따라 달라질 수 있습니다.",
        "plan_info": "Standard(USD $12/월 연간), Pro(USD $28/월 연간), Max(USD $76/월 연간)",
        "cheaper_plan": "무료 플랜으로 다운그레이드 가능 (월 125크레딧 제공)",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 월별 대비 약 20% 절감)",
        "alternative_services": ["Sora", "Pika", "Kling AI"],
        "cancel_path": "runwayml.com → 계정 설정 → Billing → 구독 취소",
        "caution": [
            "크레딧 기반 과금으로 미사용 크레딧 이월 여부 확인 필요",
            "생성된 비디오 자산은 해지 전 다운로드 권장",
            "연간 결제 중도 해지 시 환불 정책 별도 확인 필요",
        ],
        "document": "Runway는 텍스트나 이미지를 기반으로 AI 영상을 생성하고 편집할 수 있는 AI 콘텐츠 제작 구독 서비스입니다. Sora, Pika, Kling AI 등 다른 AI 영상 생성 도구와 중복으로 이용 중이라면 실제 활용 빈도와 주력 플랫폼을 기준으로 점검해볼 수 있습니다. 무료 플랜에서도 월 125크레딧이 제공되므로 사용량이 적은 경우 다운그레이드를 고려해볼 수 있습니다. 콘텐츠 제작 업무나 프로젝트에 직접 활용 중이라면 사용 목적이 명확한 구독입니다. 해지 전에는 미사용 크레딧 소멸 여부, 완성된 영상 자산의 다운로드 상태, 진행 중인 프로젝트가 있는지 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
    "ElevenLabs": {
        "category": "AI 콘텐츠 제작",
        "monthly_fee": None,
        "price_currency": "USD",
        "monthly_fee_usd": 22,
        "monthly_fee_krw_estimated": None,
        "exchange_rate_used": None,
        "pricing_note": "해외 결제 서비스입니다. Starter USD $6/월, Creator USD $22/월, Pro USD $99/월. 실제 원화 청구액은 환율·카드사 수수료에 따라 달라질 수 있습니다.",
        "plan_info": "Free, Starter(USD $6), Creator(USD $22), Pro(USD $99) 요금제 — 참고 기준: Creator($22/월)",
        "cheaper_plan": "무료 플랜 또는 Starter(USD $6/월)로 다운그레이드 가능",
        "ad_plan": "없음",
        "annual_discount": "없음 (월별 결제)",
        "alternative_services": ["CLOVA Dubbing", "Murf AI", "Suno AI"],
        "cancel_path": "elevenlabs.io → 프로필 → 구독 → 구독 취소",
        "caution": [
            "크레딧 기반 과금으로 미사용 크레딧 소멸 여부 확인 필요",
            "생성된 음성 클립 및 커스텀 음성 모델은 해지 후 이용 제한",
            "외부 서비스 API 연동이 있는 경우 사전 확인 필요",
        ],
        "document": "ElevenLabs는 텍스트를 자연스러운 AI 음성으로 변환하거나 커스텀 음성 모델을 생성할 수 있는 AI 콘텐츠 제작 구독 서비스입니다. CLOVA Dubbing, Murf AI 등 다른 AI 보이스 서비스와 중복으로 이용 중이라면 실제 활용 빈도와 사용 목적을 기준으로 점검해볼 수 있습니다. Starter 플랜(USD $6/월)이나 무료 플랜으로 다운그레이드하면 월 이용 비용을 줄일 수 있습니다. 콘텐츠 제작, 더빙, 팟캐스트 등 업무·창작에 적극 활용 중이라면 사용 목적이 명확한 구독입니다. 해지 전에는 생성한 커스텀 음성 모델, 미사용 크레딧 소멸 여부, 외부 API 연동이 있는지 확인하는 것이 좋습니다.",
        "checked_at": "2026-07-02",
    },
}

# USD 결제 서비스 카테고리 (프론트 안내 문구 판단용)
USD_CATEGORIES = {"AI/LLM", "AI 생산성", "AI 콘텐츠 제작"}


# ===== 서비스명 정규화 및 별칭 처리 =====

def normalize_name(name: str) -> str:
    """서비스명을 정규화합니다. (소문자 + 공백/하이픈/언더바/점 제거)"""
    name = name.lower().strip()
    name = re.sub(r'[\s\-_\.]', '', name)
    return name


# 정규화된 별칭 → SUBSCRIPTION_DB 표준 키
SERVICE_ALIASES = {
    # 디즈니+
    "디즈니플러스":             "디즈니+",
    "disney+":                  "디즈니+",
    "disneyplus":               "디즈니+",
    # 쿠팡 와우
    "쿠팡와우":                 "쿠팡 와우",
    "쿠팡와우멤버십":           "쿠팡 와우",
    "coupangwow":               "쿠팡 와우",
    # 유튜브 프리미엄
    "유튜브프리미엄":           "유튜브 프리미엄",
    "youtubepremium":           "유튜브 프리미엄",
    # 유튜브 프리미엄 라이트
    "유튜브프리미엄라이트":     "유튜브 프리미엄 라이트",
    # 네이버플러스 멤버십
    "네이버플러스":             "네이버플러스 멤버십",
    "네이버플러스멤버십":       "네이버플러스 멤버십",
    "naverplus":                "네이버플러스 멤버십",
    "naverplusmembership":      "네이버플러스 멤버십",
    # iCloud
    "icloud":                   "icloud",
    "아이클라우드":             "icloud",
    # 넷플릭스
    "netflix":                  "넷플릭스",
    # 웨이브
    "wavve":                    "웨이브",
    "wave":                     "웨이브",
    # 티빙
    "tving":                    "티빙",
    # 스포티파이
    "spotify":                  "스포티파이",
    # 멜론
    "melon":                    "멜론",
    # Google One
    "googleone":                "Google One",
    "구글원":                   "Google One",
    "구글드라이브":             "Google One",
    # Notion AI
    "notionai":                 "Notion AI",
    "노션ai":                   "Notion AI",
    "노션에이아이":             "Notion AI",
    "노션":                     "Notion AI",
    "notion":                   "Notion AI",
    # 밀리의서재
    "밀리":                     "밀리의서재",
    "millie":                   "밀리의서재",
    "밀리서재":                 "밀리의서재",
    # 클래스101
    "class101":                 "클래스101",
    "클래스101":                "클래스101",
    # 패스트캠퍼스
    "fastcampus":               "패스트캠퍼스",

    # ── AI/LLM ──
    "chatgpt":                  "ChatGPT Plus",
    "chatgptplus":              "ChatGPT Plus",
    "챗지피티":                 "ChatGPT Plus",
    "챗gpt":                    "ChatGPT Plus",
    "지피티":                   "ChatGPT Plus",
    "openai":                   "ChatGPT Plus",
    "chatgptteam":              "ChatGPT Team",
    "chatgptbusiness":          "ChatGPT Team",
    "챗지피티팀":               "ChatGPT Team",
    "claude":                   "Claude Pro",
    "claudepro":                "Claude Pro",
    "클로드":                   "Claude Pro",
    "클로드프로":               "Claude Pro",
    "claudeteam":               "Claude Team",
    "클로드팀":                 "Claude Team",
    "gemini":                   "Gemini Advanced",
    "geminiadvanced":           "Gemini Advanced",
    "제미나이":                 "Gemini Advanced",
    "구글제미나이":             "Gemini Advanced",
    "googleaipro":              "Gemini Advanced",
    "googleai":                 "Gemini Advanced",
    "perplexity":               "Perplexity Pro",
    "perplexitypro":            "Perplexity Pro",
    "퍼플렉시티":               "Perplexity Pro",
    "poe":                      "Poe",

    # ── AI 생산성 ──
    "cursor":                   "Cursor Pro",
    "cursorpro":                "Cursor Pro",
    "커서":                     "Cursor Pro",
    "커서프로":                 "Cursor Pro",
    "githubcopilot":            "GitHub Copilot",
    "copilot":                  "GitHub Copilot",
    "깃허브코파일럿":           "GitHub Copilot",
    "깃헙코파일럿":             "GitHub Copilot",
    "copilotpro":               "Microsoft Copilot Pro",
    "microsoftcopilot":         "Microsoft Copilot Pro",
    "microsoftcopilotpro":      "Microsoft Copilot Pro",
    "마이크로소프트코파일럿":   "Microsoft Copilot Pro",

    # ── AI 콘텐츠 제작 ──
    "canva":                    "Canva Pro",
    "canvapro":                 "Canva Pro",
    "캔바":                     "Canva Pro",
    "캔바프로":                 "Canva Pro",
    "midjourney":               "Midjourney",
    "미드저니":                 "Midjourney",
    "runway":                   "Runway",
    "런웨이":                   "Runway",
    "runwayml":                 "Runway",
    "elevenlabs":               "ElevenLabs",
    "일레븐랩스":               "ElevenLabs",
}

# SUBSCRIPTION_DB 키를 정규화한 역방향 매핑 (모듈 로드 시 자동 생성)
_NORMALIZED_DB_KEYS: dict = {normalize_name(k): k for k in SUBSCRIPTION_DB.keys()}


def resolve_service_name(service_name: str):
    """
    사용자 입력 서비스명을 SUBSCRIPTION_DB의 표준 키로 변환합니다.

    1순위: SERVICE_ALIASES 별칭 사전
    2순위: SUBSCRIPTION_DB 키 정규화 비교
    없으면 None 반환
    """
    normalized = normalize_name(service_name)

    if normalized in SERVICE_ALIASES:
        return SERVICE_ALIASES[normalized]

    if normalized in _NORMALIZED_DB_KEYS:
        return _NORMALIZED_DB_KEYS[normalized]

    return None


def generate_rag_response(service_name: str, status: str):
    """
    SUBSCRIPTION_DB에서 서비스 정보를 조회하여 결과 카드 데이터를 반환합니다.

    서비스명이 DB에 없으면 None을 반환합니다.
    (rag_stub.py의 CSV/fallback 단계로 내려가도록 유도)
    """
    if status == "유지 후보":
        return {
            "service_name": service_name,
            "matched_service_name": service_name,
            "rag_explanation": f"{service_name}은 현재 만족스럽게 이용 중이신 서비스로 분류되어 유지를 권장합니다.",
            "alternatives": [],
            "cancel_path": "",
            "cautions": [],
        }

    matched_key = resolve_service_name(service_name)
    if not matched_key:
        return None

    info = SUBSCRIPTION_DB.get(matched_key)
    if not info:
        return None

    return {
        "service_name": service_name,           # 사용자 원래 입력값 (화면 표시용)
        "matched_service_name": matched_key,    # DB에서 매칭된 표준 키
        "rag_explanation": info["document"],
        "alternatives": info["alternative_services"],   # 이미 리스트
        "cancel_path": info["cancel_path"],
        "cautions": info["caution"],                    # 이미 리스트
    }
