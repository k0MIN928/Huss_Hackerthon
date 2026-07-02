import re

# ===== 구독 서비스 마스터 데이터 (16개) =====
SUBSCRIPTION_DB = {
    "네이버플러스 멤버십": {
        "category": "Shopping, OTT",
        "monthly_fee": "4,900원",
        "plan_info": "일반 요금제",
        "cheaper_plan": "연간 멤버십 이용 시 할인 (월 3900원)",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 46800원)",
        "alternative_services": ["쿠팡 와우 멤버십", "컬리멤버스"],
        "cancel_path": "네이버플러스 멤버십 MY → 설정 → 네이버플러스 멤버십 해지",
        "caution": [
            "남은 기간 유지 여부",
            "적립된 포인트 회수 조건 확인"
        ],
        "document": "네이버플러스 멤버십은 Shopping 및 OTT 카테고리에 속하는 구독 서비스이다. 쿠팡 와우 멤버십이나 컬리멤버스와 같은 쇼핑 결합 서비스들과 대체 관계에 있으므로 중복 구독 여부를 점검할 필요가 있다. 월 요금은 4,900원이며 연간 멤버십을 이용할 경우 월 3,900원 꼴로 절감하여 이용할 수 있다. 해지하려는 경우 네이버플러스 멤버십 MY의 설정 메뉴에서 멤버십 해지를 진행할 수 있으며, 해지 전에는 남은 기간 유지 조건과 그동안 적립된 네이버페이 포인트의 회수 조건이 있는지 반드시 확인해야 한다."
    },
    "icloud": {
        "category": "DRIVE",
        "monthly_fee": "1100, 3300, 11100",
        "plan_info": "50GB, 200GB, 2TB",
        "cheaper_plan": "무료 5GB 요금제 다운그레이드",
        "ad_plan": "해당 없음",
        "annual_discount": "없음",
        "alternative_services": ["구글 원", "마이크로소프트 365", "드롭박스"],
        "cancel_path": "iPhone 설정 → Apple ID → iCloud → 저장 공간 관리 → 요금제 변경",
        "caution": ["다운그레이드 시 초과된 용량의 데이터 삭제 위험 확인"],
        "document": "iCloud는 Apple의 대표적인 클라우드 스토리지(DRIVE) 구독 서비스이다. 구글 원, 마이크로소프트 365, 드롭박스 등과 같은 대체재가 존재하므로 타 클라우드와 중복 사용 여부를 점검해야 한다. 용량에 따라 월 1,100원부터 11,100원까지 요금제가 나뉘며, 더 낮은 용량이나 무료 5GB 요금제로 다운그레이드가 가능하다. 해지 및 요금제 변경은 iPhone 설정의 Apple ID 메뉴 내 iCloud 저장 공간 관리에서 진행할 수 있다. 이때 용량을 줄이면 초과된 용량만큼의 데이터가 영구 삭제될 위험이 있으므로 백업 상태를 반드시 확인해야 한다."
    },
    "넷플릭스": {
        "category": "OTT",
        "monthly_fee": "5500, 13500, 17000",
        "plan_info": "광고형 스탠다드, 스탠다드, 프리미엄",
        "cheaper_plan": "광고형 스탠다드 요금제 선택",
        "ad_plan": "있음 (광고형 스탠다드)",
        "annual_discount": "없음",
        "alternative_services": ["웨이브", "디즈니+", "티빙"],
        "cancel_path": "계정 → 멤버십 해지",
        "caution": ["해지 후에도 이번 결제 주기가 끝날 때까지 시청 가능"],
        "document": "넷플릭스는 전 세계에서 가장 널리 쓰이는 OTT 구독 서비스이다. 티빙, 웨이브, 디즈니플러스 등 국내외 다양한 OTT 플랫폼들과 카테고리가 겹치므로 여러 OTT를 중복 구독 중이라면 이용 빈도를 점검하는 것이 좋다. 요금제는 광고형 스탠다드(5,500원)부터 프리미엄(17,000원)까지 제공되며, 비용을 아끼려면 광고형 요금제로 전환하는 방법이 있다. 해지는 서비스 내 계정 메뉴에서 멤버십 해지를 선택하면 된다. 해지 신청을 하더라도 이미 결제된 이번 주기의 만료일까지는 추가 요금 없이 정상 시청이 가능하다."
    },
    "티빙": {
        "category": "OTT",
        "monthly_fee": "5500, 9500, 13500, 17000",
        "plan_info": "광고형 요금제, 베이직, 스탠다드, 프리미엄",
        "cheaper_plan": "광고형 요금제 또는 연간 결제 확인",
        "ad_plan": "있음 (광고형 스탠다드)",
        "annual_discount": "있음 (연간 결제 시 약 25% 할인)",
        "alternative_services": ["넷플릭스", "웨이브", "디즈니+"],
        "cancel_path": "마이페이지 → 이용권/결제관리 → 정기결제 해지",
        "caution": ["연간 이용권은 중도 해지 시 환불 규정 까다로움"],
        "document": "티빙은 국내 예능 및 드라마 콘텐츠가 강점인 OTT 구독 서비스이다. 넷플릭스, 웨이브 등 동종 카테고리의 타 서비스들과 동시에 구독 중이라면 실사용량 대비 고정 지출을 점검할 필요가 있다. 광고요금제를 선택하거나 연간 결제를 활용하면 비용을 아낄 수 있다. 해지 경로는 마이페이지의 이용권/결제관리에서 정기결제 해지를 선택하면 된다. 단, 연간 이용권의 경우 중도 해지 시 환불 위약금 및 조건이 까다로우므로 결제 형태를 미리 확인하는 것이 권장된다."
    },
    "웨이브": {
        "category": "OTT",
        "monthly_fee": "7900, 10900, 13900",
        "plan_info": "베이직, 스탠다드, 프리미엄",
        "cheaper_plan": "통신사(SKT) 결합 요금제 확인",
        "ad_plan": "없음",
        "annual_discount": "있음 (연간 결제 시 16% 할인)",
        "alternative_services": ["넷플릭스", "티빙", "디즈니+"],
        "cancel_path": "MY → 이용권 내역 → 자동결제 해지",
        "caution": ["제휴 이용권은 해당 제휴사에서 해지해야 할 수 있음"],
        "document": "웨이브는 지상파 및 다양한 방송 콘텐츠를 제공하는 OTT 구독 서비스이다. 다른 OTT 플랫폼과 중복 결제되고 있지는 않은지 사용 빈도를 기준으로 점검해볼 수 있다. 기본 요금제 외에도 SKT 통신사 결합 요금제나 제휴 할인이 있는지 확인하면 비용을 낮출 수 있다. 해지는 MY 메뉴의 이용권 내역에서 자동결제 해지를 누르면 된다. 만약 통신사나 타 제휴사를 통해 가입한 이용권이라면 웨이브 앱이 아닌 해당 제휴사 커스터머 센터 등에서 해지 절차를 밟아야 할 수 있으니 유의해야 한다."
    },
    "디즈니+": {
        "category": "OTT",
        "monthly_fee": "9900, 13900",
        "plan_info": "스탠다드, 프리미엄",
        "cheaper_plan": "연간 결제 할인 확인",
        "ad_plan": "없음 (국내 기준)",
        "annual_discount": "있음 (연간 결제 시 약 16% 할인)",
        "alternative_services": ["넷플릭스", "티빙", "웨이브"],
        "cancel_path": "프로필 → 계정 → 멤버십 → 멤버십 취소",
        "caution": ["결제 주기 만료일까지 서비스 이용 가능"],
        "document": "디즈니플러스는 디즈니, 마블, 픽사 등의 IP를 독점 제공하는 OTT 구독 서비스이다. 넷플릭스나 티빙 등과 카테고리가 겹치므로 특정 시즌에만 이용하는 유저라면 상시 구독 유지 여부를 판단해볼 수 있다. 연간 결제 시 약 16% 할인이 적용된다. 해지 경로는 프로필의 계정 설정 내 멤버십 메뉴에서 멤버십 취소를 선택하면 된다. 해지 이후에도 남은 결제 주기 만료일까지는 콘텐츠를 계속해서 시청할 수 있다."
    },
    "유튜브 프리미엄": {
        "category": "OTT, MUSIC",
        "monthly_fee": "14900 (iOS 결제 시 19500)",
        "plan_info": "일반 요금제",
        "cheaper_plan": "PC/웹 브라우저에서 결제하여 수수료 절감",
        "ad_plan": "없음",
        "annual_discount": "없음 (국내는 개인 연간 요금제 미지원)",
        "alternative_services": ["넷플릭스", "티빙", "우주패스 결합 상품"],
        "cancel_path": "프로필 → 구매 항목 및 멤버십 → 멤버십 취소",
        "caution": ["iOS 결제 건은 애플 앱스토어 구독에서 해지 필요"],
        "document": "유튜브 프리미엄은 광고 없는 영상 시청(OTT)과 유튜브 뮤직(MUSIC)을 동시에 제공하는 결합 구독 서비스이다. 넷플릭스나 멜론 등 동종 카테고리 앱을 각각 따로 사용 중이라면 이중 지출 여부를 점검할 만하다. 아이폰(iOS) 인앱 결제 시 가격이 비싸지므로, PC 웹 브라우저에서 우회 결제하면 요금을 절감할 수 있다. 해지는 앱 내 프로필 메뉴의 구매 항목 및 멤버십에서 취소할 수 있으나, iOS 앱스토어 결제 건은 반드시 아이폰 자체 설정의 '구독 관리'에서 해지해야 정상 처리된다."
    },
    "유튜브 프리미엄 라이트": {
        "category": "OTT",
        "monthly_fee": "8500 (iOS 결제 시 10900)",
        "plan_info": "라이트 요금제",
        "cheaper_plan": "PC/웹 브라우저에서 결제 유도",
        "ad_plan": "일부 광고 포함 (음악 및 비디오 일부 스폰서 광고)",
        "annual_discount": "없음",
        "alternative_services": ["넷플릭스", "티빙", "디즈니+"],
        "cancel_path": "프로필 → 구매 항목 및 멤버십 → 멤버십 취소",
        "caution": ["유튜브 뮤직 이용 불가 기능 숙지"],
        "document": "유튜브 프리미엄 라이트는 음원 스트리밍을 제외하고 핵심 영상 광고만 제거해주는 실속형 OTT 구독 서비스이다. 타 OTT 구독 목록과 비교하여 유지 실익을 점검할 수 있다. 이 요금제 또한 PC나 웹 브라우저 결제가 수수료 측면에서 저렴하다. 해지 경로는 일반 프리미엄과 동일하게 프로필의 구매 항목 및 멤버십에서 가능하다. 해당 요금제는 유튜브 뮤직 백그라운드 재생 혜택이 미포함되어 있으므로 음악 스트리밍 기능 필요 여부를 미리 숙지해야 한다."
    },
    "멜론": {
        "category": "MUSIC",
        "monthly_fee": "7900~10900",
        "plan_info": "스트리밍 클럽 등 다양",
        "cheaper_plan": "통신사(SKT) 할인 및 첫 달 프로모션 활용",
        "ad_plan": "없음",
        "annual_discount": "없음",
        "alternative_services": ["유튜브 뮤직", "스포티파이", "애플뮤직"],
        "cancel_path": "내 정보 → 이용권/쿠폰/캐시 → 변경/해지",
        "caution": ["프로모션 중도 해지 시 할인 혜택 소멸"],
        "document": "멜론은 국내 최대 음원 보유량을 자랑하는 전통적인 음악(MUSIC) 스트리밍 구독 서비스이다. 유튜브 프리미엄이나 스포티파이 등 다른 음악 서비스를 다중 이용하고 있다면 하나로 통합하는 방안을 고려해볼 수 있다. SKT 통신사 결합 혜택이나 첫 달 100원 등의 특가 프로모션을 챙기면 경제적이다. 해지는 내 정보 탭의 이용권/쿠폰/캐시 메뉴에서 변경/해지를 클릭하면 된다. 다만 특가 프로모션 도중 중도 해지 시 기존 할인 혜택이 즉시 소멸되거나 패널티가 있을 수 있어 주의해야 한다."
    },
    "스포티파이": {
        "category": "MUSIC",
        "monthly_fee": "10900, 16350",
        "plan_info": "베이직, 개인, 듀오",
        "cheaper_plan": "오프라인 재생이 제외된 베이직(7,900원) 요금제 확인",
        "ad_plan": "없음 (국내는 무료 광고 요금제 미지원)",
        "annual_discount": "없음",
        "alternative_services": ["유튜브 뮤직", "애플뮤직", "멜론"],
        "cancel_path": "계정 페이지 → 요금제 변경 → 프리미엄 취소",
        "caution": ["타사 결합 상품으로 가입 시 해당 플랫폼에서 해지"],
        "document": "스포티파이는 개인화 큐레이션 알고리즘이 뛰어난 글로벌 음악(MUSIC) 구독 서비스이다. 유튜브 뮤직이나 멜론 등과 기능이 겹치므로 실사용 횟수를 기준으로 점검해볼 수 있다. 다운로드 오프라인 재생 기능이 빠진 베이직 요금제(7,900원)를 선택하면 고정비를 낮출 수 있다. 해지는 웹 계정 페이지의 요금제 변경 메뉴에서 프리미엄 취소를 선택하면 된다. 타 커머스나 통신사 결합 상품으로 가입한 경우에는 스포티파이가 아닌 해당 원가입 플랫폼에서 구독을 종료해야 한다."
    },
    "쿠팡 와우": {
        "category": "SHOPPING, OTT",
        "monthly_fee": "7890",
        "plan_info": "일반 요금제",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "없음",
        "alternative_services": ["컬리멤버스", "네이버플러스 멤버십"],
        "cancel_path": "마이쿠팡 → 와우 멤버십 → 해지하기",
        "caution": [
            "해지 즉시 로켓배송 무료 혜택",
            "쿠팡플레이 시청 제한 구역 발생 가능"
        ],
        "document": "쿠팡 와우 멤버십은 로켓배송 무료 혜택(SHOPPING)과 쿠팡플레이(OTT) 서비스를 결합한 라이프스타일 구독 서비스이다. 네이버플러스 멤버십 등 다른 쇼핑 서비스와 동시에 쓰고 있다면 실사용 이점을 비교해볼 필요가 있다. 별도의 저가 요금제나 연간 할인은 존재하지 않는다. 해지 경로는 마이쿠팡의 와우 멤버십 관리 탭 하단에서 해지하기 버튼을 누르면 된다. 주의할 점은 해지 처리가 완료되는 즉시 무료 반품 혜택 및 쿠팡플레이 비디오 시청 권한이 차단될 수 있으므로 배송 중인 상품 유무를 확인해야 한다."
    },
    "Google One": {
        "category": "클라우드 스토리지",
        "monthly_fee": "3,400원",
        "plan_info": "100GB 베이직 플랜",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 결제 시 34,000원, 약 17% 절감)",
        "alternative_services": ["iCloud+", "Microsoft 365", "NAVER MYBOX"],
        "cancel_path": "Google Play 스토어 → 프로필 → 결제 및 정기 결제 → 정기 결제 취소",
        "caution": [
            "해지 시 무료 제공량 15GB로 축소됩니다.",
            "용량 초과 시 Gmail 수발신 및 구글 드라이브 동기화가 중단됩니다."
        ],
        "document": "Google One은 구글 드라이브, Gmail, 구글 포토의 통합 저장 공간을 제공하는 구독 서비스입니다. iCloud+나 마이크로소프트 365와 같은 타사 스토리지와 기능이 겹치는지 중복 구독 여부를 점검해볼 수 있습니다. 현재 사용 중인 클라우드 저장 용량을 확인하고, 타 서비스의 용량당 가격과 비교해볼 수 있습니다."
    },
    "Notion AI": {
        "category": "생산성 / AI",
        "monthly_fee": "14,000원 (월 $10 상당)",
        "plan_info": "Notion AI 추가 기능 플랜",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 결제 시 월 $8 상당으로 약 20% 절감)",
        "alternative_services": ["ChatGPT Plus", "Claude Pro", "Microsoft Copilot"],
        "cancel_path": "설정 및 멤버 → 요금제 → 요금제 변경 또는 취소",
        "caution": [
            "해지 시 AI 블록 생성, 번역 및 자동화 기능 이용이 제한됩니다.",
            "기존에 작성된 워크스페이스 문서 데이터는 그대로 유지됩니다."
        ],
        "document": "Notion AI는 노션 워크스페이스 내에서 텍스트 생성, 요약, 데이터 분석을 돕는 생산성 구독 서비스입니다. ChatGPT Plus나 Claude Pro 등 다른 LLM 기반 서비스들과 비교해볼 수 있습니다. AI 기능의 실제 활용 빈도와 업무 기여도를 기반으로 유지 여부를 다시 판단해볼 수 있습니다."
    },
    "밀리의서재": {
        "category": "콘텐츠 / 도서",
        "monthly_fee": "11,900원",
        "plan_info": "전자책 정기구독 요금제",
        "cheaper_plan": "통신사 제휴 요금제 (KT, LGU+ 등 부가서비스 확인)",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (연간 구독 시 약 16% 할인된 119,000원)",
        "alternative_services": ["리디셀렉트", "예스24 크레마클럽", "교보문고 SAM"],
        "cancel_path": "앱 하단 관리 → 나의 밀리 → 구독 관리 → 자동결제 해지",
        "caution": [
            "해지 신청 후에도 다음 결제 예정일까지는 콘텐츠 이용이 가능합니다.",
            "다운로드해 두었던 도서 콘텐츠는 해지 시점 이후 열람할 수 없습니다."
        ],
        "document": "밀리의서재는 수만 권의 전자책과 오디오북을 무제한으로 감상할 수 있는 도서 구독 서비스입니다. 리디셀렉트나 크레마클럽 등 타 플랫폼과의 도서 보유량을 비교해볼 수 있습니다. 월평균 독서량과 완독률을 점검해보고, 해지 전에는 남은 이용 기간과 할인 혜택을 확인하는 것이 좋습니다."
    },
    "클래스101": {
        "category": "교육 / 온라인 강의",
        "monthly_fee": "19,900원",
        "plan_info": "101패스 정기구독 (연간 구독의 월 환산가 기준)",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "있음 (프로모션별 연간 결제 할인 적용)",
        "alternative_services": ["패스트캠퍼스", "인프런", "유데미"],
        "cancel_path": "마이페이지 → 구독 관리 → 구독 취소",
        "caution": [
            "구독 취소 시 수강 중이던 모든 클래스의 진도율과 학습 자료 접근 권한이 상실됩니다."
        ],
        "document": "클래스101은 취미, 재테크, 커리어 등 다양한 카테고리의 영상 강의를 제공하는 구독형 교육 플랫폼입니다. 인프런이나 패스트캠퍼스 등 타 플랫폼과 교육 콘텐츠의 도메인을 비교해볼 수 있습니다. 현재 수강 중인 강의의 주간 시청 시간 및 학습 계획 달성률을 확인해볼 수 있습니다."
    },
    "패스트캠퍼스": {
        "category": "교육 / 온라인 강의",
        "monthly_fee": "29,000원",
        "plan_info": "구독형 온라인 패스",
        "cheaper_plan": "해당 없음",
        "ad_plan": "해당 없음",
        "annual_discount": "해당 없음",
        "alternative_services": ["클래스101", "인프런", "코드잇"],
        "cancel_path": "마이페이지 → 나의 구독 → 구독 해지 신청",
        "caution": [
            "중도 해지 시 일할 계산 환불 규정은 이용 약관의 별도 확인이 필요합니다."
        ],
        "document": "패스트캠퍼스는 IT 커리어, 디자인, 마케팅 등 실무 역량 강화에 초점을 맞춘 교육 구독 서비스입니다. 코드잇이나 인프런 등 개발/실무 중심 플랫폼과 커리큘럼을 비교해볼 수 있습니다. 학습 중인 카테고리의 실무 적용도를 기반으로 유지 여부를 다시 판단해볼 수 있습니다. 해지 전에는 남은 이용 기간과 할인 혜택을 확인하는 것이 좋습니다."
    }
}


# ===== 서비스명 정규화 및 별칭 처리 =====

def normalize_name(name: str) -> str:
    """서비스명을 정규화합니다. (소문자 + 공백/하이픈/언더바/점 제거)"""
    name = name.lower().strip()
    name = re.sub(r'[\s\-_\.]', '', name)
    return name


# 정규화된 별칭 → SUBSCRIPTION_DB 표준 키
SERVICE_ALIASES = {
    # 디즈니+
    "디즈니플러스":         "디즈니+",
    "disney+":              "디즈니+",
    "disneyplus":           "디즈니+",
    # 쿠팡 와우
    "쿠팡와우":             "쿠팡 와우",
    "쿠팡와우멤버십":       "쿠팡 와우",
    "coupangwow":           "쿠팡 와우",
    # 유튜브 프리미엄
    "유튜브프리미엄":       "유튜브 프리미엄",
    "youtubepremium":       "유튜브 프리미엄",
    # 유튜브 프리미엄 라이트
    "유튜브프리미엄라이트": "유튜브 프리미엄 라이트",
    # 네이버플러스 멤버십
    "네이버플러스":         "네이버플러스 멤버십",
    "네이버플러스멤버십":   "네이버플러스 멤버십",
    "naverplus":            "네이버플러스 멤버십",
    "naverplusmembership":  "네이버플러스 멤버십",
    # iCloud
    "icloud":               "icloud",
    "아이클라우드":         "icloud",
    # 넷플릭스
    "netflix":              "넷플릭스",
    # 웨이브
    "wavve":                "웨이브",
    "wave":                 "웨이브",
    # 티빙
    "tving":                "티빙",
    # 스포티파이
    "spotify":              "스포티파이",
    # 멜론
    "melon":                "멜론",
    # Google One
    "googleone":            "Google One",
    "구글원":               "Google One",
    "구글드라이브":         "Google One",
    # Notion AI
    "notionai":             "Notion AI",
    "노션ai":               "Notion AI",
    "노션":                 "Notion AI",
    "notion":               "Notion AI",
    # 밀리의서재
    "밀리":                 "밀리의서재",
    "millie":               "밀리의서재",
    "밀리서재":             "밀리의서재",
    # 클래스101
    "class101":             "클래스101",
    "클래스101":            "클래스101",
    # 패스트캠퍼스
    "fastcampus":           "패스트캠퍼스",
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
            "cautions": []
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
        "cautions": info["caution"]                     # 이미 리스트
    }
