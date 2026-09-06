# 하루메이트 UX 레퍼런스 리서치 — 수요·벤치마크·가이드라인·뼈대 (2026-09-06)

> **목적:** v1.4「메이트」이후 개선 라운드의 근거 문서. (1) 발달장애인 수요/통계 → 니즈 도출, (2) 국내외 앱 벤치마크 → UI 패턴 추출, (3) Apple Assistive Access / W3C COGA / 학술 가이드 → 하루메이트 12원칙, (4) GitHub Apple HIG 스킬 평가, (5) IA 뼈대 + 니즈→기능→UI 매핑 + 우선순위.
> **읽는 순서:** §0 TL;DR → §5 뼈대 → §6 매핑표 → §7 우선순위. 근거가 필요할 때 §1~§4.
> **정직성 노트:** §8에 "찾지 못한 것"을 명시. 외부 표현 시 HANDOFF.md §9 가이드 준수.

---

## 0. TL;DR (5줄)

1. **수요는 "지시 없이 혼자 하루를 통과하는 것"**에 집중된다. 2021 실태조사: 전적 도움 필요 22.5%, 주돌봄자 78.6%가 부모(평균 56.6세), 미래 걱정 1위 "혼자 남겨짐" 33.4%. → 당사자 자립 + **보호자도 고령 → 보호자 UI도 접근성 대상**.
2. **근거 있는 개입은 시각 일과표(VAS) + 사진/비디오 단계 프롬프트.** 메타분석 2편 모두 유의 효과, 단 연구가 아동·여가에 편중 → **성인 자립생활 영역이 비어 있고, 그게 하루메이트 자리.**
3. **직접 경쟁/참조는 서울시복지재단 「보통의 하루」(2026.06~, 45명).** 알람 + 사진/NFC 인증 해제. 11월 효과 검증 예정. 우리는 여기에 "다음 할 일 시각화 + 에이전트 대화"가 추가된 형태.
4. **UI 뼈대는 Apple Assistive Access 를 표준으로 잡는다**: 루트 타일 ≤4, 아이콘+라벨 항상 쌍, 하단 고정 뒤로가기, 숨은 제스처 0, 시간제한 UI 0, 파괴적 동작 제거/2중 확인, 그리드·행 레이아웃 토글. 여기에 Brili/Routinery의 **실시간 카운트다운 자동 전진**, Choiceworks의 **감정·대기 보드**, CanPlan의 **사진 단계**를 얹는다.
5. **GitHub Apple HIG 스킬은 `dickwu/apple-design-skill`(Flutter 지원, 리뷰 모드)만 채택.** 단 HIG는 인지접근성 특화가 아니므로 §3의 12원칙을 **자체 스킬 `harumate-cognitive-a11y`** 로 만들어 `/ux-commit-check`에 붙이는 게 실효성 있음.

---

## 1. 수요·통계 → 니즈

### 1.1 국내 공식 통계

| 출처 | 수치 | 하루메이트 함의 |
|---|---|---|
| **2021 발달장애인 실태조사** (복지부·보사연, n=1,300 방문면접) | 모든 일상생활 도움 필요 **22.5%** (지적 21.3 / 자폐 30.5) · 의사소통 거의 불가 **18.4%** · 주돌봄자 부모 **78.6%**, 평균 **56.6세** · 미래 걱정 1위 "혼자 남겨짐" **33.4%**, 일상생활 지원·돌봄 21.7% · 본인이 주요 의사결정 **28.6%** vs 부모 50.4% · 외출 거의 매일 54.1% · 여가 TV 54.2%, 컴퓨터 19.2% | ① 약 1/5은 텍스트·음성 모두 어려움 → **픽토그램+TTS 이중화 필수** ② 보호자가 50대 후반 → **보호자 화면도 큰 글자·단순 위저드** ③ "혼자 남겨짐" 공포 → 앱의 가치 제안은 "지시 없이도 하루가 굴러간다" ④ 의사결정 주체가 본인인 비율 낮음 → **선택 기회를 UI에 심어야** (COGA: 자기결정) |
| **KODDI 인포그래픽 「나는 발달장애인입니다」** (2011 실태조사 기반, 오래됨) | 일상 타인 도움 필요 **80.4%** (시각 20.5 / 지체 13.6) · 어려움: 금전관리 90.3, 쇼핑 84.9, 식사준비 84.7, 교통수단 76.2, **전화사용 73.7** · 친한 친구 없음 60.5% · 보호자 우울 19.43 (의심 기준 16 초과) | ⑤ **전화조차 73.7%가 어려움 → 도움 요청은 1탭 (Action Blocks 방식)** ⑥ 식사준비 84.7% → 식사 그룹 단계 프롬프트 가치 ⑦ 보호자 우울 → 보호자 UI는 "관리 도구"가 아니라 "부담 경감 도구" 톤 |
| **2024 디지털정보격차 실태조사** (NIA) | 장애인 디지털정보화 **83.5%** (접근 96.5 / 역량 65.6 / 활용 80.0) · **장애 유형별 세분 없음** | ⑧ 기기 접근은 거의 해결, **역량이 병목** → 온보딩·튜토리얼이 기능만큼 중요 ⑨ 발달장애 세분 통계 부재 = 우리가 테스터 데이터로 채울 수 있는 빈칸 |
| **특수교사 197명 인식조사** (김창배, 2021, 발달장애연구) | 발달장애 학생 스마트폰 사용 **99% 긍정** · 요구: 사용법 교육 28.4%, **생활 활용 앱 개발 25.4%**, 사용 쉬운 스마트폰 22.3% | ⑩ 현장(특수교사)이 "생활 앱"을 명시적으로 요구 → 복지관·특수학교 전공과가 B2B 채널 |

### 1.2 국내 최신 연구·현장 (2025~2026)

| 출처 | 내용 | 함의 |
|---|---|---|
| **윤여경 (2025, KCI) 성인 발달장애인 30명 사용성 실험** | 문제: 복잡 메뉴, 추상 아이콘, 과도한 시각 자극. 개선 프로토타입 → 작업 완료율 **58.7% → 83.2%**, 오류 **4.1 → 1.6회**, 만족 **2.8 → 4.3** | **우리 검증 지표를 이 3개(완료율·오류·만족)로 통일**하면 국내 선행연구와 직접 비교 가능 |
| **서울시복지재단 「보통의 하루」** (법무법인 여온 협약, 2026.06~ 주거지원 참여자 45명, 11월 효과 검증) | 기상·복약·위생 시간 알람 → **사진 촬영 또는 NFC 태그로만 알람 해제**. 일부 이용자 기상 안정 → 출근 안정 | ① 국내 유일 직접 비교군. ② "행동 인증" 패턴은 검증 가능성 때문에 기관이 좋아함 → **완료 인증(사진/NFC) 옵션** 도입 가치 ③ 45명·11월 검증이라는 공공 벤치마크가 생김 → 우리 12명 테스트 결과를 같은 언어로 발표 가능 |
| **이화여대 성인 발달장애인 AI-AAC 요구분석** (조혜희 외) | 요구: 개인화, 쉬운 사용, 개인정보 보호, 다양한 상황 적응, 사회적 대화, 지역사회 참여 | 에이전트(v3) 방향과 일치. "사회적 대화" = 메이트 컨셉의 근거 |
| **스마트폰 상황학습 장기 지원** (발달장애인 10명, 거주지 사회활동) | 지원 기간에 따라 수행능력 지속 향상, 장애 정도 무관 | 장기 사용 데이터(리텐션)가 곧 효과 증거 → 이행률 로그 설계 |

### 1.3 해외 근거 (효과성)

| 출처 | 결과 | 함의 |
|---|---|---|
| **van Dijk & Gage (2018) VAS 메타분석**, 지적장애, 13편 SCD | 시각 일과표(VAS)는 독립 수행에 유의 효과. **모든 제시 양식(종이/디지털)·연령·환경에서 효과**, 조절변수는 교수 방식만 | 디지털 여부보다 **교수 방식(프롬프트 위계)**이 중요 → 앱 안에 최소-최대 프롬프트 단계(픽토 → TTS → 보호자 호출) 설계 |
| **Knight et al. (2015)** ASD VAS EBP 검토 / 터키 메타 (NAP .95) | 활동 일과표는 근거기반실제(EBP) | 외부 발표 시 "근거기반실제 기반 설계" 표현 가능 |
| **디지털 활동 일과표 체계적 문헌고찰** (17편, 58명) | 전 연령·전 환경 효과. **단 연구가 유아·여가에 편중, 성인 자립생활 연구 부족** | **성인 자립 영역 = 연구 공백 = 하루메이트 포지셔닝 + 논문 기회** |
| **비디오 프롬프팅 메타분석** (ASD, 17편 54명) | 일상생활기술 습득에 중간 효과, ID 동반 여부 무관 | 단계 카드에 **사진/짧은 영상 슬롯** 추가 근거 |
| **AT 체계적 문헌고찰 2024** (ASD/ID, 18편) | 교통·이동, 가정, 지역사회에서 모바일 앱 프롬프트 효과. 18편 중 15편 사회참여 개선 | 외출 거의 매일 54.1%와 결합 → **"나가기 전 체크" 루틴**이 고가치 |
| **Mechling (2011)** | 성인 ID 컴퓨터 41%, 휴대폰 27.7% (오래됨) | 격차는 좁혀졌지만 "쓸 수 있는 앱"은 여전히 부족 |

### 1.4 도출된 니즈 (3주체)

**당사자**
- N1 **예측성**: "지금 뭐 하고, 다음에 뭐 하지"가 항상 한 화면에
- N2 **시간의 시각화**: 숫자가 아닌 줄어드는 형태로
- N3 **지시 없는 완수**: 단계별 사진/픽토/TTS, 프롬프트 위계
- N4 **실수 안전**: 삭제·되돌리기 불가 동작 없음, 언제든 뒤로
- N5 **읽기 없이 이해**: 아이콘+라벨 쌍, 픽토(ARASAAC), 읽어주기
- N6 **자극 최소**: 차분한 색, 느린 모션, 알림 빈도 조절
- N7 **성취 피드백**: 완료 시 즉각·따뜻한 확인 (과도한 게이미피케이션 X)
- N8 **1탭 도움 요청**: 전화가 어려운 73.7%를 위한 SOS/전화/문자 원탭
- N9 **선택권**: 순서 바꾸기, 활동 고르기 (자기결정)
- N10 **사회적 대화**: 메이트 톤의 에이전트 (외로움·친구 없음 60.5%)

**보호자 (평균 56.6세)**
- G1 설정이 위저드로 5분 안에 끝남, 큰 글자 기본
- G2 원격으로 "오늘 잘 진행되는지" 한 눈에 (이행률)
- G3 템플릿(식사/신체/휴식/일과 4그룹) 로 빠른 시작
- G4 부담 경감 톤: 감시가 아닌 "덜 불러도 되는" 도구
- G5 위급 알림 수신

**기관 (복지관·주거지원·전공과)**
- I1 다인 이행률 대시보드 (Streamlit B2B 이미 존재)
- I2 검증 가능한 데이터 (완료 인증, 완료율/오류/만족 지표)
- I3 개인정보 최소 수집 (사진 인증은 온디바이스 처리 후 해시만)

---

## 2. 레퍼런스 앱 벤치마크

### 2.1 해외

| 앱 | 대상 | 핵심 UI 구조 | 타이머 | 보호자 모드 | 가격 | 가져올 것 / 피할 것 |
|---|---|---|---|---|---|---|
| **Tiimo** (2025 Apple iPhone App of the Year) | 10대~성인 ND(ADHD/ASD) | 시간순 타임라인, 아이콘+색 코딩, **지난 항목 회색 처리**, 접기/펼치기 | 차분한 원형 카운트다운, Dynamic Island | 제한적(자기주도) | 무료/프리미엄 $54/yr | ✅ 느린 모션·회색화·"강한 기본값+선택적 조정" 철학 · ❌ 설정 밀도 높음, 읽기 능력 전제 |
| **Brili Routines** | 아동·성인 ADHD/ASD | **루틴을 실시간으로 "함께 실행"**: 단계 카드 + 진행바 + 카운트다운, 자동 다음 단계 | 시각 시계, 능동 카운트다운 | ✅ 보상·히스토리 | $7.99/mo | ✅ 자동 전진, 단계 스킵 · ❌ "째깍" 압박감(사용자 리뷰), 구독 |
| **Routinery** (루티너리) | 성인 | "샤워 10분 → 커피 5분" 시퀀스, **앱이 다음을 결정, 사용자는 따르기만** | 단계별 카운트다운 | ✗ | 구독 | ✅ 결정 부담 제거 철학 (task initiation) |
| **Choiceworks** | 유아~학령기 | **일과 보드 + 감정 보드 + 대기 보드** 3종 | 내장 | ✅ | Lite 무료 / ~$15 | ✅ 감정·대기 보드 (전환 불안 대응) · ❌ 아동용 시각 |
| **First Then Visual Schedule HD** | 유아~중기 | **"먼저–그다음" 2칸** → 체크리스트까지 확장 뷰 | 단계별·전체 | ✅ | $14.99 | ✅ 2칸 뷰가 가장 낮은 인지 부하 |
| **Goally** | 2~8세 | 전용 디바이스+앱, 한 번에 한 과제, 시각 타이머, 포인트 | ✅ | ✅ (부모 앱 분리) | 디바이스 | ✅ **당사자 기기/보호자 기기 분리** 모델 · ❌ 아동 전용 |
| **CanPlan** | 전 연령 | **사진 기반 단계**, 오프라인, 음성 프롬프트 | 시간 음성 프롬프트 | 전체 설정 필요 | 무료 | ✅ 사진 단계 + 오프라인 · ❌ 설정 부담, 밋밋한 UI |
| **Visual Schedule Planner** | 학령기+ | 일/주/월, 중첩 활동, 커스텀 이미지·오디오 | ✅ | ✅ iCloud | $14.99 | ✅ 오디오 커스텀(보호자 목소리) |
| **Boardmaker 7** | 학교·임상 | PCS 심볼 74,000+ | ✅ | 표준화 | $99/yr | 참조만 (심볼 표준) |

### 2.2 국내

| 앱/서비스 | 주체 | 기능 | 우리와 관계 |
|---|---|---|---|
| **보통의 하루** (2026) | 서울시복지재단 + 법무법인 여온 | 기상·복약·위생 알람, **사진/NFC 인증 해제**, 주거지원 45명 | **직접 비교군.** 우리는 인증 + 시각 일과표 + 에이전트. 11월 검증 결과 추적 필수 |
| **나의 AAC** (2024 개편) | NC문화재단 | 심볼 10,000+ (KAAC·커뮤니사인·NC) | 심볼 세트 참조. ARASAAC 대신 국내 심볼 라이선스 검토 |
| **스마트AAC** | 경기도재활공학서비스연구지원센터 + 삼성 | 그림형/문자형/키보드/상징 제작, 무료 | 의사소통 보완 연동 후보 |
| **채비넷** (2021) | — | 발달장애 자녀 부모 평생설계 교육 | 보호자 채널·파트너 후보 |
| **Apple Assistive Access** (iOS 17~, 26에서 3rd-party scene) | Apple | 인지장애용 시스템 모드: 대형 컨트롤, 그리드/행, 하단 뒤로가기 | **UI 표준으로 채택** (§3) |
| **Google Action Blocks** | Google | 홈 화면 1탭 위젯(전화·사진·불 끄기) | SOS/전화 1탭 패턴 |

### 2.3 추출된 UI 패턴 → 하루메이트 현재 상태

| # | 패턴 | 채택 앱 | 하루메이트 현재 | 조치 |
|---|---|---|---|---|
| P1 | "지금 / 다음" 2칸 | First-Then, Tiimo | `step_card` kiosk single-focus 존재 | 사용자 홈 상단을 **2칸 고정**으로 승격 |
| P2 | 실시간 카운트다운 + 자동 전진 | Brili, Routinery | 타이머 화면 별도 | 활동 카드 안에 원형 타이머 내장, 완료 시 다음 카드로 자동 스크롤 (압박 없는 느린 애니) → M4 모션 |
| P3 | 지난 항목 회색화 | Tiimo | 없음 | 오늘 타임라인에 적용 (1시간) |
| P4 | 사진/영상 단계 | CanPlan, 비디오 프롬프팅 근거 | 텍스트 단계 | step에 이미지 슬롯 + 보호자 촬영 업로드 |
| P5 | 감정 보드 · 대기 보드 | Choiceworks | 없음 | "도움" 탭에 3표정 감정 버튼 + "기다리는 중" 화면 |
| P6 | 완료 인증 (사진/NFC) | 보통의 하루 | 없음 | 옵션 기능. 기관 모드에서만 기본 ON |
| P7 | 보상/히스토리 | Brili, Goally | 없음 | **가벼운 히스토리만** (스티커 X, "이번 주 7일 중 6일" 문장형) |
| P8 | 보호자·당사자 화면 분리 | Goally, Assistive Access | HomeUser / HomeCoordinator 분리 ✅ | 유지. 보호자 화면도 큰 글자 기본 |
| P9 | 그리드 / 행 레이아웃 토글 | Assistive Access | normal/simple/kiosk 3모드 | simple 모드에 **grid/row 토글** 추가 |
| P10 | 하단 고정 뒤로가기 | Assistive Access, ACM 2024 | 앱바 상단 뒤로 | 사용자 모드 전 화면 **하단 큰 뒤로 버튼**으로 이동 |
| P11 | 1탭 액션 | Action Blocks | SOS 버튼 ✅ | 전화·문자·"도와줘" 3버튼으로 확장, 홈 위젯 |
| P12 | 스크롤 대신 위/아래 버튼 | ACM 2024, van Calis 2025 | 스크롤 | simple/kiosk 모드에서 페이지 버튼 옵션 |
| P13 | 읽어주기 + 단어 하이라이트 | ACCESS+, van Calis | TTS ✅ | 카드 탭 시 읽어주기 + 하이라이트 |
| P14 | 온보딩 튜토리얼 (영상·단계) | 다수 | 3단계 온보딩 ✅ | "한 번 따라해보기" 실습 단계 추가 |

---

## 3. 디자인 가이드라인 → 하루메이트 12원칙

### 3.1 참조한 가이드라인

- **Apple Assistive Access 3원칙** (WWDC23): ① Streamlined task completion ② Error prevention & recovery ③ Consistency
- **WWDC25 「Customize your app for Assistive Access」** 구체 지침: 핵심 기능 1~2개만 루트에 · 옵션 수 최소 · **숨은 제스처·중첩 UI 금지, 눈에 보이는 큰 컨트롤** · **시간 제한 UI 금지** (자동 사라짐/타임아웃 재설계) · 여러 선택을 한 화면에 X → **단계별 흐름** · 파괴적 동작은 **제거 또는 2회 확인** · **아이콘+라벨 항상 쌍**, 내비게이션 타이틀에도 아이콘 · 그리드/행 레이아웃 자동 준수
- **W3C COGA 「Making Content Usable」 8 목표**: 이해 · 찾기 · 명확한 언어 · 실수 방지/복구 · 집중 · 기억 의존 X · 도움/지원 · 개인화. 일정 앱 관련 사용자 요구: "시작 전 무엇이 필요한지 알려줘", "리마인더 빈도를 내가 조절", "기호를 텍스트 위에"
- **Google Material 인지접근성 사례**: 모든 요소를 고대비로 하면 "시각적으로 시끄러워" 오히려 행동 불가 → **레이아웃·크기·형태로 위계**, 대비는 핵심 액션에만
- **ACM 2024 「Advancing Accessible Interfaces」(ID 대상 실증)**: **콘텐츠 지향 내비 > 메뉴 지향** · 햄버거 메뉴 제거 · 버튼을 큰 블록으로 · 뒤로/CTA 하단 고정 · 스크롤 버튼 · 온보딩으로 새 패턴 학습 가능 · WCAG는 인지접근성엔 불충분
- **van Calis et al. (2025, MID/저문해)**: 알아볼 수 있는 삽화(다양성 반영), 플랫폼 이름도 이해 가능하게, 읽어주기/따라읽기, 진행 표시, **깜빡이는 버튼은 짜증**, 차분한 팔레트
- **SARAL 13 가이드라인 (CSCW 2021, 저문해)**: 다중 모달, 미니멀, 시각 단서, 전문용어 X, 화면 내·간 정보 분할, 선형 내비, 짧은 도움말, 오디오·비디오 튜토리얼, 문화 반응 디자인
- **Tiimo 감각 친화 원칙**: 느린 모션, 완료 회색화, 소리/햅틱 전부 토글, "강한 기본값 + 표적 조정"

### 3.2 하루메이트 12원칙 (변경 금지 후보 — JY 컨펌 후 HANDOFF §4에 편입)

| # | 원칙 | 출처 | 검사 방법 (`/ux-status` grep 후보) |
|---|---|---|---|
| R1 | **루트 화면 타일 ≤ 4** (당사자 모드) | AA WWDC25 | 홈 위젯 카운트 |
| R2 | **아이콘 + 라벨 항상 쌍**, 아이콘 단독 버튼 0 | AA, COGA | `IconButton(` without tooltip/label grep |
| R3 | **하단 고정 뒤로가기/홈**, 상단 앱바 뒤로 X (당사자 모드) | AA, ACM 2024 | `AppBar(leading:` grep |
| R4 | **숨은 제스처 0** (스와이프 삭제·롱프레스 전용 기능 금지) | AA | `Dismissible(`, `onLongPress` grep |
| R5 | **시간 제한 UI 0**: 자동 닫힘 스낵바·토스트 대신 확인 버튼 | AA, COGA 4 | `SnackBar(duration` grep |
| R6 | **파괴적 동작은 당사자 모드에서 제거**, 보호자 모드는 2회 확인 | AA | `delete`/`remove` in user screens |
| R7 | **한 화면 한 결정**: 복수 선택은 단계 분리 | AA, SARAL G6 | 설정 화면 폼 필드 수 |
| R8 | **콘텐츠 지향 내비**: 햄버거·탭바 중첩 대신 큰 블록 버튼 | ACM 2024 | `Drawer(` grep |
| R9 | **스크롤 선택제**: simple/kiosk에서 페이지 버튼 제공 | ACM 2024, van Calis | 모드별 ListView 래핑 |
| R10 | **다중 모달**: 픽토 + 텍스트 + 읽어주기, 카드 탭=읽기 | COGA 1·3, SARAL G1 | step에 image + tts 필드 |
| R11 | **차분한 위계**: 대비는 주 CTA 1개에만, 깜빡임·그라데이션 0, 모션 ≥300ms ease | Material, Tiimo, van Calis | 그라데이션 0건 ✅ 유지 |
| R12 | **리마인더는 사용자 조절**: 빈도·소리·햅틱 각각 토글 | COGA 7, Tiimo | 설정에 3 토글 존재 |

→ v1.4 완료 항목(그라데이션 0, 이모지 0, 클러스터 카피 0)은 R11의 부분집합. **R1~R9 가 다음 라운드 핵심.**

---

## 4. GitHub Apple HIG 스킬 평가 ("apple design 하네스")

| 저장소 | 성격 | Flutter | 우리 적용 | 판단 |
|---|---|---|---|---|
| **dickwu/apple-design-skill** | HIG 53문서 기반 **리뷰어** (Design Review / Improvement / 접근성 감사 모드). Flutter·RN·Electron 명시 지원 | ✅ | `claude install-skill` 후 `/ux-commit-check`에 "HIG 리뷰" 단계 추가 | **채택** |
| tristan-mcinnis/apple-hig-designer-skill-2026 | SwiftUI **코드 생성**용, SF 타이포·8pt 그리드·Liquid Glass, MIT | ✗ | 타이포 스케일·터치 타겟 44pt·8pt 그리드 표만 HaruTokensV2 주석에 인용 | 참조만 |
| NutshellEngineering/apple-design-skill | HIG 원칙 요약 | 부분 | 중복 | 보류 |
| axiaoge2/apple-hig-designer, t2murata gist, nexu-io/open-design apple-hig | 유사 변종 | — | — | 보류 |

**한계:** Apple HIG는 일반 사용자 대상. 인지접근성(Assistive Access 지침, COGA)은 HIG 본문에 얕게만 있음. **→ §3.2 12원칙을 `.claude/skills/harumate-cognitive-a11y/SKILL.md`로 자체 작성**해서 dickwu 리뷰와 병행하는 것이 실효성 있음. 또한 HIG의 최신 iOS 시각(Liquid Glass 등)은 「메이트」warm coral/MUJI 톤과 별개 — **구조·크기·타이포 규칙만 차용, 스타일은 차용 X**.

---

## 5. IA 뼈대 제안 — "2계층 · 3모드 · 4타일"

```
┌─ 당사자 앱 (사용자 모드: normal / simple / kiosk) ─────────────────────┐
│  루트 = 4 타일 (grid ⇄ row 토글, Assistive Access 준수)                 │
│   ① 지금 할 일   ② 오늘 일과   ③ 도움   ④ 이야기(메이트)               │
│                                                                        │
│  ① 지금  = First-Then 2칸 (지금 | 다음) + 원형 카운트다운               │
│           + 단계 카드(픽토·사진·읽어주기) + 「다 했어요」 큰 버튼        │
│           + (옵션) 완료 인증: 사진 / NFC                                │
│  ② 오늘  = 시간순 타임라인, 지난 항목 회색, 4그룹 컬러 유지             │
│           simple/kiosk: 위/아래 페이지 버튼, 스크롤 선택제              │
│  ③ 도움  = 1탭 3버튼 (전화 / 문자 / 도와줘=SOS)                        │
│           + 감정 보드 3표정 + 「기다리는 중」 화면                       │
│  ④ 이야기 = 에이전트 대화(v3), 음성 우선, agent_plan_card 로 계획 투명화 │
│                                                                        │
│  공통: 하단 고정 [뒤로] [홈] · 아이콘+라벨 · 삭제 없음 · 타임아웃 없음   │
├─ 보호자 앱 (코디네이터 모드) ──────────────────────────────────────────┤
│  설정 위저드 5단계 (템플릿 4그룹 → 시간 → 사진 → 알림 → 완료)           │
│  오늘 이행 현황 1화면 (문장형: "오늘 6개 중 4개 했어요")                │
│  위급 알림 수신 · 큰 글자 기본 (56.6세) · 2회 확인 삭제                 │
├─ 기관 대시보드 (Streamlit B2B, 기존) ──────────────────────────────────┤
│  다인 이행률 · 완료율/오류/만족 지표 · 익명 통계                         │
└────────────────────────────────────────────────────────────────────────┘
```

**현재 10 화면과 매핑:** HomeUser → ①②, Timer → ① 내장, User/Agent → ④, SOS/Profile → ③, HomeCoordinator/Coordinator → 보호자, Onboarding → 위저드, YouTube → ②의 휴식 그룹 안으로 (루트에서 제거 = R1). 화면 수는 줄지 않아도 **루트 노출은 4개로 강제.**

---

## 6. 니즈 → 기능 → UI 매핑 (살 붙이기)

| 니즈 | 기능 | UI 결정 | 근거 |
|---|---|---|---|
| N1 예측성 | 지금/다음 2칸 고정 | 홈 상단 2카드, 다음은 60% 불투명 | First-Then, VAS 메타 |
| N2 시간 시각화 | 원형 카운트다운 카드 내장 | 숫자 보조, 색 변화 없음(불안 방지), 느린 감소 | Brili 리뷰(압박), Tiimo |
| N3 지시 없는 완수 | 단계 카드 + 프롬프트 위계 | 1차 픽토·사진 → 2차 탭하면 읽어주기 → 3차 60초 무응답 시 "도움 부르기?" 제안(자동 실행 X) | VAS 메타(교수방식), 비디오 프롬프팅 |
| N4 실수 안전 | 당사자 모드 삭제·편집 제거 | 편집은 보호자 모드만, 뒤로 항상 하단 | AA, COGA 4 |
| N5 읽기 없이 이해 | 픽토 + 라벨 + TTS | ARASAAC 또는 국내 심볼(나의AAC 라이선스 확인), 아이콘 단독 0 | AA, ACCESS+ |
| N6 자극 최소 | 감각 설정 3토글 | 소리/햅틱/애니 각각, 기본 OFF 아님 "약하게" | Tiimo, COGA 8 |
| N7 성취 피드백 | 완료 확인 + 주간 문장 | "다 했어요" → 체크 애니 400ms + 한 문장 TTS. 스티커·점수 X | Brili/Goally 반례 |
| N8 1탭 도움 | 도움 탭 3버튼 + 홈 위젯 | 전화 대상은 보호자가 1명 고정, 확인 없이 즉시 | Action Blocks, 전화사용 73.7% |
| N9 선택권 | 활동 순서 바꾸기·고르기 | 보호자가 "선택 가능" 표시한 활동만 2지선다 카드로 | COGA, 자기결정 28.6% |
| N10 사회적 대화 | 메이트 에이전트 | 음성 우선, 답변 3문장 이하, plan card로 "내가 뭘 할지" 보여주기 | 이화여대 AAC 요구, v3 |
| G1 쉬운 설정 | 5단계 위저드 + 4그룹 템플릿 | 한 화면 한 결정, 진행 표시 | AA, van Calis |
| G2 원격 확인 | 이행 현황 1화면 | 문장형 요약 + 타임라인, 그래프 최소 | 부모 56.6세 |
| G4 부담 경감 | 톤 가이드 | "확인하세요" X → "오늘도 잘 지나가고 있어요" | 보호자 우울 19.43 |
| I2 검증 데이터 | 완료 인증 옵션 + 3지표 로그 | 사진은 온디바이스 판정 후 해시·시각만 서버 | 보통의 하루, 윤여경 지표 |

---

## 7. 우선순위 (기존 Pending Gates 병합)

### P0 — 구조 (2주, 시각 임팩트 + 근거 최대)
1. **루트 4타일 + grid/row 토글** (R1, P9) — 2일
2. **하단 고정 뒤로/홈** 당사자 모드 전 화면 (R3, P10) — 2일
3. **지금/다음 2칸 + 카드 내장 카운트다운** (P1, P2) — 3일 ← 기존 Gate 5 "M4 모션" 흡수
4. **아이콘+라벨 쌍 강제 + 작은 카드 이모지 → IconData** (R2) — 0.5일 ← 기존 Gate 3
5. `buildAppTheme()` 전역 ElevatedButton V2 (기존 Gate 2) — 0.5일
6. **`.claude/settings.json` 박기** (기존 Gate 1, JY 직접) — 5분

### P1 — 근거 기반 기능 (3주)
7. 단계 카드 사진 슬롯 + 보호자 촬영 업로드 (P4)
8. 도움 탭 3버튼 + 감정 보드 (P5, P11)
9. 지난 항목 회색화 + 스크롤 선택제 (P3, P12)
10. 감각 설정 3토글 + 스낵바 타임아웃 제거 (R5, R12)
11. ARASAAC/국내 심볼 번들 + 라이선스 표기 (기존 Gate 4)
12. `harumate-cognitive-a11y` 스킬 작성 + dickwu 스킬 설치 → `/ux-commit-check` 연동

### P2 — 검증·차별화 (출시 후)
13. 완료 인증 옵션 (사진/NFC) — 기관 모드 기본 ON
14. 보호자 위저드 5단계 리뉴얼
15. 3지표(완료율·오류·만족) 로깅 → 테스터 12명 결과 → 「보통의 하루」 11월 검증과 같은 언어로 정리
16. 에이전트 plan card 통합 (v3)

**검증 설계:** 윤여경(2025) 3지표 + 이행률. 사전(v1.3.3)/사후(v1.5) 비교. 복지관 테스터 12명 × 14일. 결과는 HANDOFF §9 표현 가이드 안에서만 외부 발표.

---

## 8. 찾지 못한 것 / 한계 (정직성)

- **발달장애인 스마트폰 보유·앱 사용 국내 공식 통계 없음.** 2024 NIA 조사는 장애 유형별 세분 없음. 2021·2023 실태조사 보도자료에도 정보기기 항목 없음 (원문 보고서 hwpx 확인 필요).
- **발달장애인이 "가장 많이 쓰는 앱" 랭킹 데이터 없음.** 스토어는 장애 여부를 모름. 학술·현장 문헌상 실제 사용은 AAC 앱, 유튜브, 카카오톡, 알람/타이머가 반복 언급되지만 정량 근거는 아님.
- **효과성 근거는 아동·여가 편중.** 성인 자립생활 앱의 RCT 수준 근거는 국내외 모두 없음 → 우리 결과가 그 자체로 기여.
- **「보통의 하루」 상세 UI 미확인.** 보도자료만 존재. 11월 검증 발표 추적 필요.
- Apple Assistive Access 3rd-party scene은 **iOS 26 SwiftUI 전용** → Flutter에서는 API 채택 불가, **디자인 규칙만 이식** (UISupportsFullScreenInAssistiveAccess 키는 Info.plist에 추가 가능).

---

## 9. 출처

**통계·정책**
- 보건복지부, 2021년 발달장애인 실태조사 결과 발표 — https://www.mohw.go.kr/board.es?mid=a10503000000&bid=0027&act=view&list_no=372831
- 한국장애인개발원, 인포그래픽 「나는 발달장애인입니다」 — https://www.koddi.or.kr/data/research01_view.jsp?brdNum=7401046
- 2024 디지털정보격차 실태조사 결과 (korea.kr) — https://www.korea.kr/briefing/pressReleaseView.do?newsId=156681128 · 더인디고 정리 https://theindigo.co.kr/archives/61549
- 서울시복지재단 「보통의 하루」 (천지일보 2026-09-02) — https://www.newscj.com/news/articleView.html?idxno=3429499

**국내 연구**
- 윤여경 (2025), 성인 발달장애인의 디지털 접근성 향상을 위한 모바일 앱 디자인 연구 (KCI) — https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003252913
- 김창배 (2021), 특수교사의 발달장애 학생 스마트폰 사용에 대한 인식 — https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002793389
- 조혜희 외, 성인발달장애인 대상 AI 기반 AAC 시스템 요구 분석 — https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003177671

**해외 근거**
- van Dijk & Gage (2018), VAS meta-analysis (ID) — https://doi.org/10.3109/13668250.2018.1431761
- Kļaviņa et al. (2024), AT for practical skills in ASD/ID systematic review — https://pmc.ncbi.nlm.nih.gov/articles/PMC11590154/
- Hammond, Systematic Review of Digital Activity Schedule Use — https://scholarsarchive.byu.edu/cgi/viewcontent.cgi?article=11562&context=etd
- Advancing Accessible Interfaces (ACM 2024) — https://dl.acm.org/doi/full/10.1145/3696593.3696613
- van Calis et al. (2025), Inclusive digital platforms MID/LL — https://doi.org/10.1016/j.chbr.2025.100617
- Srivastava et al. (CSCW 2021), SARAL guidelines — https://www.shivanikapania.com/assets/cscw2021paper.pdf

**가이드라인**
- Apple, Assistive Access developer doc — https://developer.apple.com/documentation/accessibility/assistive-access
- WWDC25 Customize your app for Assistive Access — https://developer.apple.com/videos/play/wwdc2025/238/
- WWDC23 Meet Assistive Access (notes) — https://wwdcnotes.com/documentation/wwdc23-10032-meet-assistive-access/
- Assistive Access 레이아웃 선택 — https://support.apple.com/en-mz/guide/assistive-access-iphone/dev683243feb/ios
- W3C, Making Content Usable for People with Cognitive and Learning Disabilities — https://www.w3.org/TR/coga-usable/
- Google Action Blocks (ASSETS 2020) — https://dl.acm.org/doi/fullHtml/10.1145/3373625.3418043
- Tiimo, Sensory-friendly design — https://www.tiimoapp.com/resource-hub/sensory-design-neurodivergent-accessibility

**벤치마크**
- Spectrum Unlocked, Best Visual Schedule Apps (2026) — https://www.spectrumunlocked.com/blog/best-visual-schedule-apps
- Autisable, VizyPlan vs Goally/Choiceworks/Tiimo — https://autisable.com/blog/vizyplan-vs-goally-choiceworks-and-tiimo-comparing-visual-schedule-apps-for-autism/
- Brili — https://brili.com/ · Routinery — https://www.routinery.app/blog/best-routines-planner-apps
- 미디어생활, 장애인을 위한 반려앱 20 — https://www.imedialife.co.kr/news/articleView.html?idxno=53263

**GitHub 스킬**
- dickwu/apple-design-skill — https://github.com/dickwu/apple-design-skill
- tristan-mcinnis/apple-hig-designer-skill-2026 — https://github.com/tristan-mcinnis/apple-hig-designer-skill-2026
- NutshellEngineering/apple-design-skill — https://github.com/NutshellEngineering/apple-design-skill
- awesome-claude-code issue #747 (HIG skills 모음) — https://github.com/hesreallyhim/awesome-claude-code/issues/747
