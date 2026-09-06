# 하루메이트 — 진화사 (Evolution / Changelog)

> **문서 목적:** 프로젝트가 어떻게 변해왔는지, 어떤 기술이 언제 왜 들어왔는지, 다음에 무엇이 들어올지를 한 곳에서 추적.
> **작성일:** 2026-05-09
> **누적 통계:** 181 커밋 / ~14,927줄 / 7개 주요 페이즈 / 5개월
> **자매 문서:** [ARCHITECTURE_FULL.md](ARCHITECTURE_FULL.md) (현재 상태) · [CLAUDE.md](../CLAUDE.md) (에이전트 설정)

---

## 0. 전체 타임라인 (한눈에)

```
 2025                          2026
   │                             │
12─┼─01─02─03─04─05─06─07─08─09─10─11─12─01─02─03─04─05── (현재)
   │                                            │   │  │
   ●──── Streamlit 시기 ──────────────────────────●   │  │
   초기                                      포트폴리오│  │
   2025-12-06                              2026-03-08│  │
                                                    │  │
                                          v1.0──────●  │
                                          (Flutter,    │
                                          Gemini)      │
                                          2026-03-22   │
                                                       │
                                          v2.0/2.1 ────●
                                          (에이전트,
                                          UI 3모드)
                                          2026-03-25~26
                                                          │
                                                v1.2~1.3.1●
                                                (B2B+CI+테스트)
                                                2026-04-19~22
                                                          │
                                                  v3.0-dev●
                                                  (멀티에이전트
                                                  +페르소나)
                                                  2026-05-08~09
```

**5개월 동안 Streamlit 웹 → Flutter 앱 → AI 에이전트 → 멀티 에이전트로 진화.**

---

## 1. 페이즈별 진화 (7개)

### Phase 0: Streamlit 프로토타입 (2025-12-06 ~ 2026-03-08, 3개월)

**왜:** 발달장애인 쿠킹클래스 만족도 4.83/5 달성한 "온쿡" 챗봇을 웹앱화.
**무엇:** Streamlit + Python 유틸 (TTS, YouTube)
**커밋 스타일:** "Update X.py", "a", "feed2" — 빠른 반복
**코드 규모:** Initial commit `24d476e` 기준 104 파일 / 2,603줄

**파일 구조 (당시):**
```
Hi-Buddy.py             ← 메인 페이지
pages/
├── 1_코디네이터_일정입력.py
└── 2_사용자_오늘_따라하기.py
utils/
├── tts.py              ← OpenAI TTS
├── youtube_ai.py
└── ...
```

**의의:** "복지관 종사자가 일정 입력 → 당사자 따라하기" 기본 사이클 확립.

---

### Phase 1: 포트폴리오 정리 (2026-03-08, 짧음)

**커밋:** `4fee50f` Add portfolio README with project background and technical docs

**왜:** 외부 공유/포트폴리오용 첫 README. 서울청년기획봉사단 2기 → 헬로TV 보도 → 연세대 HEART Lab 협력 스토리 정리.
**영향:** 프로젝트 정체성 ("기술 토이"가 아니라 "사회복지 임팩트") 명문화. 이후 모든 결정의 기준이 됨.

---

### Phase 2: Flutter 앱화 + 백엔드 분리 (2026-03-13 ~ 22, 9일)

| 커밋 | 일자 | 내용 |
|---|---|---|
| `9e6aafd` | 03-13 | **Add Flutter cross-platform mobile app (iOS + Android)** ← 모바일 진출 |
| `597b651` | 03-13 | 단위/통합 테스트 스위트 추가 |
| `147a6fc` | 03-13 | 보안 강화 (앱스토어 배포 준비) |
| `9cf741a` | 03-22 | **v1.0.0: Gemini/EdgeTTS 마이그레이션, 백엔드 배포, 스토어 준비** (37 파일, +2,875/-557) |
| `1dee16a` | 03-22 | **HaruMate 리네임** (Hi-Buddy → HaruMate, 패키지명 변경) |

**핵심 변화:**
- **언어 변경:** Streamlit (Python 단일 앱) → Flutter (모바일) + FastAPI (백엔드 분리)
- **LLM 변경:** OpenAI GPT → **Google Gemini 2.0 Flash** (15 RPM 무료 → 코스트 0)
- **TTS 변경:** OpenAI TTS (유료) → **Microsoft Edge TTS** (무료, 한국어 우수)
- **호스팅 추가:** Render Free Tier 백엔드 + Google Play 비공개 테스트 준비

**의의:** "데모"에서 "출시 가능 제품"으로 격상. 무료 운영 가능 구조 완성.

---

### Phase 3: AI 에이전트화 v2.0 (2026-03-25, 단일일)

| 커밋 | 내용 |
|---|---|
| `3a524d8` | **v2.0: HaruMate Agent — 발달장애인 종합 생활 에이전트** (11 파일, +2,303/-9) |
| `3a299ad` | Real AI agent: Claude-powered context-aware life assistant |
| `fb0a8f1` | **VLA-based CLAUDE.md — autonomous development agent config** |

**핵심 변화:**
- **에이전트 패러다임 도입:** 단순 챗봇 → 컨텍스트 기반 에이전트 (사용자 프로필/일정/식재료/약/연락처/수행기록 모두 LLM에 전달)
- **Claude API 추가:** 대화 응답 전용 (Gemini는 일정 생성 전담)
- **VLA (Vision-Language-Action) 패러다임:** CLAUDE.md = weight, prompt = action signal, memory = shared state. 자율 개발 에이전트 컨피그.

**의의:** 단순 일정 앱이 "AI 도우미"로 성격 변화. 듀얼 LLM 분담 구조 확립.

---

### Phase 4: 접근성 v2.1 (2026-03-26, 단일일)

| 커밋 | 내용 |
|---|---|
| `3be0b92` | **v2.1: Weather briefing, YouTube player, timer, UI modes, SOS button** (14 파일, +1,671/-68) |

**한 커밋에 들어간 것:**
- **MorningBriefing 위젯** — 날씨 + AI 옷 추천 + 인사 + TTS
- **YouTube 인앱 재생** — `youtube_player_flutter`
- **TimerScreen** — 큰 글씨 카운트다운, 30/10초 경고음, 진동
- **UI 모드 3단계** — `UiModeService` (normal 16px / simple 22px / kiosk 28px)
- **SosButton** — 빨간 FAB (비상 연락처 → 119 폴백)
- **StepCard 신규** — 단계 체크박스 + TTS 자동 재생

**의의:** **접근성 우선 앱 정체성 확립.** WCAG AAA 준수 (48px+ 터치, 16px+ 폰트). 키오스크 모드로 복지관 현장 적용 가능성 확보.

---

### Phase 5: 보안 / 안정화 (2026-03-23 ~ 27, 5일간 분산)

| 커밋 | 내용 |
|---|---|
| `c4135d6` | 백엔드 body 파싱 크래시 수정 + Flutter 코드 리뷰 픽스 |
| `5bdc4cc` | APP_AUTH_TOKEN 미설정 시 인증 우회 허용 (개발/무료 tier 대응) |
| `5a6646c` | **Gemini 무료 tier 15 RPM 대응 — 재시도 루프 제거** (재시도가 오히려 실패율 ↑) |
| `b46227f` | "전문가 패널 + 시뮬레이션 리뷰" 기반 UX 픽스 |
| `f327fc4` | "전문가 패널 리뷰" 기반 5개 핵심 기능 추가 |
| `bb43960`/`af9ea2a` | **🔒 SECURITY: API 키 노출 제거 (CLAUDE.md, api_service.dart)** |
| `6b08ba9` | CLAUDE.md 재추가 (키 제거 + 깨끗한 history) |

**핵심 변화:**
- **API 키 .env 분리 + git history 정리** — 노출됐던 키 추적/제거
- **무료 티어 운영 안정화** — Gemini 15 RPM 한계 안에서 동작하도록 재시도 로직 단순화
- **에러 핸들링 강화** — 백엔드 에러에서 30+ 문자 토큰 정규식 마스킹

**⚠️ 정직성 노트:** 이 시기의 "전문가 패널 5인 검증 / 사용자 100명 시뮬레이션"은 **Claude API로 만든 페르소나**임. 외부 자료에는 사용 불가 (메모리 `feedback_apply_means_running.md`). 실제 검증은 v3 페르소나 시뮬레이션으로 대체 (Phase 7).

---

### Phase 6: 품질 v1.x 정상화 (2026-04-19 ~ 22, 4일)

| 커밋 | 일자 | 내용 |
|---|---|---|
| `f706825` | 04-19 | **/api/agent 엔드포인트 + Gemini 2.5 Flash 폴백** |
| `2af8e85` | 04-19 | Gemini 2.5 → 2.0 롤백 (2.5는 400 반환) |
| `1ff7221` | 04-19 | Gemini systemInstruction camelCase 픽스 |
| `4c9dbd3` | 04-19 | **Groq Llama 3.3 70B 폴백 추가 (Claude→Gemini→Groq 캐스케이드)** |
| `8923a4c` | 04-19 | GitHub Pages 활성화 (privacy policy 호스팅) |
| `0cccb14` | 04-20 | **사용자 세그먼트 단계 (DD + senior/dementia/youth waitlist)** |
| `c84d2c4` | 04-21 | **v1.2 — sync, memory, YT recs, AI clothing** (149 파일, +5,682/-138) |
| `922e70f` | 04-22 | **v1.3 — B2B-ready, bug fixes, UX refinement** (27 파일, +1,347/-323) |
| `47cebfb` | 04-22 | **v1.3.1 — Pretendard, tests, B2B dashboard, CI, accessibility** (11 파일, +796/-140) |
| `2f16baf` | 04-22 | v1.3.1 finish — metrics 엔드포인트 + 복지관 매뉴얼 + 에뮬 검증 스크린샷 |
| `1374044` | 04-22 | **테스트 54/54 통과** ← `v2.1.3-baseline-pre-v3` 태그 |

**핵심 변화:**
- **LLM 캐스케이드 완성** — Claude (대화 1차) → Gemini (백업) → Groq (무료 폴백)
- **사용자 세그먼트 확장** — 발달장애 외에 노인/치매/청소년 waitlist (B2B 확장 노림수)
- **메모리 도입** — `chat_memory.dart` 5분 세션 자동 리셋 (토큰 절약)
- **AI 옷 추천** — 온도 + 날씨 + 이름 + 장애수준 → 개인화
- **B2B 엑셀 내보내기** — `export_service.dart` 3시트 (수행기록/프로필/주간요약)
- **Pretendard 폰트 도입** — 한글 가독성 1순위
- **GitHub Actions CI** — `flutter analyze` + `flutter test --coverage` 자동화
- **HaruTokens 디자인 토큰** — `app_theme.dart` 459줄 (Figma 기반)
- **메트릭 엔드포인트** — `/api/metrics` 인증 (서버 상태 모니터링)
- **개인정보처리방침** — GitHub Pages 호스팅 (Play 등록 필수)
- **테스트 54개** — 회귀 가드 확보

**의의:** **출시 가능 + B2B 확장 + 자동화 준비 완료.** "돈만 내면 출시" 상태 도달. v2.1.3-baseline-pre-v3 태그 = 안전한 롤백 포인트.

---

### Phase 7: v3.0 멀티 에이전트 + 페르소나 검증 (2026-05-08 ~ 09, 진행 중)

이번 작업 세션. 두 트랙 병행.

#### Track A: v3 백엔드/연구 (2026-05-08, untracked → 곧 commit)

```
v3/
├── ARCHITECTURE.md
├── agents/                      ← 4 도메인 에이전트 + Orchestrator
│   ├── base.py                  Context/Plan/PlanStep/Result 프로토콜
│   ├── orchestrator.py          점수 max + 0.2 임계값 + fallback
│   ├── schedule_agent.py
│   ├── meal_agent.py
│   ├── health_agent.py          ← EMERGENCY priority 1.0
│   ├── social_agent.py
│   └── backend_integration.py   /api/v3/* 6 엔드포인트
├── memory/
│   └── mem_store.py             ← Mem0 스타일 3-tier (Zep temporal)
├── personas/
│   ├── 01_download_and_filter.py
│   ├── 02_inspect.py
│   ├── harumate_personas.parquet  (281,992 rows, 497MB)
│   └── stats.json
├── simulation/
│   ├── 01_run_scenarios.py
│   ├── 02_evaluate.py
│   └── results/                 ← 240건 시뮬레이션 100% 통과
└── data/hf_cache/               ← 5.8GB (NVIDIA dataset)
```

**Flutter 측 신규:**
- `lib/services/ondevice_llm.dart` — Gemini Nano AICore MethodChannel 브리지 (Kotlin 미작성)
- `lib/widgets/agent_plan_card.dart` — 에이전트 plan 시각화 + 사용자 승인 UI

**backend/main.py 수정:**
- `if os.getenv("USE_V3_ORCHESTRATOR", "true").lower() != "false":` 가드
- `app.include_router(v3_router, prefix="/api/v3")` (try/except로 안전)

#### Track B: UI/UX 디자인 시스템 일관 적용 (2026-05-08~09, 4 커밋)

| 커밋 | 내용 |
|---|---|
| `7ef4058` | **D1: HaruText 7개 const TextStyle + 카피 4건** (도우미→하루 도우미, 프로필→내 정보 등) |
| `bfee110` | **D2: HomeUserScreen 토큰화 + 다음 활동 미리보기** (실데이터만, 더미 금지) |
| `fe4e8f1` | **D3: step_card 토큰화 + 키오스크 single-focus 위젯** + user_screen 5곳 wire |
| `9b3d5eb` | **🐛 fix(intl): 한국어 locale 초기화** ← v2.1.3 잠재 버그 수정 (없으면 HomeUser 진입 즉시 빨간 크래시) |

**의의:** 디자인 시스템(HaruTokens) 인프라는 v1.3.1에 깔렸지만 일관 적용은 안 됐었음 (169 인라인 TextStyle 등). D1-D3로 가장 가시적인 화면(홈+단계) 부분 적용. 양산형 탈피도 15~20% 진전.

---

## 2. 기술 도입 매트릭스 (시간순)

| 시점 | 도입 기술/패러다임 | 카테고리 | 영향 |
|---|---|---|---|
| 2025-12 | Streamlit + Python utils | 프레임워크 | 웹 프로토타입 시작 |
| 2025-12 | OpenAI GPT + TTS | LLM/TTS | 초기 챗봇 |
| 2026-03-13 | **Flutter (Dart)** | 프레임워크 | 모바일 앱화 |
| 2026-03-13 | flutter_test 단위/통합 | QA | 품질 가드 |
| 2026-03-22 | **Google Gemini 2.0 Flash** | LLM | OpenAI 교체, 무료 운영 |
| 2026-03-22 | **Microsoft Edge TTS** | TTS | OpenAI 교체, 무료, 한국어 우수 |
| 2026-03-22 | FastAPI + uvicorn | 백엔드 | API 서버 분리 |
| 2026-03-22 | Render Free Tier | 호스팅 | 무료 호스팅 |
| 2026-03-22 | Google Play Console | 배포 | 비공개 테스트 등록 |
| 2026-03-25 | **Anthropic Claude API** | LLM | 대화 전담 (Gemini는 일정) |
| 2026-03-25 | **VLA 패러다임 (CLAUDE.md)** | 패러다임 | 자율 개발 에이전트 |
| 2026-03-26 | UiModeService 3단계 | 접근성 | normal/simple/kiosk |
| 2026-03-26 | flutter_tts (디바이스) | TTS | 오프라인 음성 |
| 2026-03-26 | youtube_player_flutter | 미디어 | 인앱 영상 |
| 2026-03-26 | timezone (Asia/Seoul) | 시간 | 일정 정확성 |
| 2026-03-26 | SosButton + 비상 연락처 | 안전 | 위급 대응 |
| 2026-03-27 | API 키 .env 분리 | 보안 | 키 노출 차단 |
| 2026-03-27 | git history 키 정리 | 보안 | 과거 노출 제거 |
| 2026-04-19 | slowapi rate limiter | 백엔드 | 10~30/min |
| 2026-04-19 | **Groq Llama 3.3 70B** | LLM | 캐스케이드 폴백 |
| 2026-04-19 | GitHub Pages | 배포 | privacy policy 호스팅 |
| 2026-04-20 | 사용자 세그먼트 (4종) | 비즈니스 | DD/senior/dementia/youth |
| 2026-04-20 | waitlist 수집 | 비즈니스 | 미공개 세그먼트 사전 등록 |
| 2026-04-21 | sqflite 7테이블 | 저장 | 로컬 영속 |
| 2026-04-21 | chat_memory (5분 세션) | LLM | 토큰 절약 |
| 2026-04-21 | AI 옷 추천 | AI | 개인화 |
| 2026-04-21 | flutter_local_notifications | 알림 | Firebase 없이 로컬 |
| 2026-04-21 | path_provider (TTS 캐시) | 저장 | 음성 재사용 |
| 2026-04-22 | **Pretendard Variable** | 디자인 | 한글 가독성 |
| 2026-04-22 | **HaruTokens 디자인 시스템** | 디자인 | 색/spacing/radius/touch/typo 7단 |
| 2026-04-22 | Material Symbols Icons | 디자인 | 이모지 대체 |
| 2026-04-22 | excel 패키지 | B2B | 3시트 내보내기 |
| 2026-04-22 | share_plus | 공유 | OS 공유 시트 |
| 2026-04-22 | cached_network_image | 성능 | 이미지 캐싱 |
| 2026-04-22 | GitHub Actions CI | 자동화 | analyze + test 자동화 |
| 2026-04-22 | 페어링 코드 시스템 | 협업 | 코디↔당사자 30초 자동 싱크 |
| 2026-04-22 | /api/metrics 엔드포인트 | 모니터링 | 서버 상태 |
| 2026-05-08 | **NVIDIA Nemotron-Personas-Korea** | 검증 | 700만 페르소나, 281K 필터링 |
| 2026-05-08 | **Mem0 스타일 3-tier 메모리** | 에이전트 | user_facts + session + agent_patterns |
| 2026-05-08 | **Zep temporal validity** | 메모리 | valid_from/until로 사실 변화 추적 |
| 2026-05-08 | **멀티 에이전트 (4 도메인)** | 에이전트 | Schedule/Meal/Health/Social + Orchestrator |
| 2026-05-08 | **EMERGENCY priority** | 안전 | 위급 키워드 → HealthAgent 1.0 |
| 2026-05-08 | **Gemini Nano AICore (Tier 1)** | LLM | 온디바이스 (Kotlin 미완) |
| 2026-05-08 | **agent_plan_card** | UX | 투명성 + 사용자 승인 |
| 2026-05-09 | **HaruText typography utility** | 디자인 | 7개 const + copyWith only |
| 2026-05-09 | _SingleFocusStep 위젯 | UX | 키오스크 한 화면 한 단계 |
| 2026-05-09 | _ProgressIndicator 위젯 | UX | N/M 단계 진행바 |
| 2026-05-09 | intl ko_KR 초기화 | 버그픽스 | 한국어 DateFormat 크래시 방지 |

---

## 3. 영역별 진화 트래킹

### 3.1 LLM 스택의 진화

```
v0 (2025-12)        : OpenAI GPT (유료)
v1.0 (2026-03-22)   : Google Gemini 2.0 Flash (무료 15 RPM) — 단일
v2.0 (2026-03-25)   : + Anthropic Claude (대화 전담, Gemini는 일정)
v1.2.x (2026-04-19) : + Groq Llama 3.3 70B (캐스케이드 폴백)
                      = Claude → Gemini → Groq
v3.0 (2026-05-08)   : + Gemini Nano (Tier 1 온디바이스)
                      = 로컬 → Nano → 캐스케이드
```

### 3.2 TTS 스택의 진화

```
v0     : OpenAI TTS (유료)
v1.0   : Microsoft Edge TTS (무료, ko-KR-SunHi/InJoon)
v2.1+  : + flutter_tts (디바이스, 오프라인 우선)
        Edge TTS는 백엔드 캐시(SHA256 → mp3)로만 보조
```

### 3.3 데이터 저장의 진화

```
v0     : 메모리 only
v1.0   : SharedPreferences (간단 KV)
v1.2   : + sqflite 7테이블 (프로필/식재료/연락처/약/수행기록/장소/페어세션)
        + 백엔드 SQLite 3개 (schedules / errors / waitlist)
v3.0   : + v3/memory/mem.db (3-tier: user_facts / session_events / agent_patterns)
        + v3/personas/harumate_personas.parquet (281,992 rows, 497MB)
        + v3/data/hf_cache (5.8GB)
```

### 3.4 검증 방법의 진화

```
v0~v2.1 : (없음) → 클로드 페르소나 5인 "전문가 패널" 만든 후 사용
          ⚠️ 외부 사용 금지 (정직성 이슈)
v3.0    : NVIDIA Nemotron-Personas-Korea 281,992 (한국 통계청 grounding)
        → 5 시나리오 × 48 페르소나 = 240건 시뮬레이션
        → 라우팅 100%, 위급 100%
        ✅ 외부 사용 가능 (CC BY 4.0)

대외 표현 가이드:
✅ "LLM 기반 사용자 페르소나 시뮬레이션 (NVIDIA, 통계청 grounding)"
✅ "연세대 HEART Lab + 서부장애인종합복지관 협력"
✅ "온쿡 헬로TV 보도 + 발달장애인 클래스 만족도 4.83/5"
❌ "전문가 5인 패널 검증" (Claude 페르소나)
❌ "치료 효과 / 진단 가능"
```

### 3.5 에이전트 구조의 진화

```
v0~v1.x : 단순 챗봇 (입력 → LLM 응답)
v2.0    : 컨텍스트 기반 단일 에이전트 (haru_agent.dart)
          - 프로필/일정/식재료/약/연락처/수행기록 모두 LLM에 전달
          - AgentAction 파싱 (recipe/youtube/timer/call/navigate)
v3.0    : 멀티 에이전트 + Orchestrator
          - Schedule / Meal / Health / Social 도메인 분리
          - strong_keywords (0.95) + weak_keywords + EMERGENCY (1.0)
          - Plan 시각화 + 사용자 승인 (투명성)
          - Mem0 3-tier 메모리 통합
```

### 3.6 디자인 시스템의 진화

```
v0~v2.0 : 기본 Material (인라인 스타일 산발)
v2.1    : Material3 + 커스텀 ThemeData
v1.3.1  : HaruTokens 도입 (Figma 기반, 색/spacing/radius/touch/typo)
          ⚠️ 정의는 했으나 일관 적용 X (169 인라인 TextStyle 등)
D1-D3   : HaruText typography utility 추가 + 핵심 화면 일관 적용
          (현재 진행 중: ~13건 / 169건 = 8% 마이그레이션)
```

### 3.7 접근성의 진화

```
v0      : (고려 X)
v1.0    : 큰 글씨 옵션 추가
v2.1    : UiModeService 3단계 정식화
          - normal: 16px 폰트, 48px 버튼
          - simple: 22px 폰트, 64px 버튼, 자동 TTS
          - kiosk:  큰 글씨, 자동 진행, SOS 상시 노출
          + WCAG AAA 터치 타겟 (48/56/88)
          + Semantics 라벨
v1.3.1  : Pretendard 폰트 (한글 가독성 1순위)
v3.0(D3): kiosk 모드 한 화면 한 단계 single-focus 신규
```

### 3.8 보안의 진화

```
v0      : API 키 코드에 직접 (! 위험)
v1.0    : .env 파일 도입
v2.1    : APP_AUTH_TOKEN Bearer 인증 + slowapi rate limit
v1.3.x  : sanitize() (입력 길이/제어문자) + raise_for_upstream() (키 마스킹)
        + ProGuard 설정 (현재 minify OFF, 역컴파일 고려)
        + 키스토어 .gitignore + 백업 스크립트
        + privacy policy + 보안 감사 체크리스트 (docs/security_audit_checklist.md)
v3.0    : USE_V3_ORCHESTRATOR ENV 토글 (즉시 회귀 가능)
```

### 3.9 배포/CI 의 진화

```
v0      : 수동 (로컬)
v1.0    : Render Free Tier (백엔드) + Google Play 비공개 테스트 (앱)
v1.3.1  : GitHub Actions CI (analyze + test)
        + scripts/ (generate_keystore.sh, build_release.sh, deploy_backend.sh)
        + 페어링 코드 시스템 (코디↔당사자 협업)
v3.0    : 백업 태그 v2.1.3-baseline-pre-v3 (롤백 포인트)
        + feature/uiux-polish-v134 별도 브랜치 (UI 트랙 격리)
```

### 3.10 비즈니스 모델의 진화

```
v0~v2.1 : 발달장애인 단일 타겟
v1.2~   : 사용자 세그먼트 4종 도입
        - dd (developmental disability): 메인
        - senior (노인): waitlist
        - dementia (치매): waitlist
        - youth (청소년): waitlist
v1.3    : B2B 확장 — 엑셀 내보내기 (3시트, 복지관 제출용)
        + 페어링 코드 (코디 ↔ 당사자)
        + B2B dashboard
v3.0    : 차별화 강화 — 멀티 에이전트 + 투명성 + 페르소나 검증
        → 현대오토에버 콘테스트 (D-9, 5/17) + 연세대 발표 + 포트폴리오
```

---

## 4. 주요 마일스톤 비교 (Before/After)

### 마일스톤 1: Streamlit → Flutter (2026-03-13)

| | Before | After |
|---|---|---|
| 플랫폼 | 웹 only | iOS + Android + 웹 (3 트랙) |
| 코드 | Python 단일 | Dart (앱) + Python (백엔드) 분리 |
| 배포 | localhost | Render + Play Console |
| 사용자 도달 | 웹 브라우저만 | 모바일 (실사용) |

### 마일스톤 2: 단일 LLM → 듀얼 → 캐스케이드 (2026-03-22, 03-25, 04-19)

| | v1.0 (단일) | v2.0 (듀얼) | v1.2.x (캐스케이드) |
|---|---|---|---|
| LLM | Gemini 2.0 | Gemini + Claude | Claude → Gemini → Groq |
| 코스트 | 무료 (15 RPM) | 무료 + 유료 (Claude) | 무료 우선 + 유료 보조 |
| 안정성 | 단일 실패점 | 분담으로 분산 | 3중 폴백 |
| 응답 품질 | 단일 톤 | 도메인별 최적 | 동일 + 폴백 |

### 마일스톤 3: 단일 에이전트 → 멀티 에이전트 (2026-03-25 → 2026-05-08)

| | v2.0 (단일) | v3.0 (멀티) |
|---|---|---|
| 라우팅 | 모든 입력 → 한 LLM 호출 | strong_keywords로 4 도메인 분기 |
| 위급 처리 | 일반 응답 흐름 | EMERGENCY priority 1.0 즉시 분기 |
| 투명성 | 결과만 표시 | Plan 미리보기 + 사용자 승인 |
| 메모리 | 5분 세션만 | + 영속 사실 + 학습 패턴 (3-tier) |
| 검증 | 클로드 페르소나 (외부 X) | NVIDIA 281K (외부 OK) |

### 마일스톤 4: 디자인 시스템 정의 → 일관 적용 (2026-04-22 → 2026-05-09)

| | v1.3.1 | D1-D3 (현재) |
|---|---|---|
| HaruTokens 정의 | ✅ (459줄) | 동일 |
| 인라인 TextStyle | 169건 | ~156건 (~13건 처리) |
| typography utility | ❌ | ✅ HaruText 7개 |
| 카피 정리 | 기본 | 4건 (도우미→하루 도우미 등) |
| 키오스크 single-focus | ❌ | ✅ (D3) |
| 양산형 탈피도 | ~5% | ~15~20% |

---

## 5. 코드 규모의 진화

| 페이즈 | 시점 | 주요 변화 | 누적 코드 (대략) |
|---|---|---|---|
| Phase 0 | 2025-12 | Streamlit 초기 | ~2,600줄 |
| Phase 2 | 2026-03-22 | Flutter 추가 (v1.0) | ~5,500줄 |
| Phase 3 | 2026-03-25 | v2.0 에이전트 | ~7,800줄 |
| Phase 4 | 2026-03-26 | v2.1 위젯/UI 모드 | ~9,400줄 |
| Phase 6 | 2026-04-22 | v1.3.1 (B2B + CI + tests) | ~13,500줄 |
| Phase 7 | 2026-05-08 | v3.0 + 디자인 적용 | **~14,927줄** |

**테스트:** 0 → 54 통과 (v1.3.1 시점)
**시뮬레이션:** 0 → 240건 100% (v3.0 시점)

---

## 6. 기술 부채 / 미완

| 항목 | 상태 | 다음 액션 |
|---|---|---|
| 인라인 TextStyle 156건 | 진행 중 (8% 처리) | D4-D6에서 잔여 화면 마이그레이션 |
| 하드코딩 EdgeInsets 118건 | 진행 중 | 동일 |
| 하드코딩 BorderRadius 89건 | 진행 중 | 동일 |
| Color(0xFF...) 12건 | 미진행 | 신규 토큰 또는 HiBuddyColors 매핑 |
| Kotlin AICore MethodChannel | 미작성 | D8: AICore deps + handler |
| v3 백엔드 Render 재배포 | 로컬만 | D7: ENV USE_V3_ORCHESTRATOR=true |
| agent_plan_card 통합 | 위젯만 | D10: agent_screen에 박기 |
| ProGuard minify | OFF | 출시 전 (현재 디버깅 우선) |
| iOS 배포 | 미진행 | $99/년 + 메타데이터 |
| 다중 사용자 관리 | 미지원 | v3.x 후속 |
| 수행 기록 리포트 자동화 | 부분 (엑셀 내보내기만) | v3.x 후속 |
| Firebase 동기화 | 미지원 | v3.x 후속 |
| PersonaPlex 음성 페르소나 | 실험 | 별도 사이클 |

---

## 7. 다음 페이즈 예측 (2026-05 ~ 06)

| Day | 작업 | 상태 |
|---|---|---|
| D4 | Onboarding + MorningBriefing 토큰화 | ⏳ |
| D5 | HomeCoordinator + SOS + 잔여 화면 토큰화 | ⏳ |
| D6 | 키오스크 시각 차별화 강화 (kioskBg/kioskCard 활용) | ⏳ |
| D7 | v3 백엔드 Render 재배포 (USE_V3_ORCHESTRATOR=true) | ⏳ |
| D8 | Kotlin AICore 네이티브 어댑터 작성 | ⏳ |
| D9 | Flutter Tier1 라우팅 통합 (haru_agent.dart 수정) | ⏳ |
| D10 | agent_plan_card 메인 채팅에 통합 + 시연 동선 | ⏳ |
| D11 | v1.3.4 릴리즈 빌드 + 시연 자료 5장 + Play Console | ⏳ |

**병행 트랙:**
- 카페 테스터 모집 (Google Group `harumate-testers@googlegroups.com`)
- 연세대 발표 자료 준비
- 현대오토에버 콘테스트 (D-9, 5/17 마감) — JY 결정에 따라 별도 진행

---

## 부록: 명령어로 변천사 직접 확인

```bash
# 전체 커밋 (최신 → 과거)
git log --all --oneline --decorate

# 주요 마일스톤만
git log --all --oneline --grep -E 'v1\.|v2\.|v3\.|D[0-9]'

# 특정 파일의 변천사
git log --follow -p hi_buddy_app/lib/services/haru_agent.dart

# 특정 시점 코드로 시간 여행
git checkout v2.1.3-baseline-pre-v3   # 안전 롤백 포인트
git checkout main                       # 다시 최신

# 브랜치 (현재 작업)
git branch -a
# main
# feature/uiux-polish-v134  (현재)
# claude/continue-work-kth2Y
# v1.3.1-finish

# 통계
git shortlog -sn --all                  # 커밋 수 by 작성자
git log --all --pretty=format: --shortstat | awk '{i+=$4; d+=$6} END {print i" insertions, "d" deletions"}'
```

---

**문서 끝.**
**상시 업데이트:** 새 페이즈 시작 시 또는 주요 마일스톤 도달 시.
**메모리 참조:** `~/.claude/projects/.../memory/project_harumate.md`
