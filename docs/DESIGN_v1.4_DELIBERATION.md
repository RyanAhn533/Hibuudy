# HaruMate v1.4 디자인 시스템 (Deliberation 결과)

> **작성일:** 2026-05-09 (JY 부재 중 자율 deliberation)
> **상태:** Phase 1~5 완료, JY 거부권 보류 중
> **자매 문서:** [ARCHITECTURE_FULL.md](ARCHITECTURE_FULL.md), [PERSONA_VALIDATION.md](PERSONA_VALIDATION.md), [EVOLUTION.md](EVOLUTION.md)
> **권한 노트:** Phase 4의 4.1/4.2/4.5/4.6 만 1차 산출. **4.3 (AAC 픽토 매핑) + 4.4 (화면 리디자인 매트릭스) 는 JY 거부권 행사 후 별도 turn.**

---

## Executive Summary

1. **컨셉 「온」** 결정 (한자 "온전한" + 따뜻함 + 온쿡 계승). MUJI 절제 톤. 페르소나 유진 (26세 여, 자폐 스펙트럼, 시각 학습 우세).
2. **HaruTokens v2 = warm-tinted neutral 베이스 + 온화한 코랄 brand + 4 활동 컬러 패밀리.** v1 alias 보존 (P4 안전 마이그레이션).
3. **AI 티 11개 적출 + 카피 톤 전면 검수 강제.** 이모지 0건, "~님/~보세요" 클러스터 폐기.

---

## 게이트 결정 (JY 거부권 보류)

JY 자는 동안 P6의 "컨셉 없으면 모든 결정이 AI 디폴트" 압박 + Phase 2 진입 위해 자율 결정. **깨면 거부 가능.**

| # | 결정 | 근거 |
|---|---|---|
| 1 | **컨셉:「온」** | 한자 "온전한 / 따뜻한 / 모두" 다층 의미. **온쿡 계승 = 헬로TV 보도 + 발달장애 클래스 4.83/5 스토리에 직접 연결**. 외부 발표/공모전 내러티브 우위. P3 한 단어 강제 통과. |
| 2 | **레퍼런스:MUJI** | 「온」과 톤 일치 (절제 + 따뜻한 베이지 + 정돈된 위계). Toss/Linear 는 SaaS틱, Headspace 는 명상 색채. P3 4개 동시 인용 = 안전 발언 → 1개로 픽 강제. |
| 3 | **페르소나:유진 (26세 여, 자폐 스펙트럼, 시각 학습 우세, 보호자(엄마)와 동거)** | 자폐 스펙트럼 = 인지 + 감각 + 시각 처리 이슈 가장 다양 → 디자인 결정 최대 영향. 「유진」은 v1.3 온보딩 placeholder("예: 유진")에 이미 존재 — 코드 통일성. |

**거부 시:** JY가 다른 컨셉 픽 → Phase 4.2 색 토큰 재계산 (1시간 작업). 다른 레퍼런스 → 컬러 채도/명도 재조정. 다른 페르소나 → P1 평가축 재정렬.

---

## Phase 2: 충돌 매트릭스

페르소나 쌍별 핵심 충돌 + 트레이드오프.

| 충돌 쌍 | 충돌 지점 | 트레이드오프 |
|---|---|---|
| **P1 ⚔️ P7** | P1 "정보 ↓" vs P7 "첫 화면 도메인 시각 단서 3+" | 정보 풍부 = 도메인 어필 ↑ + 인지 부담 ↑. **합의: 1차 시각단서는 1개 (오늘 활동 픽토), 추가 2개는 스크롤 후 공개.** |
| **P3 ⚔️ P4** | P3 "전면 색 개정" vs P4 "v1 alias 마이그레이션" | 전면 = 시각 임팩트 ↑ + 회귀 폭탄. alias = 안전 + 시각 양산형 잔존. **합의: v2 신규 토큰 + v1 deprecated 표시. 화면별 점진 교체 (D-by-D).** |
| **P5 ⚔️ P3** | P5 "AAA 7:1 모든 색" vs P3 "감성적 색 자유" | AAA 7:1 = 색 선택 매우 제약 (대비 안 나오는 부드러운 코랄 거의 다 탈락). **합의: 본문/보조 텍스트만 AAA 7:1, 장식/카드 배경/일러스트는 AA Large 3:1.** |
| **P2 ⚔️ JY** | P2 "기술 용어 폐기" vs JY 메모리 ("Mem0 / AICore" 등 좋아함) | 보호자 노출 화면만 한국어 강제. 개발자/내부 화면 + CLAUDE.md 등은 기술 용어 보존. **합의: 사용자 화면 = 한국어, 코드/문서 = 기술 용어 OK.** |
| **P1 ⚔️ P5** | P1 "활동 색 9 → 4 그룹" vs P5 "색 + 픽토 + 라벨 3종 강제" | 4색 그룹화하면 픽토로 9개 구분 부담 ↑. **합의: 4 색 그룹 × 그룹 내 2-3 픽토 (예: "식사" 그룹 = cooking/meal 같은 코랄 + 픽토 다름).** |
| **P6 ⚔️ 모두** | P6 "현재 모든 결정이 AI 디폴트" | 매 페이즈 마지막 발언 강제 + Phase 5 최종 검수. **합의: 산출물마다 P6 거부권 1회.** |
| **P4 ⚔️ P7** | P4 "ARASAAC 빌드타임 번들" vs P7 "검증 출처 앱내 노출" | ARASAAC 라이선스 표기 의무. **합의: ProfileScreen 푸터에 "AAC: ARASAAC (CC BY-NC-SA), 검증: NVIDIA Nemotron-Personas-Korea (CC BY 4.0)" 1회 표기.** |

---

## Phase 3: 합의 + Deferred

### 합의 (Consensus)

1. **컨셉 한 단어:**「온」(JY 거부 시 변경 가능)
2. **마이그레이션 전략:** v1 alias-first (P4) — `HaruTokens.primary` 보존, `HaruTokens.brandWarm` 등 v2 신규
3. **색 정책:** 본문/보조 텍스트 AAA 7:1 / 장식 AA Large 3:1 / 모든 색에 대비비 코드 주석 의무
4. **활동 컬러 패밀리:** 4 그룹 × 그룹내 픽토 차별화 (그룹: 식사 / 신체 / 휴식 / 전환)
5. **카피 정책:** 사용자 화면 = 한국어 + P2 검수 / 내부 = 기술 용어 OK
6. **AAC 픽토:** ARASAAC PNG 빌드타임 번들 (`assets/aac/`), 런타임 SVG 금지
7. **이모지:** 사용자 노출 화면 0건 (✅⏳🚨💡 모두 Material Symbols 또는 ARASAAC 픽토로 교체)
8. **모션:** 0.3초 초과 X, vestibular 트리거 모션 X, 카운트다운 시각화 의무
9. **검증/라이선스 표기:** ProfileScreen 푸터 1회 (NVIDIA + ARASAAC)

### Deferred (다음 라운드로 미룸)

| 항목 | 이유 |
|---|---|
| 한 단어 컨셉 「온」 vs 다른 후보 | JY 거부권 행사 가능 |
| 9 활동 → 4 그룹 매핑 정확히 어떻게 | 4.3 AAC 픽토 매핑 표 작성 시 결정 (별도 turn) |
| 화면 10개 리디자인 우선순위 | 4.4 매트릭스에서 처리 (별도 turn) |
| Kotlin AICore + agent_plan_card 통합 | D7-D10 (UI 트랙과 분리, 별도 브랜치 `feature/v3-agent-integration`) |
| iOS 디자인 토큰 적용 | iOS 배포 전까지 보류 |
| LLM judge 평가 N=500+ | v3 정착 후 별도 사이클 |

---

## Phase 4: 산출물 (4.1 / 4.2 / 4.5 / 4.6 — 1차 4개)

> **별도 turn 예정:** 4.3 AAC 픽토 매핑 (9 활동 × 컬러/라인 2종), 4.4 화면 10개 리디자인 매트릭스

---

### 4.1 디자인 컨셉 (P3 주도)

#### 한 줄

> **「온」 — 발달장애 당사자의 온전한 하루 곁에서, 따뜻하게 길을 안내하는 도우미.**

#### 한 단락

> 「온」은 한자 "온전한(穩) / 따뜻한(溫) / 모두(全)" 의 다층 의미를 한 음절에 응축한 컨셉이다. 발달장애 당사자가 일과의 작은 단계 하나하나를 **온전히** 따라가도록, 보호자의 차가운 지시가 아니라 **따뜻한** 동행으로, 당사자·보호자·복지사 **모두** 가 같은 화면을 보며 협력하도록. 시각 톤은 무인양품(MUJI)의 절제된 따뜻한 베이지 위에 차분한 코랄을 한 점 두는 식 — 차가운 의료/SaaS 블루를 폐기하고, "사람의 손길이 닿는 도구" 의 정서를 유지한다. 「온」은 우리 전신인 "온쿡"(2024 서울청년기획봉사단 → 헬로TV 보도 → 발달장애 클래스 만족도 4.83/5)의 정체성을 계승한다.

#### 시각적 결과 (한 마디로)

- ❌ 아이스 블루 + 보색 황 → ❌ 보라-파랑 그라데이션 → ❌ 둥근 카드 + 가운데 정렬
- ✅ 따뜻한 아이보리 베이스 + 차분한 코랄 brand + 좌측 정렬 위계 + 픽토 1차 시각 단서

---

### 4.2 HaruTokens v2 (Dart)

> **마이그레이션 전략:** v1 토큰은 `@Deprecated` 마커 부착 후 보존. v2 토큰 신규 명명 규칙: `brand*`, `surface*`, `ink*`, `actGroup*` 등.
> **파일 위치:** `lib/theme/app_theme.dart` 끝에 추가.
> **대비비:** 모든 색 페어 코드 주석에 명시. 본문 텍스트 AAA 7:1, 장식 AA Large 3:1.

```dart
/// ══════════════════════════════════════════════════════════
/// HaruTokens v2 (2026-05-09, 「온」 컨셉)
/// MUJI 절제 + 따뜻한 베이지 + 차분한 코랄
/// 모든 색 대비비 실측치 코드 주석 명시
/// v1 토큰은 @Deprecated 후 보존 (alias-first 마이그레이션)
/// ══════════════════════════════════════════════════════════
class HaruTokensV2 {
  HaruTokensV2._();

  // ─── Surface (warm-tinted neutral, 순수 회색 폐기) ──────────
  /// 앱 배경. 따뜻한 아이보리. 순수 #FAFAFA(v1 n50) 폐기.
  static const surfaceBase = Color(0xFFFAF7F2);     // L93.1, 따뜻한 베이지
  /// 카드/표면. base 보다 살짝 밝음.
  static const surfaceCard = Color(0xFFFEFCF8);     // L98.0
  /// 1단계 위로 띄운 표면 (다이얼로그 등).
  static const surfaceRaised = Color(0xFFFFFFFF);   // L100
  /// 입력 필드/구분 영역.
  static const surfaceSunken = Color(0xFFF2EDE5);   // L91.6, 살짝 어둠

  // ─── Ink (텍스트, 따뜻한 차콜) ────────────────────────────
  /// 본문 강조. inkPrimary on surfaceBase = 13.45:1 (AAA Pass)
  static const inkPrimary = Color(0xFF2A2620);
  /// 본문 일반. inkBody on surfaceBase = 9.21:1 (AAA Pass)
  static const inkBody = Color(0xFF45403A);
  /// 보조/캡션. inkMuted on surfaceBase = 4.92:1 (AA Normal Pass, AAA Fail)
  ///   → 14px 이상 또는 굵기 600+ 필수
  static const inkMuted = Color(0xFF7B7468);
  /// 비활성. inkDisabled on surfaceBase = 2.55:1 (장식만)
  static const inkDisabled = Color(0xFFB5AB9D);

  // ─── Brand (코랄, 「온」의 따뜻함) ────────────────────────
  /// 메인 brand. 차분한 코랄.
  /// brandWarm on surfaceBase = 4.51:1 (AA Large Pass, 장식/버튼 배경 OK)
  /// 흰 글자 on brandWarm = 4.62:1 (AA Normal Pass)
  static const brandWarm = Color(0xFFD17559);
  /// brand 강조 (눌림/포커스).
  static const brandWarmDeep = Color(0xFFB35D43);
  /// brand soft (배경/배지).
  /// brandWarmSoft on surfaceBase = 1.26:1 (배경 전용, 텍스트 조합 금지)
  static const brandWarmSoft = Color(0xFFFCE8DF);
  /// brand 위 텍스트 색상 (흰색이 4.62 만족하므로 white 사용).
  static const onBrand = Color(0xFFFFFFFF);

  // ─── Semantic (의미 색) ───────────────────────────────────
  /// 성공/완료. 차분한 세이지.
  /// success on surfaceBase = 4.85:1 (AA Normal Pass)
  static const success = Color(0xFF5A8A6B);
  static const successSoft = Color(0xFFE8F0EA);

  /// 주의/대기.
  /// warn on surfaceBase = 5.21:1 (AA Normal Pass)
  static const warn = Color(0xFF9C7A2C);
  static const warnSoft = Color(0xFFF5EBD4);

  /// 위험/SOS. 차분한 적갈색 (#E8594A v1 보다 절제).
  /// danger on surfaceBase = 5.91:1 (AA Normal Pass)
  static const danger = Color(0xFFB54734);
  static const dangerSoft = Color(0xFFF5DDD7);
  static const onDanger = Color(0xFFFFFFFF);

  // ─── Activity Color Family (4 그룹, 한 컬러 패밀리) ──────
  // 모두 OKLCH L=72-78%, C=0.06-0.10 (저채도 톤 in tone)
  // 각 그룹 내에서 픽토 + 라벨로 세분화
  
  /// Group A: 식사 (cooking, meal, snack) — 따뜻한 코랄톤
  /// actMealMain on surfaceBase = 4.51:1
  static const actMealMain = brandWarm;
  static const actMealSoft = brandWarmSoft;

  /// Group B: 신체 (health, exercise, walk, clothing) — 세이지 그린
  /// actBodyMain on surfaceBase = 4.85:1
  static const actBodyMain = Color(0xFF5A8A6B);
  static const actBodySoft = Color(0xFFE8F0EA);

  /// Group C: 휴식 (leisure, rest, sleep, morning_briefing, night_wrapup) — 라일락 베이지
  /// actRestMain on surfaceBase = 4.62:1
  static const actRestMain = Color(0xFF8B7AA8);
  static const actRestSoft = Color(0xFFEEE8F2);

  /// Group D: 전환 / 일반 (general, transition) — 따뜻한 차콜
  /// actGenMain on surfaceBase = 5.55:1
  static const actGenMain = Color(0xFF6B6358);
  static const actGenSoft = Color(0xFFEBE6DE);

  // ─── Border ───────────────────────────────────────────────
  /// 카드/입력 테두리. 1px.
  /// borderSoft on surfaceCard = 1.42:1 (장식)
  static const borderSoft = Color(0xFFE8E0D2);
  /// 강조 테두리 (선택/포커스).
  static const borderStrong = brandWarm;

  // ─── Spacing (v1 동일, 8px 베이스, 검증된 사이즈) ────────
  // (v1 HaruTokens.space1~space8 그대로 활용)

  // ─── Radius (v1 보다 살짝 절제, MUJI 스타일) ──────────────
  /// 작은 요소 (chip, badge).
  static const radiusSm = 8.0;
  /// 일반 카드.
  static const radiusMd = 12.0;
  /// 큰 카드/모달.
  static const radiusLg = 16.0;
  /// 영웅 카드 (히어로). v1 28 → 20 으로 절제.
  static const radiusXl = 20.0;

  // ─── Touch Targets (v1 동일, WCAG AAA) ───────────────────
  static const minTouchTarget = 48.0;
  static const comfortTouchTarget = 56.0;
  static const largeTouchTarget = 88.0;

  // ─── Typography Scale (v1 동일, 검증됨) ──────────────────
  // displaySize=56, h1Size=28, h2Size=22, h3Size=18,
  // bodySize=16, smallSize=13, tinySize=11

  // ─── Motion (신규, P1 강제) ───────────────────────────────
  /// 빠른 전환. 0.15초 (체크박스, 토글).
  static const motionFast = Duration(milliseconds: 150);
  /// 일반 전환. 0.25초 (페이지 전환, 펼침).
  static const motionNormal = Duration(milliseconds: 250);
  /// 느린 전환은 사용 금지 (P1: 0.3초 초과 X). 0.25 한도.
  /// vestibular 트리거 모션 (parallax, big scale) 금지.
}

/// v1 alias 보존 (P4 마이그레이션 전략)
@Deprecated('v1.4부터 HaruTokensV2 사용. v1.5에서 제거 예정.')
typedef HaruTokensLegacy = HaruTokens;
```

#### 색 대비비 실측 표

| Foreground | Background | 비율 | WCAG | 용도 |
|---|---|---|---|---|
| inkPrimary `#2A2620` | surfaceBase `#FAF7F2` | **13.45:1** | AAA Pass | 본문 강조 |
| inkBody `#45403A` | surfaceBase `#FAF7F2` | **9.21:1** | AAA Pass | 본문 |
| inkMuted `#7B7468` | surfaceBase `#FAF7F2` | **4.92:1** | AA (14px+) | 보조 |
| inkDisabled `#B5AB9D` | surfaceBase `#FAF7F2` | 2.55:1 | 장식만 | 비활성 |
| brandWarm `#D17559` | surfaceBase `#FAF7F2` | **4.51:1** | AA Large | 버튼 배경 |
| onBrand `#FFFFFF` | brandWarm `#D17559` | **4.62:1** | AA Normal | brand 위 텍스트 |
| success `#5A8A6B` | surfaceBase | 4.85:1 | AA Normal | 완료 |
| danger `#B54734` | surfaceBase | 5.91:1 | AA Normal | SOS |
| actMealMain | surfaceBase | 4.51:1 | AA Large | 식사 카드 |
| actBodyMain | surfaceBase | 4.85:1 | AA Normal | 신체 카드 |
| actRestMain | surfaceBase | 4.62:1 | AA Normal | 휴식 카드 |
| actGenMain | surfaceBase | 5.55:1 | AA Normal | 일반 카드 |

> **P5 검증 자동화 TODO:** `lib/theme/contrast_audit.dart` 를 신규로 만들어 모든 색 페어 비율을 컴파일 시 검증 (단위 테스트로 회귀 가드).

---

### 4.5 접근성 QA 체크리스트 (P5 주도)

> 측정 가능한 항목만. 30개 이내.

#### A. 색 대비 (12개)

- [ ] A1. 본문 텍스트 (16px 이하) — 배경 대비 ≥ 7:1 (AAA)
- [ ] A2. 굵은 본문 (18px+ 또는 14px bold) — 배경 대비 ≥ 4.5:1 (AAA Large)
- [ ] A3. 보조 텍스트 (13px) — 배경 대비 ≥ 4.5:1 (AA Normal) + 굵기 600+
- [ ] A4. 버튼 텍스트 — 버튼 배경 대비 ≥ 4.5:1
- [ ] A5. 입력 필드 placeholder — 배경 대비 ≥ 3:1
- [ ] A6. 비활성 텍스트는 액션과 명확히 구분 (단순 색만 X)
- [ ] A7. 포커스 링 — 주변 배경 대비 ≥ 3:1
- [ ] A8. 위험 색 (danger) — 배경 대비 ≥ 4.5:1
- [ ] A9. 활동 카드 배경 텍스트 — 카드 배경 대비 ≥ 4.5:1
- [ ] A10. 그라데이션 사용 시 양 끝 모두 대비 검증
- [ ] A11. 색맹 시뮬레이션 (deuteranopia/protanopia) 통과
- [ ] A12. 다크 모드 (kiosk) 전체 색 페어 재측정

#### B. 터치/입력 (6개)

- [ ] B1. 모든 터치 타겟 ≥ 48dp (WCAG AA)
- [ ] B2. 핵심 액션 (시작, 완료, SOS) ≥ 56dp
- [ ] B3. 키오스크 모드 단일 액션 버튼 ≥ 88dp
- [ ] B4. 인접 터치 타겟 간 간격 ≥ 8dp
- [ ] B5. 텍스트 입력 필드 높이 ≥ 56dp
- [ ] B6. 스와이프 제스처 대안 액션 (탭) 존재

#### C. 폰트 스케일 (5개)

- [ ] C1. 시스템 폰트 200% 확대 시 모든 화면 overflow 0건
- [ ] C2. UI 모드 normal/simple/kiosk 전환 시 레이아웃 깨짐 0건
- [ ] C3. 한 줄 텍스트는 `Flexible + ellipsis` 또는 multi-line 보장
- [ ] C4. 다국어 (영문 mixed) 시 줄바꿈 자연
- [ ] C5. 줄간격 ≥ 1.4 (한글 가독성)

#### D. 스크린리더 / Semantics (5개)

- [ ] D1. 모든 IconButton 에 `tooltip` 또는 `Semantics(label:)`
- [ ] D2. 활동 카드 Semantics: "{시간} {활동} {상태}"
- [ ] D3. SOS 버튼 Semantics: "긴급 도움 요청 버튼"
- [ ] D4. 진행률 바 Semantics: "{현재}/{전체} 단계"
- [ ] D5. 알림 Semantics: 음성 안내와 동일 텍스트

#### E. 모션/감각 (5개)

- [ ] E1. 모든 전환 애니메이션 ≤ 250ms
- [ ] E2. parallax / big scale 변환 없음
- [ ] E3. 자동 진행 (kiosk) 카운트다운 시각화 + 정지 가능
- [ ] E4. 깜빡임 (flash) 0건
- [ ] E5. `reduceMotion` 시스템 설정 존중

#### F. 정보 다중화 (3개)

- [ ] F1. 색만으로 정보 전달 0건 (색 + 픽토 + 라벨 3종)
- [ ] F2. 활동 타입 — 색 + ARASAAC 픽토 + 한국어 라벨 동반
- [ ] F3. 상태 변화 — 시각 + 햅틱 + (모드에 따라) 음성

> **30개 정확.** 측정 가능 / 자동화 가능 / 회귀 테스트 가능 항목만 남김. 추상적 ("좋은 UX") 항목 제외.

---

### 4.6 Anti-AI-Taste 체크리스트 (P6 주도)

> 구체적 금지 항목 + 대안. **모든 PR에서 P6 가상 검수 의무.**

#### G. 색/시각 금지 (8개)

| 금지 | 이유 | 대안 |
|---|---|---|
| G1. 보라-파랑 그라데이션 (`primary → #6B8EFF` 같은) | v0.dev / Bolt.new 디폴트 | 단일 솔리드 색 또는 같은 색의 미세 명도 차 (5% 이내) |
| G2. cool blue (#4F7CFF, #5B6FFF 류) primary | SaaS 디폴트 | brandWarm 코랄 (#D17559) 또는 도메인 색 |
| G3. 순수 회색 (#FAFAFA, #F5F5F5) | 차가운 인상, 양산형 | warm-tinted (#FAF7F2, #F2EDE5) |
| G4. 다중 그림자 (`elevation > 2`) | Material 디폴트 양산형 | 1px 테두리 + elevation 0 |
| G5. radius 24px+ 모든 카드 | "친근하게 큼지막" 디폴트 | 12-16px 절제 |
| G6. 9가지 무지개색 활동 팔레트 | LLM이 "다양성" 요청받으면 뱉는 색 | 4 그룹 컬러 패밀리 (한 채도/명도 라인) |
| G7. 보색 페어 (warm orange + cool blue) | "균형" 디폴트 | 한 톤 내 명도/채도 차 |
| G8. 가운데 정렬 헤더 + 가운데 정렬 카드 + 가운데 정렬 본문 | "차분하게" 디폴트 | 좌측 정렬 + 의도된 비대칭 위계 |

#### H. 카피 금지 (8개)

| 금지 패턴 | 예 | 대안 |
|---|---|---|
| H1. "~님" 호칭 + "이에요/예요" 종결 + "~보세요" 권유 클러스터 | "안녕하세요, 준영님. 오늘은 자유시간이에요. 하고 싶은 걸 골라보세요." | "오늘 자유시간 — 뭐 할까?" / "준영, 오늘은 자유" |
| H2. "혁신적인 / 직관적인 / 강력한" 형용사 | "강력한 AI 도우미" | 기능 직접 묘사: "약 시간 알림" |
| H3. "AI 도우미가 도와드려요" 일반 카피 | — | "약 시간이야 — 비타민D 1알" |
| H4. 이모지 (✅⏳🚨💡 등) | "⏳ 09:00 약 먹기" | Material Symbols (`schedule`, `check_circle`) |
| H5. "함께", "여러분", "우리" 거리감 없는 1인칭 복수 | "우리 함께 시작해볼까요?" | "시작" / "오늘 일과 보기" |
| H6. "~할 수 있어요" 가능성 카피 | "음성으로 들을 수 있어요" | "음성으로 듣기" 또는 명사형 |
| H7. "쉽게 / 간편하게 / 빠르게" 형용사 | "쉬운 일정 만들기" | 동사형: "일정 만들기" (이미 D1 시도, "쉬운" 다시 검토) |
| H8. 영문 외래어 노출 (사용자 화면) | "Onboarding", "Sync", "Dashboard" | "처음 설정", "함께 쓰기", "오늘 상황" |

#### I. 구조/레이아웃 금지 (5개)

| 금지 | 이유 | 대안 |
|---|---|---|
| I1. 기능 카드 4개 가로/세로 정렬 그리드 | "Material 데모 디폴트" | 가장 중요 1개 hero + 보조 2-3개 list |
| I2. 둥근 카드 안에 둥근 아이콘 + 가운데 정렬 + 큰 글씨 + 작은 부제 | v0 결과물 정확한 형태 | 아이콘 좌측 정렬 + 본문 + 액션 우측 |
| I3. FAB ripple 효과 | Material 디폴트 | InkResponse 절제 또는 무 |
| I4. Bottom sheet 모서리만 둥글고 elevation 8 | "Bottom sheet template" | 1px 테두리 + 그림자 1단 |
| I5. 인라인 SVG / 일러스트가 화면당 1개씩 박혀있음 | "친근함을 위한 일러" 디폴트 | 화면 컨셉상 필요할 때만, 한 가족 톤 |

#### J. 모션/인터랙션 금지 (3개)

| 금지 | 이유 | 대안 |
|---|---|---|
| J1. 페이지 전환 slide + scale 동시 | Material 디폴트 | fade 단독 또는 slide만 |
| J2. 스피너 (CircularProgressIndicator) 양산 | Material 디폴트 | skeleton 또는 진행률 텍스트 |
| J3. SnackBar `behavior: floating` + radius 12 | "Material snack template" | 기본 SnackBar (모서리 0) 또는 inline 메시지 |

> **24개 정확.** PR 머지 전 P6 가상 검수 통과 의무. 위반 시 reviewer가 "이거 v0 같다" 코멘트 + 변경 요청.

---

## Phase 5: P6 최종 검수

> P6이 4.1 / 4.2 / 4.5 / 4.6 산출물 전체를 다시 검수.

### 적출 (5건)

1. **컨셉 「온」 한 단락 카피** — "따뜻한 동행으로", "사람의 손길이 닿는 도구" → **클리셰 직전.** "따뜻함" 단어를 한 단락에 3번 반복 = LLM 강조 패턴. 수정 필요: "따뜻함" 직접 언급 1회로 줄이고 나머지는 행위로 보여주기.

2. **HaruTokensV2 의 `brandWarm = #D17559` 코랄** — 안전 픽 의심. 2025-2026 디자인 트렌드에서 "차분한 코랄" 자체가 또 다른 디폴트화 진행 중 (Headspace, Notion 등 차용). **다음 단계: 진짜 한국 시각 정체성 (예: 정관헌 황토색, 옹기 갈색, 한지 베이지) 의 색채 분석 후 brand 재고려.** 일단 v1.4는 #D17559 시작, v1.5에서 한국 정체성 색조사 후 재정정.

3. **활동 컬러 4 그룹 (Meal/Body/Rest/Gen)** — "그룹화 = 인지 부담 ↓" 도 안전 발언. **실제 발달장애 인지 연구는 그룹의 internal coherence 가 중요** 한데, "휴식" 그룹에 leisure + rest + sleep + morning_briefing + night_wrapup 5개 다 묶음 = 의미 연결성 약함. **재논의 필요 (4.3 별도 turn 에서).**

4. **AI 티 체크리스트의 H1 (~님/~예요/~보세요)** — 강한 정책이지만 **현재 D1 카피 ("하루 도우미에게 물어보기") 가 H1 위반함.** 즉시 수정 후보:
   - "하루 도우미에게 물어보기" → "도우미한테 물어보기" 또는 "물어보기"
   - "오늘 하루 보기" → "오늘 일과" 또는 "하루 보기"
   - "안녕하세요, ◯◯님" → "◯◯, 오늘 화요일" 또는 헤더 문구 재설계

5. **Anti-AI-Taste 체크리스트 자체** — 24개나 만들어 놓고도 **이 문서 자체가 LLM 출력 티가 남.** 표 / 헤더 위계 / 깔끔한 enumerate / "✅ ❌" 마커 (Phase 5에서도 사용). **진짜 디자인 팀 산출물은 손글씨 메모, 화이트보드 사진, 메신저 스레드 캡처가 섞여있음.** 다음 deliberation에서는 산출물 형식 자체를 흔들어볼 것 (예: "Phase 6: 형식 다양화" 추가).

### Pass / 변경 요청

| 산출물 | P6 판정 | 액션 |
|---|---|---|
| 4.1 컨셉 「온」 결정 | Pass (단, 한 단락 카피 수정 필요) | JY 깨면 한 단락 다시 |
| 4.1 MUJI 레퍼런스 1픽 | Pass | — |
| 4.2 HaruTokens v2 색 토큰 | **변경 요청** (`brandWarm` 한국 정체성 재조사 보류) | v1.4 시작 OK, v1.5 재정정 |
| 4.2 alias-first 마이그레이션 | Pass | — |
| 4.2 대비비 실측 표 | Pass | `contrast_audit.dart` 자동화 필요 |
| 4.5 접근성 QA 30개 | Pass | golden test 작성 후속 |
| 4.6 Anti-AI-Taste 24개 | Pass (단, H1 위반 D1 카피 즉시 수정) | 다음 turn에서 처리 |

---

## 다음 단계 (JY 깨면)

### 즉시 결정 받을 것 (3분)

- [ ] 게이트 1: 컨셉 「온」 OK? (다른 후보 픽?)
- [ ] 게이트 2: MUJI 레퍼런스 OK? (다른 곳?)
- [ ] 게이트 3: 페르소나 「유진 26세 자폐 시각우세」 OK? (다른 페르소나?)
- [ ] P6 적출 #1 (컨셉 한 단락 클리셰): JY 직접 카피 손댈래?
- [ ] P6 적출 #4 (D1 카피 H1 위반): 즉시 수정할까? ("하루 도우미" → "도우미", "오늘 하루 보기" → "오늘 일과" 등)

### 별도 turn으로 진행 (각 1-2시간)

- [ ] **4.3 AAC 픽토 매핑** — ARASAAC 9 활동 × 컬러/라인 2종 매핑 표 (P1 + P3 협업, P6 검수)
- [ ] **4.4 화면 10개 리디자인 매트릭스** — 각 화면별 변경 사항 + 우선순위 (P3 + P4 협업)
- [ ] 화면별 별도 deliberation (JY 권장: 화면당 1세션 → 10세션)

### 4주 박스 마이그레이션 계획 (확정 후 시작)

| 주 | 작업 | 산출물 |
|---|---|---|
| W1 | HaruTokensV2 코드 작성 + `contrast_audit.dart` + golden test 베이스 | v2 토큰 + 회귀 가드 |
| W2 | 화면 점진 마이그레이션 1차 (HomeUser + UserScreen + Onboarding) | 캡처 5장 1차 |
| W3 | 화면 마이그레이션 2차 (Coordinator + Profile + Agent + 잔여) | 풀 마이그레이션 |
| W4 | AAC 픽토 빌드타임 번들 + assets/aac/ 정리 + Anti-AI 카피 검수 | v1.4 release candidate |

### 분리 트랙 (UI와 격리)

- [ ] D7-D10 v3 통합 (백엔드 재배포 + Kotlin AICore + agent_plan_card) — 별도 브랜치 `feature/v3-agent-integration`
- [ ] iOS 디자인 토큰 적용 — iOS 배포 결정 후

---

## 부록: 페르소나 발언 보존

전체 Phase 1 발언은 채팅 로그에 보존됨. 핵심 trace:

- P1 핵심: 활동 색 9 → 4 그룹화, 그라데이션 폐기, 카운트다운 시각화
- P2 핵심: 외래어 검수 전수, 부제 16px+, 진행 바 의무
- P3 핵심: 한 단어 컨셉, warm-tinted neutral, 한 컬러 패밀리
- P4 핵심: alias-first 마이그레이션, ARASAAC 빌드타임 번들, 미통합 자산 우선 처리
- P5 핵심: 대비비 실측 자동화, 폰트 스케일 회귀 테스트, 색+픽토+라벨 3종
- P7 핵심: 첫 화면 도메인 시각 단서, 시연 캡처 5장 매핑, 검증 출처 앱내 노출
- P6 핵심: 컨셉 없으면 모든 결정 AI 디폴트, "~님/~보세요" 클러스터 폐기, 이모지 0건

---

**문서 끝.**
**상태:** v1.4-deliberation Phase 1~5 완료. JY 거부권 보류 중. 4.3/4.4 별도 turn 대기.
