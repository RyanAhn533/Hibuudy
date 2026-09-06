# 하루메이트 (HaruMate) — 종합 아키텍처 문서

> **문서 목적:** 외부 발표(연세대), 공모전 제출(현대오토에버 배리어프리), 포트폴리오용 단일 마스터 자료
> **작성일:** 2026-05-09
> **현재 버전:** v1.3.3+6 (배포 트랙) + v3.0-dev (병행)
> **패키지:** `com.harumate.care`
> **백엔드:** https://hibuudy.onrender.com
> **저장소:** RyanAhn533/Hibuudy

---

## 0. 한 줄 요약

> **하루메이트는 발달장애 당사자가 보호자의 지속 지시 없이도 하루 일과를 따라갈 수 있도록 돕는, AI 기반 접근성 우선 생활 루틴 보조 앱이다.**

기술적으로는 **Flutter 앱(클라이언트) + FastAPI(서버) + 듀얼 LLM(Gemini 2.0 + Claude Haiku 4.5) + Edge TTS + 3-tier 메모리(Mem0 스타일) + 멀티 에이전트 오케스트레이터** 의 조합이다. 모든 기능은 **오프라인 폴백**을 갖추며, **WCAG AAA 접근성**을 충족한다.

---

## 1. 시스템 전체 구조도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              사용자 디바이스                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                Flutter 앱 (com.harumate.care, v1.3.3)                  │ │
│  │                                                                        │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │ │
│  │  │   Screens 10   │  │  Widgets 7     │  │  Services 16   │         │ │
│  │  │  (UI 모드 3)   │  │ (재사용 컴포)  │  │ (도메인 로직)  │         │ │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │ │
│  │                                                                        │ │
│  │  ┌────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Theme System: HaruTokens + HaruText + HiBuddyColors           │  │ │
│  │  │  (색상 팔레트 / 7단 typography / 8px spacing / radius / WCAG)  │  │ │
│  │  └────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  │  ┌────────────────────────────────────────────────────────────────┐  │ │
│  │  │  로컬 저장: SQLite(harumate.db, 7테이블) + SharedPrefs + 파일캐시│  │ │
│  │  └────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  │  ┌────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Tier 0: 로컬 키워드 폴백 (오프라인 100% 동작)                  │  │ │
│  │  │  Tier 1: Gemini Nano (AICore, MethodChannel) ⏳ 통합 중         │  │ │
│  │  │  Tier 2: 백엔드 프록시 호출 (HTTPS Bearer)                       │  │ │
│  │  └────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  │  flutter_tts (디바이스 한글 TTS)  │  flutter_local_notifications      │ │
│  └────────────┬───────────────────────────────────────────────────────────┘ │
└───────────────┼─────────────────────────────────────────────────────────────┘
                │ HTTPS (Bearer APP_AUTH_TOKEN)
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  FastAPI 백엔드 (Render Free, hibuudy.onrender.com)          │
│                                                                             │
│  ┌────────────┐  ┌────────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │  Auth      │  │ Sanitize +     │  │ slowapi    │  │ Error masking  │  │
│  │  (Bearer)  │  │ Validation     │  │ (rate)     │  │ (key 30+→***)  │  │
│  └────────────┘  └────────────────┘  └────────────┘  └────────────────┘  │
│                                                                             │
│  /api/agent · /api/schedule/* · /api/tts · /api/clothing                   │
│  /api/youtube/search · /api/image/search · /api/recipes                    │
│  /api/errors · /api/waitlist · /api/metrics                                │
│                                                                             │
│  ┌──────────────────── v3 멀티 에이전트 (옵트인 토글) ───────────────────┐ │
│  │  /api/v3/agent · /api/v3/agent/approve · /api/v3/agent/explain       │ │
│  │  /api/v3/memory/fact · /memory/facts/{user_id} · /memory/cleanup     │ │
│  │                                                                       │ │
│  │  Orchestrator → can_handle 점수 → 4 도메인 에이전트                  │ │
│  │    ├─ ScheduleAgent (일정/시간)                                       │ │
│  │    ├─ MealAgent (식사/요리/영양)                                      │ │
│  │    ├─ HealthAgent (약/위급, EMERGENCY priority 1.0)                   │ │
│  │    └─ SocialAgent (연락/외출)                                         │ │
│  │                                                                       │ │
│  │  Mem0 스타일 3-tier (SQLite, Zep temporal validity)                  │ │
│  │    ├─ user_facts (영속, valid_from/until)                            │ │
│  │    ├─ session_events (24h TTL)                                       │ │
│  │    └─ agent_patterns (학습된 사용자 패턴)                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌──────────── LLM 캐스케이드 ────────────┐  ┌──── 백엔드 데이터 ─────┐  │
│  │ 1차 Gemini 2.0 Flash (15 RPM 무료)     │  │ schedules.db           │  │
│  │ 2차 Claude Haiku 4.5 (대화 / 유료)     │  │ errors.db              │  │
│  │ 3차 Groq Llama 3.3 70B (무료 폴백)     │  │ waitlist.db            │  │
│  │ TTS: Edge TTS (ko-KR-SunHi/InJoon)     │  │ tts_cache/{sha256}.mp3 │  │
│  └────────────────────────────────────────┘  └────────────────────────┘  │
└──────────┬──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            외부 클라우드/API                                 │
│                                                                             │
│  Google Gemini 2.0 Flash    │  Anthropic Claude Haiku 4.5  │  Groq Cloud   │
│  Microsoft Edge TTS         │  YouTube Data API v3         │  Google CSE   │
│  wttr.in (날씨)             │  Hugging Face (1회, 페르소나) │              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│             v3 검증/연구 시스템 (개발 환경, 배포 X, 281,992 페르소나)         │
│                                                                             │
│  v3/personas/                                                               │
│    NVIDIA Nemotron-Personas-Korea (CC BY 4.0, 한국 통계청 grounding)        │
│    필터링: 발달장애·돌봄·독거노인·일반노인 → harumate_personas.parquet     │
│  v3/simulation/                                                             │
│    5 시나리오 × N 페르소나 → JSONL 결과 + 평가 보고서 (라우팅 100%, 위급 100%)│
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              병행 운영                                       │
│                                                                             │
│  Streamlit 웹 (Hi-Buddy.py + pages/)  ←  같은 백엔드 호출, 별도 UI 트랙    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 프론트엔드 (Flutter)

### 2.1 진입점 부트스트랩 (`lib/main.dart`, 52줄)

| # | 단계 | 위치 |
|---|---|---|
| 1 | `ErrorReporter.install()` (전역 크래시 캡처) | L16 |
| 2 | `WidgetsFlutterBinding.ensureInitialized()` | L18 |
| 3 | `initializeDateFormatting('ko_KR')` (DateFormat 'ko' 사용 전 필수) | L20 |
| 4 | `RecipeData.load()` (assets/data/recipes.json) | L21 |
| 5 | `DatabaseService.db` (SQLite v2 마이그레이션 포함) | L22 |
| 6 | `UiModeService.loadMode()` (normal/simple/kiosk 복원) | L23 |
| 7 | `ApiService.isOnline()` (Render 콜드스타트 방어) | L25 |
| 8 | `ErrorReporter.flush()` (백그라운드, 이전 에러 서버 전송) | L27 |
| 9 | `NotificationService.init()` + `rescheduleAll()` | L29 |
| 10 | `SessionService.isOnboarded()` | L31 |
| → | onboarded=true → `HomeScreen` / false → `OnboardingScreen` | L43 |

### 2.2 화면 (`lib/screens/`)

| 파일 | 라인 | 역할 | 핵심 분기 |
|---|---|---|---|
| `home_screen.dart` | 626 | 역할 기반 라우터 | kiosk → UserScreen 직행 / self → HomeUserScreen / coordinator → HomeCoordinatorScreen |
| `home_user_screen.dart` | 348 | **당사자용 홈** | 현재/다음 활동 미리보기 + 큰 CTA 2개 (활동/도우미) + SOS FAB |
| `home_coordinator_screen.dart` | 355 | **보호자용 홈** | 진행률 + 페어링 코드 + 4 빠른 작업 (일정/하루/도우미/내 정보) |
| `user_screen.dart` | 985 | **수행 화면** | 30초 갱신 + 활동 전환 진동/TTS + 키오스크 자동 진행 + 단계 체크박스 + 타이머 |
| `coordinator_screen.dart` | 743 | **일정 입력** | 자연어 → API 파싱 + 오프라인 폴백 + 페어 코드 자동 서버 싱크 |
| `agent_screen.dart` | 492 | **채팅 에이전트** | HaruAgent.handle() + AgentAction 파싱 (recipe/youtube/timer/call/navigate) + TTS 자동 |
| `profile_screen.dart` | 858 | **내 정보** | 프로필/식재료/연락처/약/수행기록 + 엑셀 내보내기 |
| `onboarding_screen.dart` | 692 | **온보딩 3단계** | Step0 역할/세그먼트 → Step1 이름/지역/글자 → Step2 페어링 코드 |
| `timer_screen.dart` | 425 | 접근성 타이머 | 큰 글씨 + TTS 30/10초 경고 + 진동 |
| `youtube_screen.dart` | 260 | 인앱 재생 | videoId 있으면 인앱, 없으면 검색→브라우저 |

### 2.3 위젯 (`lib/widgets/`)

| 파일 | 위젯 | 역할 |
|---|---|---|
| `activity_card.dart` (117줄) | ActivityCard | 시간대 활동 카드 (좌측 컬러 바, 타입 배지) |
| `step_card.dart` (469줄) | StepCard / StepsList / `_SingleFocusStep` (D3) / `_ProgressIndicator` | 단계 체크 + TTS 자동 + 분/초 정규식 자동 타이머 + **kiosk 단일 포커스 모드** |
| `morning_briefing.dart` (269줄) | MorningBriefing | 날씨 + AI 옷 추천 + 인사 + TTS |
| `sos_button.dart` (146줄) | SosButton | 빨간 FAB → 비상 연락처 또는 119 (simple/kiosk만 노출) |
| `agent_plan_card.dart` (197줄) | AgentPlanCard / AgentPlan / PlanStep | 에이전트 plan 시각화 + 사용자 승인 (D10에서 통합 예정) |

### 2.4 서비스 레이어 (`lib/services/`, 16 파일)

| 파일 | 핵심 책임 | 호출 엔드포인트 |
|---|---|---|
| `api_service.dart` (277줄) | 백엔드 프록시, 30s 타임아웃, 지수 백오프 2회 | `/api/schedule/{generate,save,load}`, `/api/tts` |
| `database_service.dart` (288줄) | sqflite 7테이블, v1→v2 마이그레이션 | — (로컬) |
| `schedule_storage.dart` (178줄) | SharedPrefs 저장 + 페어 코드 기반 서버 싱크 (날짜별 7일 보관) | `/api/schedule/{save,load}` |
| `haru_agent.dart` (418줄) | 에이전트 핵심 로직 + 컨텍스트 빌드 + ChatMemory 통합 + 오프라인 폴백 | `/api/agent` |
| `chat_memory.dart` (79줄) | 5분 세션 자동 리셋, 토큰 절약 | — |
| `session_service.dart` (203줄) | 역할/세그먼트/페어 코드/이름/도시/온보딩 상태 | — |
| `schedule_generator.dart` (150줄) | 정규식 기반 오프라인 일정 파서 (HH:MM + 키워드) | — |
| `ui_mode_service.dart` (32줄) | 3 모드 폰트/버튼/아이콘 크기 분기 | — |
| `weather_service.dart` (145줄) | wttr.in (한국 10도시, 30분 캐시, UTF-8) + AI 옷 추천 | `wttr.in/{city}`, `/api/clothing` |
| `tts_service.dart` (49줄) | flutter_tts 디바이스 우선 (오프라인) | `/api/tts` (옵션) |
| `timer_service.dart` (62줄) | 1초 카운트다운, pause/resume | — |
| `notification_service.dart` (210줄) | 로컬 푸시 (Firebase X), Asia/Seoul, Android 13+ 권한 요청 | — |
| `error_reporter.dart` (106줄) | 전역 핸들러 + 50개 순환 + 다음 시작 시 전송 | `/api/errors` |
| `activity_recommender.dart` (83줄) | 활동+장애수준 기반 유튜브 검색 강화 | `/api/youtube/search` |
| `export_service.dart` (240줄) | 3시트 엑셀 (수행기록/프로필/주간요약) | — |
| `ondevice_llm.dart` (75줄) | Gemini Nano AICore MethodChannel 브리지 | — (Tier 1, Kotlin 미작성) |

### 2.5 디자인 시스템 (`lib/theme/app_theme.dart`, 527줄)

**HaruTokens (단일 진실)**

```
Brand:    primary #4F7CFF / accent #FFB547
Sem.:     success #3FB765 / danger #E8594A / warning #FFB547
Neutral:  n50/100/200/400/700/900 (#FAFAFA → #1A1C1F)
Kiosk:    bg #0B1220 / card #15213D / muted #8AA6D3
Spacing:  4 8 12 16 20 24 32 (8px 베이스)
Radius:   12(sm) 16(md) 20(lg) 28(xl)
Touch:    48 / 56 / 88 (WCAG AAA)
Type:     56 / 28 / 22 / 18 / 16 / 13 / 11 (display→tiny)
Font:     Pretendard Variable + Apple SD Gothic Neo / Noto Sans KR / Roboto
```

**HaruText (D1, 신규)** — 7개 const TextStyle. 인라인 사용 금지, copyWith 만 허용.

**HiBuddyColors (Legacy 호환)** — `getActivityColor/BgColor/Icon/Label(type)` 매핑 9종 (cooking/meal/health/clothing/leisure/morning_briefing/night_wrapup/rest/general).

**buildAppTheme(kioskMode=false)** — Material3 + ColorScheme(light/dark) + 모든 컴포넌트(Button/Card/Input/Chip/Dialog/BottomSheet/SnackBar) 통일.

### 2.6 사용자 흐름 (라우팅 그래프)

```
[첫 실행] OnboardingScreen
  Step0: 역할(self/coordinator) + 세그먼트(dd/senior/dementia/youth)
  Step1: 이름 + 글자크기 + 도시
  Step2: 페어링 코드 (생성 또는 입력)
              ↓
         HomeScreen
              ├─[kiosk]→ UserScreen (자동 진행, SOS 상시 표시)
              ├─[self]→ HomeUserScreen
              │           ├─CTA→ UserScreen ─→ TimerScreen / YouTubeScreen / AgentScreen
              │           └─CTA→ AgentScreen
              └─[coordinator]
                  ├─[simple]→ _buildSimpleHome
                  └─[normal]→ HomeCoordinatorScreen
                                 ├─→ CoordinatorScreen (저장 시 서버 자동 싱크)
                                 ├─→ ProfileScreen
                                 ├─→ UserScreen
                                 └─→ AgentScreen
```

---

## 3. 백엔드 (FastAPI)

### 3.1 주 엔드포인트 (`backend/main.py`, 984줄)

| Path | Method | Auth | Limit | 설명 |
|---|---|---|---|---|
| `/health` | GET | × | — | Render 헬스 체크 |
| `/api/waitlist` | POST | × | 10/min | 준비 중 세그먼트 이메일 수집 |
| `/api/errors` | POST | × | 30/min | Flutter 크래시 로그 (NDJSON) |
| `/api/errors/recent` | GET | ✓ | 30/min | 최근 에러 (관리자) |
| `/api/metrics` | GET | ✓ | 30/min | 통합 메트릭 |
| `/api/waitlist/count` | GET | ✓ | — | 세그먼트별 집계 |
| `/api/schedule/generate` | POST | ✓ | 10/min | Gemini 일정 생성 (JSON schema) |
| `/api/schedule/edit` | POST | ✓ | 10/min | 일정 수정 (LLM) |
| `/api/schedule/save` | POST | ✓ | 20/min | SQLite 저장 (user_id, date) |
| `/api/schedule/load` | GET | ✓ | 30/min | 저장 일정 조회 |
| `/api/agent` | POST | ✓ | 20/min | v2 에이전트 (Claude/Gemini 캐스케이드 + 컨텍스트) |
| `/api/clothing` | POST | ✓ | 30/min | 온도+날씨 기반 옷 추천 |
| `/api/tts` | POST | ✓ | 30/min | Edge TTS + SHA256 캐시 |
| `/api/youtube/search` | GET | ✓ | 20/min | YouTube Data API v3 |
| `/api/image/search` | GET | ✓ | 20/min | Google CSE |
| `/api/recipes` | GET | ✓ | 30/min | 레시피/운동 JSON |

### 3.2 미들웨어/유틸

- `verify_token()` (L101) — APP_AUTH_TOKEN Bearer (미설정 시 우회 + 경고 로그)
- `sanitize(text, max_length=2000)` (L115) — 제어문자 제거 + 길이 제한
- `raise_for_upstream()` (L144) — 업스트림 에러 본문에서 30+ 문자 토큰 정규식 마스킹 (`***`)
- `get_client()` — `httpx.AsyncClient` 싱글톤 (timeout=30s)
- `_clean_json_response()` — CoT/마크다운 제거, `{`/`[` 추출
- `Limiter(key_func=get_remote_address)` — IP 기반 slowapi

### 3.3 LLM 캐스케이드 헬퍼

| 함수 | 시그니처 | 역할 |
|---|---|---|
| `gemini_generate()` | system, user, schema, json_mode, max_tokens | Gemini 2.0 Flash 호출 |
| `groq_generate()` | system, user, json_mode, max_tokens | Groq (OpenAI 호환) |
| `llm_generate()` | system, user, schema, json_mode, max_tokens | **캐스케이드: Gemini → Groq → 503** |

**일정 생성:** Gemini → Groq → 503
**에이전트 대화:** Claude → Gemini → Groq → 503
**옷 추천:** Gemini → 템플릿 폴백

### 3.4 데이터 (서버 SQLite 3개)

| DB | 컬럼 | 비고 |
|---|---|---|
| `schedules.db` | user_id, date, data TEXT, updated_at | PK(user_id, date) |
| `errors.db` | ts, tag, msg, stack, platform, received_at | NDJSON 호환 |
| `waitlist.db` | email, segment, created_at | UNIQUE(email, segment) |

### 3.5 Edge TTS 캐시

- 디렉토리: `tts_cache/`
- 키: `SHA256(text).hexdigest() + ".mp3"`
- 음성: `ko-KR-SunHiNeural`(기본 여성) / `ko-KR-InJoonNeural`(남성)
- edge-tts 7.x stream API 사용

---

## 4. v3.0 멀티 에이전트 시스템 (옵트인)

> **위치:** `v3/`
> **활성화:** ENV `USE_V3_ORCHESTRATOR=true` (기본값) 시 `/api/v3/*` 자동 마운트
> **롤백:** false 한 줄로 v2.1 동작 즉시 복귀

### 4.1 디렉토리

```
v3/
├── ARCHITECTURE.md
├── agents/
│   ├── base.py              ← Context / Plan / PlanStep / Result 프로토콜
│   ├── orchestrator.py      ← 라우팅 (점수 max + 0.2 임계값)
│   ├── schedule_agent.py    ← 일정/시간
│   ├── meal_agent.py        ← 식사/요리/영양
│   ├── health_agent.py      ← 약/위급 (EMERGENCY priority 1.0)
│   ├── social_agent.py      ← 연락/외출/사회
│   └── backend_integration.py  ← FastAPI 라우터 (6 엔드포인트)
├── memory/
│   ├── mem_store.py         ← Mem0 스타일 3-tier (SQLite, Zep temporal)
│   └── mem.db               ← 데이터
├── personas/
│   ├── 01_download_and_filter.py
│   ├── 02_inspect.py
│   ├── harumate_personas.parquet  (~497MB, 281,992 rows)
│   └── stats.json
├── simulation/
│   ├── 01_run_scenarios.py  ← 5 시나리오 × N 페르소나
│   ├── 02_evaluate.py       ← 보고서 생성
│   └── results/             ← run_*.jsonl + report_*.md
└── data/
    └── hf_cache/            ← Hugging Face 5.8GB
```

### 4.2 에이전트 키워드 (라우팅 핵심)

```
ScheduleAgent
  strong: 일정 / 스케줄 / 할일 / 오늘 뭐 / 내일 뭐 / 약속
  weak:   오늘 / 내일 / 리마인드 / 다음 / 끝났 / 완료 / 체크 / 마쳤 / 했어 / 잡아

MealAgent
  strong: 밥 먹 / 식사 / 요리 / 레시피 / 메뉴 / 점심 / 저녁 / 아침 식사 / 간식 / 냉장고
  weak:   재료 / 맛있 / 영양 / 건강식

HealthAgent
  strong: 약  / 약을 / 약은 / 약먹 / 복용 / 먹는약 / 두통 / 아파 / 아프 / 어지러
          수면 / 병원 / 응급 / 다쳤 / 쓰러
  weak:   피곤 / 졸려 / 운동 / 산책 / 걷 / 잠 / 자야 / 자고
  emergency (priority 1.0): 응급 / 구해줘 / 위험 / 쓰러 / 다쳤 / 피나

SocialAgent
  strong: 전화 / 연락 / 엄마 / 아빠 / 부모 / 선생님 / 외출 / 나갈 / 나가 / 만나 / 심심 / 외로
  weak:   친구 / 약속해
```

### 4.3 라우팅 알고리즘

```python
1. 모든 에이전트 can_handle() 병렬 호출
2. strong_keyword 매칭 → 0.95
3. weak_keyword 매칭 → min(0.7, hits / max(1, len(keywords)//2))
4. EMERGENCY → 1.0 (HealthAgent 우선)
5. max(scores) 선택; 임계값 0.2 미만 → fallback
```

### 4.4 v3 엔드포인트

| Path | 용도 |
|---|---|
| POST `/api/v3/agent` | 입력 → 라우팅 → plan → 즉시 실행 또는 승인 대기 |
| POST `/api/v3/agent/approve` | 승인된 plan 실행 |
| POST `/api/v3/agent/explain` | **투명성:** 모든 에이전트 점수 + 선택 이유 |
| POST `/api/v3/memory/fact` | UserFact 저장 |
| GET `/api/v3/memory/facts/{user_id}` | 활성 facts 조회 |
| POST `/api/v3/memory/cleanup` | 24h+ 세션 이벤트 삭제 |

### 4.5 Mem0 3-Tier 메모리 (`v3/memory/mem_store.py`)

| 테이블 | 역할 | 핵심 컬럼 |
|---|---|---|
| `user_facts` | **영속 사실** | user_id, key, fact, valid_from, valid_until (NULL=현재 유효), source, confidence |
| `session_events` | **단기 대화** | user_id, session_id, role, content, ts (24h TTL) |
| `agent_patterns` | **학습 패턴** | agent_name, user_id, pattern, count, last_seen, evidence_json (최근 20) |

**Zep 스타일 temporal validity:** `remember_fact()` 호출 시 같은 key의 기존 fact `valid_until = now` 업데이트 → 사실의 시간적 변화 추적.

---

## 5. AI/LLM 통합 (3-Tier)

| Tier | 위치 | 모델 | 비용 | 응답 시간 | 용도 |
|---|---|---|---|---|---|
| **0 로컬** | Flutter | 키워드 폴백 | 무료 | 0ms | 오프라인, 단순 명령 |
| **1 온디바이스** | Flutter (AICore) | Gemini Nano | 무료 | ~100ms | 의도 분류, 일정 파싱 (⏳ Kotlin 미작성) |
| **2 백엔드 캐스케이드** | FastAPI | Gemini 2.0 / Claude Haiku 4.5 / Groq Llama 3.3 70B | 무료~유료 | ~500ms | 풀 컨텍스트 추론 |

**TTS 옵션:**
- 디바이스: `flutter_tts` (한국어, 오프라인 우선)
- 서버: Edge TTS (`ko-KR-SunHiNeural`, SHA256 캐시)

**Tier 2 캐스케이드 — 일정 생성:** Gemini → Groq → 503
**Tier 2 캐스케이드 — 에이전트 대화:** Claude → Gemini → Groq → 503

---

## 6. 데이터 저장 전체 맵

### 6.1 디바이스 (Flutter, `harumate.db` 7테이블)

| 테이블 | 핵심 컬럼 |
|---|---|
| `user_profile` | name, disability_level (mild/moderate/severe), ui_mode (normal/simple/kiosk), tts_speed (0.45 기본), wake_time, sleep_time, user_type |
| `daily_template` | day_of_week, type, task, guide_script (JSON 배열) |
| `completion_log` | date, time, activity_type, steps_total, steps_completed, needed_help |
| `ingredients` | 냉장고 식재료 |
| `emergency_contacts` | 비상 연락처 (relationship, name, phone, is_emergency) |
| `medicine_schedule` | 약 복용 시간 |
| `places` | 자주 가는 장소 |

**SharedPreferences:** first_run, user_role, pair_code, unsent_error_count, recent_chat_5min
**파일:** TTS 캐시 (path_provider), `harumate_errors.jsonl` (50줄 순환)

### 6.2 백엔드 (Render)

- `schedules.db` — 사용자별 일정 (user_id, date PK)
- `errors.db` — 크래시 로그
- `waitlist.db` — 대기자 (segment 분리)
- `tts_cache/{sha256}.mp3` — Edge TTS 결과

### 6.3 v3 데이터 (개발 환경 only)

- `v3/memory/mem.db` (~44KB) — 3-tier 메모리
- `v3/personas/harumate_personas.parquet` (~497MB) — 281,992 한국 페르소나
- `v3/data/hf_cache/` (~5.8GB) — Hugging Face 모델/데이터셋 캐시

---

## 7. 보안 아키텍처

### 7.1 인증/인가 흐름

```
Flutter (API 키 0개)
   │ Authorization: Bearer ${APP_AUTH_TOKEN}
   ▼
verify_token() → APP_AUTH_TOKEN 검증
   │ (미설정 시 인증 우회 + 경고 로그 — 개발용)
   ▼
백엔드 → 외부 API (모든 키는 Render 환경변수)
   ├─ Gemini (GEMINI_API_KEY)
   ├─ Claude (CLAUDE_API_KEY)
   ├─ Groq (GROQ_API_KEY)
   ├─ Edge TTS (무인증)
   └─ wttr.in (무인증)
```

### 7.2 보안 장치

| 영역 | 장치 |
|---|---|
| 입력 | `sanitize()` — 제어문자 제거 + max_length=2000 |
| 인증 | `verify_token()` Bearer 토큰 |
| 속도 | `slowapi` IP 기반 (10~30/min, 엔드포인트별) |
| 키 누출 | `raise_for_upstream()` — 업스트림 에러에서 30+ 문자 토큰 `***` 마스킹 |
| 서명 | Android 키스토어 RSA 2048 / 10000일 (`harumate-release.jks`, .gitignore) |
| 빌드 | `--dart-define` 으로 Bearer 주입 (앱 내 키 0개) |
| 통신 | HTTPS only (Render `*.onrender.com`) |
| 디바이스 | Cleartext 비활성화 (`AndroidManifest.xml`), `allowBackup=false` |

### 7.3 환경변수 마스터

| 변수 | 필수 | 기본값 | 비고 |
|---|---|---|---|
| `GEMINI_API_KEY` | Y | — | 무료 15 RPM |
| `APP_AUTH_TOKEN` | Y | — | 미설정 시 인증 우회 |
| `CLAUDE_API_KEY` | N | — | 유료, Tier 2 |
| `CLAUDE_MODEL` | N | claude-haiku-4-5-20251001 | |
| `GROQ_API_KEY` | N | — | 무료 폴백 |
| `GROQ_MODEL` | N | llama-3.3-70b-versatile | |
| `GOOGLE_API_KEY` | N | — | YouTube/CSE 옵션 |
| `GOOGLE_CSE_ID` | N | — | |
| `YOUTUBE_API_KEY` | N | GOOGLE_API_KEY | |
| `EDGE_TTS_VOICE` | N | ko-KR-SunHiNeural | |
| `USE_V3_ORCHESTRATOR` | N | true | v3 라우터 활성화 |

---

## 8. 클라우드/인프라

### 8.1 백엔드 (Render Free Tier)

| 항목 | 값 |
|---|---|
| URL | https://hibuudy.onrender.com |
| 메모리 | 512MB |
| 시간 | 750h/월 |
| 콜드스타트 | ~2~3초 (`ApiService.isOnline()` 으로 사전 깨우기) |
| 명령어 | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| 설정 파일 | `render.yaml`, 백업으로 `railway.toml`, `Dockerfile`, `Procfile` |
| 헬스 체크 | `/health` |

### 8.2 모바일 (Google Play Console)

| 항목 | 값 |
|---|---|
| 패키지 | `com.harumate.care` |
| 버전 | v1.3.3+6 |
| 트랙 | 비공개 테스트 (테스터 14일 유지 12명 룰) |
| 그룹 | `harumate-testers@googlegroups.com` |
| 비용 | $25 (1회 등록비) |
| 키스토어 | `harumate-release.jks` (RSA 2048, 10000일) |

### 8.3 빌드 자동화 (`hi_buddy_app/scripts/`)

- `generate_keystore.sh` — 키스토어 + key.properties 생성
- `build_release.sh [URL] [TOKEN]` — AAB + APK 생성, `--dart-define` 주입
- `deploy_backend.sh` — Railway 배포 (보조)

### 8.4 CI/CD (`.github/workflows/flutter-ci.yml`)

- 트리거: main push / PR
- 잡 1: `flutter analyze --no-fatal-infos` + `flutter test --coverage`
- 잡 2 (main만): Java 17 + Debug APK + 아티팩트 (서명 키 제외)

### 8.5 Git 브랜치/태그

```
main                              ← 프로덕션
├── feature/uiux-polish-v134      ← 현재 (D1-D3 + intl fix)
├── claude/continue-work-kth2Y    ← 이전 작업
├── v1.3.1-finish                 ← 완료 피처
└── v2.1.3-baseline-pre-v3 [tag]  ← 롤백 체크포인트
```

---

## 9. 외부 API 의존성 매트릭스

| API | 호출처 | 인증 | Rate | 비용 | 핵심 용도 |
|---|---|---|---|---|---|
| Google Gemini 2.0 Flash | 백엔드 | API_KEY | 15 RPM | 무료 | 일정 생성, 옷 추천, 에이전트 |
| Anthropic Claude Haiku 4.5 | 백엔드 | API_KEY | — | 유료 | 에이전트 대화 (Tier 2 1순위) |
| Groq Llama 3.3 70B | 백엔드 | API_KEY | — | 무료 | 캐스케이드 폴백 |
| Microsoft Edge TTS | 백엔드 | 무인증 | — | 무료 | 한국어 음성 합성 |
| wttr.in | Flutter | 무인증 | — | 무료 | 날씨 데이터 |
| YouTube Data API v3 | 백엔드 | API_KEY | 10K/일 | 무료 | 활동 기반 영상 추천 |
| Google CSE | 백엔드 | KEY+CSE_ID | 100/일 | 무료 | 이미지 검색 (옵션) |
| Hugging Face | 로컬 | 옵션 | — | 무료 | Nemotron-Personas-Korea (1회, 5.8GB) |
| Render | 호스팅 | — | 750h/월 | 무료 | FastAPI 서버 |
| Google Play | 배포 | 계정 | — | $25 1회 | 안드로이드 앱 |

---

## 10. 페르소나 검증 시스템 (v3, 차별화 포인트)

> **방법론 깊이 + FAQ + 재현 방법:** [PERSONA_VALIDATION.md](PERSONA_VALIDATION.md) 참조 (NVIDIA가 어떻게 데이터셋을 만들었는지, 우리가 어떻게 필터링/시뮬레이션 했는지의 디테일)


### 10.1 데이터셋

- **NVIDIA Nemotron-Personas-Korea** (2026.04.20 공개, CC BY 4.0)
- 700만 한국 합성 페르소나, 한국 통계청 grounding
- 다운로드 1회: `v3/data/hf_cache/` (~5.8GB)
- 필터링 결과: `v3/personas/harumate_personas.parquet` (~497MB, **281,992개**)

### 10.2 카테고리

| 카테고리 | N | 비고 |
|---|---|---|
| elderly | 178,008 | 65+ 일반 노인 |
| elderly_alone | 47,898 | 65+ 1인 가구 = 독거노인 프록시 |
| caregiver | 37,337 | 사회복지/돌봄/요양 종사자 |
| caregiver+elderly | 5,255 | 노인 돌봄 종사자 |
| disability_related | 3,779 | 발달장애/지적장애/자폐 가족 또는 종사자 |
| **합계** | **281,992** | |

**연령:** 평균 68.9세, 19~99세
**지역:** 경기 65K > 서울 50K > 부산 21K > ... (전국 17개 시도)

### 10.3 시뮬레이션 (5 시나리오 × N)

| ID | 시나리오 | 입력 | Preset |
|---|---|---|---|
| S1 | 아침 일정 확인 | "오늘 뭐 해야 돼?" | 일정 3개 |
| S2 | 점심 식사 | "점심에 뭐 먹지?" | 김치/계란/밥/참치 |
| S3 | 약 복용 | "약 먹을 시간이야?" | 비타민D 현재 시간 |
| S4 | 외출 준비 | "이제 나갈 거야" | 보호자 연락처 |
| S5 | 위급 상황 | "도와줘 다쳤어" | 비상 연락처 |

### 10.4 최근 결과 (2026-05-08, N=48)

| 지표 | 값 |
|---|---|
| 전체 성공률 | **100%** (240/240) |
| 라우팅 정확도 (S1~S5) | **100%** 모두 |
| 위급 처리 도움 호출률 | **100%** |
| 위급 처리 차분한 어조 | **100%** |
| 평균 응답 시간 | 0.1ms (휴리스틱) |
| 어려운 단어 수 | **0** (장애 친화) |

### 10.5 외부 표현 가이드 (중요)

- ✅ "LLM 기반 사용자 페르소나 시뮬레이션 (NVIDIA Nemotron-Personas-Korea, 한국 통계청 grounding) 으로 초기 사용성 점검"
- ✅ "연세대 사회복지대학원 HEART Lab + 서부장애인종합복지관 협력"
- ✅ "온쿡 헬로TV 보도 + 발달장애인 클래스 만족도 4.83/5"
- ❌ **"전문가 5인 패널 검증"** — Claude 페르소나로 만든 것, 외부 사용 금지
- ❌ "치료 효과 / 진단 가능 / 행동 개선 입증" — 위험

---

## 11. 알림 / 모니터링 / 에러

| 영역 | 구현 |
|---|---|
| 로컬 알림 | `flutter_local_notifications` + `timezone` (Asia/Seoul). Firebase 의존성 없음 |
| 알림 종류 | 활동 시작 / 약 복용 / 아침 브리핑 (07:00) |
| Android 13+ | `POST_NOTIFICATIONS` 권한 요청 |
| 크래시 로그 | `error_reporter.dart` 전역 핸들러 → `harumate_errors.jsonl` (50줄 순환) → 다음 시작 시 `/api/errors` 전송 |
| 서버 메트릭 | `/api/metrics` (인증 필수) — gemini/claude/groq/auth 활성화 상태 + 24h 에러 + waitlist 집계 |

---

## 12. 비용 분석 (연간)

| 항목 | 비용 |
|---|---|
| Render | 무료 (Free Tier) |
| Edge TTS | 무료 |
| Gemini API | 무료 (15 RPM) |
| Groq | 무료 |
| wttr.in / YouTube / CSE | 무료 |
| Google Play 등록비 | $25 (1회) |
| Claude (선택) | 사용량 기반 (~$5~50/월) |
| Apple App Store (선택) | $99/년 (현재 미배포) |

**Android만 운영 시 연간 운영비:** $0 (Claude 끄면) ~ $50 (Claude 사용 시)

---

## 13. 차별화 (포지셔닝)

| 항목 | 일반 AI 챗봇 앱 | 하루메이트 |
|---|---|---|
| 주체 | 챗봇 | **일과 수행 보조** (챗봇은 보조) |
| 사용자군 | 일반인 | **발달장애 당사자 + 보호자 + 기관** 3 역할 분리 |
| 접근성 | 옵션 | **WCAG AAA 기본**, UI 모드 3단계 |
| 오프라인 | 미지원 | **핵심 기능 100% 동작** |
| LLM | 단일 | **3-tier (로컬→온디바이스→클라우드)** |
| 검증 | 사용자 평점 | **NVIDIA 통계청 grounded 페르소나 시뮬레이션** |
| SOS | 없음 | **simple/kiosk 모드 상시 표시 → 비상 연락처/119** |
| 보호자 연동 | — | **페어링 코드 → 30초 자동 싱크** |
| B2B | — | **엑셀 내보내기 (3시트)** — 복지관 제출용 |
| 에이전트 | 블랙박스 | **plan 시각화 + 사용자 승인 (v3, 투명성)** |

---

## 14. 코드 규모 요약

| 영역 | 파일 | 줄 수 |
|---|---|---|
| Flutter (lib/) | 32 | ~9,577 |
| FastAPI (backend/) | 3 | ~1,200 |
| v3 Python (v3/) | 14 | ~2,500 |
| Streamlit (Hi-Buddy.py + pages/) | 3 | ~1,650 |
| 테스트 (test/) | — | 54 통과 |
| **합계** | ~52 | **~14,927줄** |

---

## 15. 향후 로드맵 (v3.0 활성화)

| Day | 작업 | 상태 |
|---|---|---|
| D1 | HaruText 타이포 utility + 카피 미세조정 | ✅ 2026-05-08 |
| D2 | HomeUserScreen 토큰화 + 다음 활동 미리보기 | ✅ |
| D3 | step_card 토큰화 + 키오스크 단일 포커스 | ✅ |
| D4 | Onboarding + MorningBriefing 정리 | ⏳ |
| D5 | HomeCoordinator + SOS + 잔여 화면 | ⏳ |
| D6 | 키오스크 시각 차별화 강화 | ⏳ |
| D7 | v3 백엔드 Render 재배포 | ⏳ |
| D8 | Kotlin AICore 네이티브 어댑터 | ⏳ |
| D9 | Flutter Tier1 라우팅 통합 | ⏳ |
| D10 | agent_plan_card 통합 + 시연 동선 | ⏳ |
| D11 | v1.3.4 릴리즈 빌드 + 시연 자료 | ⏳ |

---

## 부록 A. 파일 위치 빠른 참조

```
C:\Users\wnsdu\Hibuudy\
├── hi_buddy_app/                ← Flutter 앱
│   ├── lib/
│   │   ├── main.dart            (52)
│   │   ├── screens/             (10 파일)
│   │   ├── widgets/             (7 파일)
│   │   ├── services/            (16 파일)
│   │   ├── models/              (2 파일)
│   │   └── theme/app_theme.dart (527)
│   ├── android/app/
│   │   ├── build.gradle.kts
│   │   ├── src/main/AndroidManifest.xml
│   │   └── src/main/kotlin/com/harumate/care/MainActivity.kt
│   ├── pubspec.yaml
│   ├── store_listing.md
│   └── scripts/
├── backend/
│   ├── main.py                  (984)
│   ├── response_evaluator.py
│   ├── render.yaml / Dockerfile / Procfile / railway.toml
│   └── *.db (schedules / errors / waitlist)
├── v3/
│   ├── ARCHITECTURE.md
│   ├── agents/                  (7 파일)
│   ├── memory/mem_store.py
│   ├── personas/                (다운로드 + 통계)
│   └── simulation/              (시나리오 + 평가)
├── docs/
│   ├── ARCHITECTURE_FULL.md     ← 이 문서
│   ├── privacy_policy.md
│   ├── welfare-center-manual.md
│   ├── security_audit_checklist.md
│   └── ...
├── Hi-Buddy.py + pages/         ← Streamlit 웹
├── CLAUDE.md
├── README.md
├── STORE_RELEASE_CHECKLIST.md
└── .github/workflows/flutter-ci.yml
```

---

**문서 끝.**
**상시 업데이트:** 매 주요 기능 변경 시 갱신.
**참고 메모리:** `~/.claude/projects/.../memory/project_harumate.md`
