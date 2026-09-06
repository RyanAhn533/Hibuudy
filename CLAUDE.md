# 하루메이트 Autonomous Development Agent

> 이 파일을 읽은 Claude는 하루메이트 프로젝트의 자율 개발 에이전트로 동작한다.
> CLAUDE.md = weight, prompt = action signal, memory = shared state.
> 프로젝트 디렉토리: C:/Users/wnsdu/Hibuudy/

---

## 0. 새 세션 시작 시 (필수)

**먼저 `HANDOFF.md` 읽어라.** 5분 안에 모든 상황 파악 가능.
그 다음 `docs/JY_WAKEUP.md` 로 직전 세션 종료 상태 + Pending Gates 확인.

---

## 1. 프로젝트 상태 (V: Vision)

### 현재 버전: v2.1.3 (안정) + v3.0-dev (병행) + **v1.4-dev (UI/UX 「메이트」)**
- 패키지: **com.harumate.care** (com.harumate.app 아님 — 실제 build.gradle 기준)
- 앱 이름: 하루메이트 (구 Hi-Buddy, 이름 변경 완료)
- 서버: https://hibuudy.onrender.com (Render Free)
- LLM: Claude Haiku 4.5 (에이전트 대화) + Gemini 2.0 Flash (백엔드) + Groq 폴백
- TTS: flutter_tts (디바이스, 오프라인) + Edge TTS (서버 캐시)
- DB: sqflite 로컬 (7 테이블) + SharedPreferences
- 오프라인: 핵심 기능 100% 동작
- **컨셉: 「메이트」** (warm coral + warm-tinted neutral, MUJI 절제)

### v1.4 UI/UX 「메이트」 (2026-05-08~, 현재 브랜치 `feature/uiux-polish-v134`)
- **HaruTokensV2** 풀 마이그레이션: 9 화면 + 5 위젯 (12 commits)
- 양산형 탈피도 55 → **75** (목표 90)
- 그라데이션 0건 / 사용자 화면 이모지 0건 / H1 클러스터 0건
- 활동 9색 → 4 그룹 컬러 패밀리 (식사/신체/휴식/일과)
- v1 alias-first 마이그레이션 (HaruTokens v1 보존, 롤백 가능)
- 상세: `HANDOFF.md`, `docs/JY_WAKEUP.md`, `docs/UX_v1.4_PROGRESS.md`

### v3.0 진화 (2026-05-08~)
- **위치:** `v3/` (v2.1과 병행, ENV `USE_V3_ORCHESTRATOR` 토글)
- **검증:** NVIDIA Nemotron-Personas-Korea (281,992개 추출, 통계청 grounding) — 클로드 페르소나 검증 폐기
- **멀티 에이전트:** Schedule / Meal / Health / Social 4개 + Orchestrator
- **메모리:** Mem0 스타일 3-tier (user_facts / session_events / agent_patterns), SQLite 백엔드
- **온디바이스:** `lib/services/ondevice_llm.dart` Gemini Nano AICore 브리지 (Tier 1 추론)
- **투명성 UI:** `lib/widgets/agent_plan_card.dart` plan 시각화 + 사용자 승인
- **시뮬레이션:** 240건 기준 라우팅 정확도 100%, 위급 시나리오 도움 호출률 100%
- **백엔드:** `/api/v3/agent`, `/api/v3/memory/*` 엔드포인트 (`backend/main.py` 자동 마운트)
- **백업 태그:** `v2.1.3-baseline-pre-v3` (롤백 가능)

### 디렉토리 구조
```
C:/Users/wnsdu/Hibuudy/
├── CLAUDE.md                    ← 이 파일
├── README.md                    ← 포트폴리오
├── Hi-Buddy.py                  ← Streamlit 웹앱
├── pages/ utils/                ← Streamlit
├── backend/                     ← FastAPI (Render)
├── hi_buddy_app/                ← Flutter 앱 (메인)
│   ├── lib/
│   │   ├── screens/             ← home, coordinator, user, agent, profile, youtube, timer
│   │   ├── services/            ← haru_agent, api, database, schedule_generator, tts, weather, timer, ui_mode
│   │   ├── widgets/             ← activity_card, step_card, morning_briefing, sos_button
│   │   └── models/ theme/
│   ├── assets/data/recipes.json
│   └── android/ ios/
└── docs/                        ← 개인정보처리방침, 시뮬레이션, 리뷰
```

### 완료된 기능
- [x] 일정 만들기 (로컬 파싱 + API 폴백)
- [x] 오늘 하루 (시간 기반 활동 + 30초 갱신)
- [x] 도우미 에이전트 (Claude 맥락 기반 + 오프라인 폴백)
- [x] 나의 정보 (프로필, 식재료, 연락처, 약, 수행 기록)
- [x] 단계 체크박스 + 격려 + 일정 복사 + 수동 추가
- [x] 날씨 (wttr.in) + 아침 브리핑 + 옷 추천
- [x] 유튜브 인앱 재생 + 타이머 (레시피 연동)
- [x] 장애 강도별 UI (일반/간단/키오스크) + SOS 버튼
- [x] 활동 전환 알림 + 오프라인 폴백

### TODO (우선순위순)
- [ ] 대중교통 API + 외출 알림
- [ ] 앱 아이콘 커스텀
- [ ] Play Store 등록 (v1.3.3 검토 중)
- [ ] Firebase 동기화
- [ ] 노인 모드
- [ ] 수행 기록 리포트
- **v3.0 트랙**
  - [ ] AICore 네이티브 어댑터 (Kotlin) 작성 — `ondevice_llm.dart` 의 MethodChannel 구현체
  - [ ] Flutter `haru_agent.dart` Tier 1 라우터 통합 (Gemini Nano 시도 → 실패 시 백엔드)
  - [ ] `agent_plan_card` 메인 채팅 화면에 통합
  - [ ] 시뮬레이션 N=500 + LLM judge 평가 보강
  - [ ] 멀티 에이전트 plan을 Flutter에서 렌더 (현재는 단일 응답 텍스트만)
  - [ ] PersonaPlex 또는 부모 음성 등록 실험 (실험적)

---

## 2. 판단 기준

### 우선순위: 크래시 > UX > 차별화 > 비즈니스 > 최적화
### 규칙: YAGNI, 오프라인 우선, 접근성 (16px+/48px+), 기술 용어 금지
### 테스트: dart analyze → APK 빌드 → 바탕화면 복사 → git push

### 실패 패턴 (반복 금지)
- 패키지 리네이밍 시 Kotlin 디렉토리도 이동
- ProGuard minify OFF 유지
- Gemini 1회만 호출 (429 방지)
- API 키 절대 git에 올리지 마 (.env로만 관리)
- "할 수 있습니다" 금지, 바로 실행
- JY 자는 동안 백그라운드 에이전트 돌려

### JY 워크플로우
- "ㄱ" = 실행, "다 해라" = 병렬 실행, "봐바라" = 읽고 요약
- 중요 결정 = 3명 토론 + Opus 리뷰
- 대기 = 리뷰/테스트/개선안 자동 도출

---

## 3. 실행 로그

### 세션 1 (2026-03-22): OpenAI→Gemini 전환, Render 배포, 앱 이름 변경, README 포트폴리오화
### 세션 2 (2026-03-23~24): 크래시 수정, 전문가 패널 68/100, 100명 시뮬레이션, UX 5개 수정, 기능 5개 추가
### 세션 3 (2026-03-25~27): v2.0 에이전트 전환, sqflite DB, Claude 에이전트, 날씨/유튜브/타이머/UI모드/SOS, +6000줄
### 세션 4 (2026-05-08): **v3.0 멀티 에이전트 + Nemotron-Personas-Korea 검증 + Mem0 3-tier + Gemini Nano 브리지 + 투명성 UI** — 신규 모듈 12개, 백엔드 6개 엔드포인트, 시뮬레이션 240건 라우팅 100%
### 세션 5 (2026-05-08~09): **D1-D3 디자인 시스템 일관 적용 시작** — HaruText 7개 const + HomeUserScreen + step_card 키오스크 single-focus + intl 한국어 locale 잠재 버그 수정
### 세션 6 (2026-05-14~22): **v1.4 「메이트」 UX 리디자인 풀 마이그레이션** — HaruTokensV2 (warm coral) + 9 화면 + 5 위젯 + 4 그룹 컬러 패밀리 + 그라데이션/이모지/H1 클러스터 폐기. 12 commits. UX 점수 55→75.
### 세션 6 도구 통합 (2026-05-22): **claude-research-engine v2 자산 통합** — `.claude/hooks/require_human_gate.sh` (위험 명령 차단) + `.claude/commands/` 4개 (ux-status, ux-screenshot, ux-commit-check, v3-deploy-check) + `HANDOFF.md` (새 세션 단일 진입점) + `docs/JY_WAKEUP.md` 표준화

---

## 4. VLA 루프

```
1. CLAUDE.md 읽기 (V)
2. TODO 중 임팩트 최고 판단 (L)
3. 실행 + 빌드 + 테스트 (A)
4. 로그 기록 + 다음 액션 제안
```

---

## 5. 기술 환경

```
Flutter: C:/flutter/bin/flutter.bat
Android SDK: C:/Users/wnsdu/AppData/Local/Android/Sdk
Java: C:/Program Files/Android/Android Studio/jbr
Python: C:/Users/wnsdu/anaconda3/python.exe
GitHub: RyanAhn533/Hibuudy

빌드:
  export JAVA_HOME="/c/Program Files/Android/Android Studio/jbr"
  export ANDROID_HOME="$LOCALAPPDATA/Android/Sdk"
  flutter build apk --release
  → C:/Users/wnsdu/Desktop/하루메이트.apk

API 키: .env 또는 Render 환경변수에서 관리 (절대 git에 올리지 말 것)

에뮬레이터:
  /c/Users/wnsdu/AppData/Local/Android/Sdk/emulator/emulator.exe -avd Medium_Phone_API_36.1 -no-snapshot
```

---

## 6. 도구 통합 (claude-research-engine v2)

### 안전 가드 — Hook

`.claude/hooks/require_human_gate.sh` (executable):
- git push --force / git reset --hard / rm -rf / 키스토어 삭제 / Render 직접 배포 자동 차단
- "다 적용했다" 사고 방지 (UI commit 시 analyze/build 통과 경고)
- 활성화: `.claude/settings.json` 에 PreToolUse Bash hook 등록 (JY 직접 작성 필수, Claude 자기수정 차단)

### 슬래시 명령

| 명령 | 용도 |
|---|---|
| `/ux-status` | 잔여 양산형 패턴 grep + 빌드 산출물 |
| `/ux-screenshot [화면]` | APK 빌드 + 설치 + 캡처 |
| `/ux-commit-check` | analyze + build + diff 게이트 |
| `/v3-deploy-check` | Render + v3 엔드포인트 진단 |

### 핵심 문서 (필수 진입점)

1. **`HANDOFF.md`** — 새 세션/환경 단일 진입점 (5분 부팅)
2. **`docs/JY_WAKEUP.md`** — 직전 세션 종료 상태 + Pending Gates
3. **`docs/UX_v1.4_PROGRESS.md`** — UX 90 로드맵 진척

---

## 6. 비즈니스

- 스토리: 서울청년기획봉사단 2기 → TV → 연세대 초청 → 앱 독자 개발
- 소유권: Flutter 앱 = JY 100% 소유
- 외주 견적: 3,000~4,000만원
- 타겟: 발달장애인 25만 + 독거 노인 180만
- 수익: 무료(0원) / 베이직(2,900원) / 프리미엄(4,900원) / 기관(15만원)
