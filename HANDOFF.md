# 하루메이트 — Master Handoff

> **목적:** 새 Claude 세션 또는 새 환경에서 **5분 안에 모든 상황 파악 + 즉시 작업 재개** 가능하도록 설계한 단일 진입점.
> **마지막 갱신:** 2026-09-06 밤 (세션 7 종료)
> **읽는 순서:** 이 파일 → docs/JY_WAKEUP.md (직전 종료 상태) → CLAUDE.md → 작업별 문서
> **세션 7 요약:** 4개월 공백 복구(Render·LLM·미푸시) + 리서치 2편 + v1.5 「4타일」 + P0 완료인증·수행기록·3지표 + 백엔드 5단 캐스케이드 + 스토어 등록정보 v1.5. 하네스는 §12.

---

## 0. 30초 정체성

```
프로젝트   : 하루메이트 (HaruMate)
정체성     : 발달장애 당사자가 보호자 지속 지시 없이 하루 일과 따라가도록 돕는 AI 일과 보조 앱
경로       : C:\Users\wnsdu\Hibuudy
저장소     : RyanAhn533/Hibuudy
백엔드     : https://hibuudy.onrender.com (Render Free)
패키지     : com.harumate.care
v2.1.3     : 안정 (Play Console v1.3.3 비공개 테스트)
v3.0-dev   : 멀티 에이전트 백엔드 (로컬 OK, Render 미배포)
v1.4-dev   : UX/UI 「메이트」 리디자인 (현재 브랜치 feature/uiux-polish-v134)
v1.5       : 루트 4타일 + Assistive Access 구조 (2026-09-06, R1~R11 통과, 에뮬 검증)
백엔드     : Render 복구 (2026-09-06, 무료계정 카드 등록). 정지 원인 = 결제수단 미등록
컨셉       : 「메이트」 (친구 톤, warm coral + warm-tinted neutral, MUJI 절제)
```

---

## 1. 즉시 실행 — 새 환경 부팅

```bash
cd /c/Users/wnsdu/Hibuudy

# 0) 상태 5초
git fetch -q && git status --short | grep -v "^?? v3/"     # 비어야 정상 (v3/ 는 의도적 언트랙)
git log --oneline -5                                       # feature/uiux-polish-v134
git log origin/main --oneline -3                           # 서버 배포 브랜치 (Render 자동 배포)

# 1) 핸드오프 (5분)
cat docs/JY_WAKEUP.md                                      # 직전 세션 종료 상태 + JY 할 일
cat docs/COMPETITIVE_TECH_ROADMAP_2026-09.md | head -60    # 다음 개발 우선순위 P0~P3

# 2) 서버 생사
curl -s https://hibuudy.onrender.com/health                # llm_providers 에 true 가 하나는 있어야 AI 동작

# 3) 앱 검증 (에뮬)
bash tools/emu/run_ui_check.sh self 0 ui_                  # 빌드→깨끗한 설치→시드→캡처→예외 0
cd hi_buddy_app && /c/flutter/bin/flutter.bat test         # 54개 (api_integration 3건은 서버 의존)

# 4) 백엔드 검증 (키 없이도)
cd backend && /c/Users/wnsdu/anaconda3/python.exe -m pytest test_cascade.py -q   # 6/6
```

**⚠️ settings.json (JY 직접, 아직 미생성 — hook 은 고쳐놨고 등록만 남음):**
```bash
cat > .claude/settings.json <<'EOF'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": ".claude/hooks/require_human_gate.sh"}]
      }
    ]
  }
}
EOF
```

**브랜치 규칙 (세션 7 확정):**
- 앱 작업 = `feature/uiux-polish-v134` (origin 추적). 서버 배포 = `main` (Render 가 `backend/` Docker 로 자동 배포, GitHub Pages 가 `docs/` 서빙).
- 서버·문서 핫픽스를 main 에 올릴 때: `git checkout -B hotfix/<이름> origin/main && git checkout feature/uiux-polish-v134 -- <파일> && git commit && git push origin hotfix/<이름>:main`. **앱 코드는 main 에 섞지 않는다** (v1.5 머지는 JY 결정).
- main push 는 자동모드 분류기가 막을 수 있음 → JY 가 "푸시 권한 준다" 명시하면 진행.

---

## 2. 시스템 전체 (3층)

```
┌──────────────────────────────────────────────────────────────┐
│ Flutter App (com.harumate.care, v1.3.3+6)                    │
│  ├ 10 screens / 7 widgets / 16 services                       │
│  ├ HaruTokens v1 (안정) + HaruTokensV2 「메이트」 (v1.4 진행)  │
│  ├ UI 모드 3 (normal/simple/kiosk)                            │
│  ├ sqflite 7테이블 + flutter_local_notifications + Pretendard │
│  └ Tier 0 (오프라인) / Tier 1 (Gemini Nano, Kotlin 미작성)    │
│                          ↓ HTTPS Bearer                       │
├──────────────────────────────────────────────────────────────┤
│ FastAPI 백엔드 (Render Free, hibuudy.onrender.com)            │
│  ├ /api/* 16 엔드포인트 + slowapi rate limit                  │
│  ├ LLM 5단 캐스케이드 (ENV LLM_CASCADE): gemini→upstage→groq→ │
│  │   openrouter→cerebras. 실제 1차 응답자 = Upstage solar-pro3   │
│  ├ 에이전트 대화: Claude Haiku 4.5                              │
│  ├ Edge TTS (ko-KR) + SHA256 캐시                            │
│  └ /api/v3/* (멀티 에이전트, USE_V3_ORCHESTRATOR=true 옵트인) │
├──────────────────────────────────────────────────────────────┤
│ v3 검증 (개발 환경, 배포 X)                                   │
│  ├ Nemotron-Personas-Korea 281,992 (한국 통계청 grounding)   │
│  ├ 5 시나리오 × N 시뮬레이션 100% (240건)                    │
│  └ Mem0 3-tier 메모리 (SQLite, Zep temporal)                 │
└──────────────────────────────────────────────────────────────┘
```

상세: `docs/ARCHITECTURE_FULL.md` (722줄, 섹션 15개)

---

## 3. 현재 작업 브랜치 — `feature/uiux-polish-v134`

### 진행 (30 commits, 세션 7 = 18개)

세션 7 (2026-09-06) 핵심 커밋:
```
b40ace2  docs: 스토어 등록정보 애셋 v1.5.0 + JY_WAKEUP 밤 종료
5963c67  docs(privacy): 개인정보처리방침 v1.5 (main 에도 → GitHub Pages 라이브)
7bc1d3e  test(backend): 캐스케이드 테스트 6건 + 실측 순서 gemini→upstage→groq→openrouter→cerebras
6c7b701  feat(backend): 무료 LLM 5단 캐스케이드 + /api/metrics slowapi 부팅 버그
3593633  fix(backend): gemini-2.0-flash(06-01 셧다운)·Groq llama-3.3(08 종료) 교체
75ff63d  feat(p0): 완료 인증 사진 + 수행 기록 실제 저장(호출부 0개였음) + 3지표 주간 문장, v1.5.0+7
88b0ae0  fix: Round 3b — code-review 8건 (v3 인증 우회, Android 11+ tel/sms, stale 홈, FAB 겹침, 페이지 오버플로, hook)
0a62e02  fix: Round 3 — 날씨 카피 친구 톤 · 헤더 라벨 · 체크박스 48pt
fbc3ea3  fix(a11y): Round 2 — 아이콘+라벨 100% · 상단 뒤로 제거 · 그라데이션 0 · 이모지 0
bb00ed2  feat(ui): v1.5 루트 4타일 + Assistive Access 구조 (NowNext·하단바·도움·오늘일과·HaruFeedback·전역 V2)
```
main (서버·문서) : e0691e2 백엔드 핫픽스 3/3 → fdb2bec 개인정보처리방침 v1.5

세션 6 이전:
```
ⓝ fbc3ea3  Round 2 — R2 아이콘+라벨 100% · R3 상단 뒤로 제거 · R11 그라데이션 0 · P6 이모지 0
ⓜ bb00ed2  v1.5 루트 4타일 + NowNext 2칸 + 하단 고정 바 + 도움 탭 + 오늘 일과 + 전역 V2 테마
ⓛ 69bd4ce  M3 이모지 5건 + AI 카피 4건 폐기
ⓚ 2094809  M2 D5 잔여 6 화면 V2 매핑
ⓙ 012e78b  M2 D4 OnboardingScreen V2
ⓘ 33f8478  M2 D4 UserScreen V2 (12 토큰)
ⓗ 225897e  M2 D3 3 위젯 + 9→4 활동 그룹화
ⓖ 4daec4b  M2 D2 HomeCoordinatorScreen V2
ⓕ 74138e2  M2 D1 HomeUserScreen V2
ⓔ 2263eb6  M1 HaruTokensV2 「메이트」 (warm coral + warm-tinted)
ⓓ 9b3d5eb  🐛 intl 한국어 locale 초기화 (v2.1.3 잠재 버그 수정)
ⓒ fe4e8f1  D3 kiosk single-focus
ⓑ bfee110  D2 HomeUser 다음 활동 미리보기
ⓐ 7ef4058  D1 HaruText typography utility
```

### UX 90 로드맵 M1-M5 진척

| M | 작업 | 상태 |
|---|---|---|
| M1 | HaruTokensV2 + 회귀 가드 | ✅ 토큰 / ⏳ contrast_audit + golden test |
| M2 | 디자인 시스템 100% 적용 (9 화면 + 5 위젯) | ✅ V2 매핑 / ⏳ 잔여: 작은 카드 이모지 + buildAppTheme 전역 |
| M3 | AAC + 카피 + 일러스트 | ⏳ 카피 부분 / ❌ ARASAAC 다운로드 / ❌ 일러 |
| M4 | 모션 + 마이크로 인터랙션 | ❌ 미진행 |
| M5 | 외부 검증 + 시연 캡처 5장 | ⏳ 캡처 1.5장 / ❌ 외부 시각 테스트 (JY 보류) |

**점수:** UX/UI 55 → 75 → **82** (세션 7, 목표 90까지 -8). 접근성 72 → **80**.

---

## 4. 핵심 결정 사항 (변경 금지)

| 항목 | 결정 | 이유 |
|---|---|---|
| 컨셉 | **「메이트」** | JY 픽 (친구/버디/메이트 중). 앱 이름 통일. 「온」 폐기. |
| 색 | warm coral `#D17559` brand + warm-tinted `#FAF7F2` surface | MUJI 절제. cool blue 폐기. |
| 활동 색 | 9 → 4 그룹 (식사/신체/휴식/일과) | 양산형 무지개 폐기 |
| 마이그레이션 | v1 alias-first (HaruTokens v1 보존, V2 신규) | P4 안전 가드, 롤백 가능 |
| 외부 표현 | NVIDIA Nemotron-Personas-Korea 만 인용 | 클로드 페르소나 검증은 외부 사용 금지 |
| 카피 룰 | "~님/~보세요/~예요" 클러스터 폐기 (사용자 화면) | TTS/알림 자연 발화는 보존 |
| 이모지 | 사용자 노출 0건 (Material Symbols 통일) | P6 적출 |
| 그라데이션 | 0건 | P6 + P1 적출 |
| **당사자 UI 구조** | **Apple Assistive Access 이식**: 루트 타일 ≤4 · 아이콘+라벨 쌍 · 하단 고정 뒤로/홈 · 숨은 제스처 0 · 타임아웃 UI 0 · 삭제 없음 | 세션 7. 근거 `docs/RESEARCH_UX_REFERENCE_2026-09.md` §3 (12원칙 R1~R12) |
| **인지접근성 감사** | 당사자 화면 변경 시 `harumate-cognitive-a11y` 스킬 + `apple-design` 스킬 리뷰 필수 | R4/R5/R8/R11 = 0 이 commit 조건 |

---

## 5. 문서 인덱스 (읽는 순서)

| 우선 | 문서 | 줄 | 용도 |
|---|---|---|---|
| 1 | **HANDOFF.md** (이 파일) | — | 새 세션 단일 진입점 |
| 2 | **CLAUDE.md** | ~120 | VLA 자율 개발 에이전트 설정 + 프로젝트 상태 |
| 3 | **docs/JY_WAKEUP.md** | ~150 | 직전 세션 종료 상태 + Pending Gates |
| 4 | **docs/UX_v1.4_PROGRESS.md** | ~280 | UX 90 로드맵 진척 상세 |
| 5 | **docs/UX_100_ROADMAP.md** | ~160 | Round 2 deliberation + 5 마일스톤 |
| 6 | **docs/DESIGN_v1.4_DELIBERATION.md** | ~450 | Round 1 deliberation (7 페르소나 발산) |
| — | **docs/ARCHITECTURE_FULL.md** | 722 | 시스템 전체 구조 (15섹션) |
| — | **docs/EVOLUTION.md** | 562 | 5개월 진화사 (7 페이즈) |
| — | **docs/PERSONA_VALIDATION.md** | 461 | NVIDIA Nemotron-Personas-Korea 방법론 |
| — | **docs/ONE_PAGER.md** | 104 | 발표/공모전 1장 요약 |
| — | **docs/store-listing-v1.5.0/** | — | Play Console 스토어 등록정보 애셋 (스크린샷 6·그래픽·복붙 텍스트·README) |
| — | **.claude/skills/README.md** | — | 리뷰 하네스 (스킬 4·명령 4·hook·테스트) 사용법 |
| — | **docs/COMPETITIVE_TECH_ROADMAP_2026-09.md** | ~200 | 「보통의 하루」 해부 + 2026 SOTA 기술 로드맵 P0~P3 + 검증 설계 |
| — | **docs/RESEARCH_UX_REFERENCE_2026-09.md** | ~250 | 수요통계·벤치마크·Assistive Access/COGA 12원칙·IA 뼈대·우선순위 (2026-09 리서치) |
| — | **docs/INDEX.md** | — | docs 가이드 |

### 슬래시 명령 (settings.json 박힌 후 사용 가능)

| 명령 | 용도 |
|---|---|
| `/ux-status` | 잔여 양산형 패턴 grep + 빌드 산출물 |
| `/ux-screenshot [화면]` | APK 빌드 + 설치 + 캡처 → docs/screenshots/ |
| `/ux-commit-check` | analyze + build + diff 게이트 |
| `/v3-deploy-check` | Render + v3 엔드포인트 진단 |

---

## 6. 안전 가드 / Kill Switch

| 안전 장치 | 위치 | 비고 |
|---|---|---|
| 백업 태그 | `v2.1.3-baseline-pre-v3` | v3 작업 전 스냅샷 |
| 브랜치 격리 | `feature/uiux-polish-v134` | main 보존 |
| v1 alias | `HaruTokens` (v1) 보존 | V2와 공존, 롤백 가능 |
| Hook 차단 | `.claude/hooks/require_human_gate.sh` | git push --force / rm -rf / 키스토어 삭제 / Render 직접 배포 자동 차단 |
| ENV 토글 | `USE_V3_ORCHESTRATOR=false` | v3 라우터 즉시 무력화 |
| Git history 정리 | `bb43960`/`af9ea2a` | API 키 노출 제거 |

### 즉시 롤백

```bash
git checkout main                              # v2.1.3 안정 버전으로
git checkout v2.1.3-baseline-pre-v3            # v3 작업 전 스냅샷으로
```

---

## 7. Pending Gates — 2026-09-06 밤 기준

**JY 직접 (콘솔·계정)**
1. Play Console: v1.5.0+7 AAB 업로드됨 → "출시 시작" 확인 · 스크린샷 6장 교체 (`docs/store-listing-v1.5.0/`) · **9/30 Android 개발자 인증 등록 확인**
2. 테스터 12명 × 14일 참여 (프로덕션 재신청 조건. 거부 사유 = 참여도 부족, Gmail 08-08·08-25)
3. `.claude/settings.json` 생성 (§1)
4. API 키 rotate (채팅 노출 Cerebras·Upstage) → Render ENV. Gemini 키 재발급(현재 실패). `gemini-2.5-flash` 10/16 종료 → `GEMINI_MODEL=gemini-3.5-flash`
5. 결정: v3/ 코드 커밋 여부 · 완료 인증 기관 기본 ON 여부 · 보호자 목소리 동의 문구 · Wear OS 기기 · 서울시복지재단 접촉 시점(11월 검증 후)

**다음 개발 (COMPETITIVE_TECH_ROADMAP §4 순)**
6. R7 보호자 위저드(한 화면 한 결정) · R12 리마인더 3토글 → 12원칙 완주 (UX 82→88)
7. P0-5 NFC 인증 (nfc_manager, 실기기) · P1 온디바이스 사진 판정 (Gemini Nano Kotlin 어댑터 = CLAUDE.md v3 TODO 1)
8. APP_AUTH_TOKEN 활성화 — Render ENV + `--dart-define=API_TOKEN` 재빌드 **동시에**
9. `/api/agent` (Claude) 실호출 확인 — 세션 7 미검증

---

## 8. 메모리 룰 (절대 지킴)

| 룰 | 메모리 위치 |
|---|---|
| **"다 적용했다" = 빌드/실행/검증까지** | `feedback_apply_means_running.md` |
| 자율 결정 게이트 자제 (어제 「온」 자율 결정해서 의심받음) | (현재 세션) |
| EIGHT PT 코드 수정 전 설명+동의 필수 | `feedback_eightpt_caution.md` |
| 함부로 새 기능 추가 X (UI는 톤업 위주) | `agent_app_dev_evolution.md` |
| 빠른 실행 선호 ("ㄱ" = 실행) | `feedback_behavior_rules.md` |

---

## 9. 외부 표현 가이드 (정직성 중요)

### ✅ 써도 됨
- "NVIDIA Nemotron-Personas-Korea (한국 통계청 grounding, CC BY 4.0) 281,992 페르소나 시뮬레이션"
- "라우팅 정확도 100%, 위급 시나리오 도움 호출률 100%"
- "연세대 사회복지대학원 HEART Lab + 서부장애인종합복지관 협력"
- "온쿡 (전신) 헬로TV 보도 + 발달장애인 클래스 만족도 4.83/5"

### ❌ 쓰면 안 됨
- ~~"전문가 5인 패널 검증"~~ — Claude 페르소나
- ~~"발달장애인 100명 사용자 시뮬레이션 4.24/5"~~ — 동일
- ~~"치료 효과 입증 / 진단 가능 / 행동 개선"~~ — 의료 영역

---

## 10. 다음 세션 시작 순서 (5분)

```bash
git fetch -q && git status --short | grep -v "^?? v3/"
cat docs/JY_WAKEUP.md                      # 1) 직전 종료 상태 + JY 할 일
curl -s https://hibuudy.onrender.com/health # 2) 서버·AI 키 생사
bash tools/emu/run_ui_check.sh self 0 ui_  # 3) 앱 빌드·캡처·예외 0 (에뮬 켜고)
# 4) 작업 선택: §7 Pending Gates 6~9 또는 docs/COMPETITIVE_TECH_ROADMAP §4
# 5) 변경 후: cognitive-a11y 스킬 → /code-review → /ux-commit-check → commit (§12 리뷰 루프)
```

---

## 11. JY 작업 스타일 (메모리 종합)

- **빠른 실행 선호**: "ㄱ" = 실행, "다 해라" = 병렬 실행, "봐바라" = 읽고 요약
- **솔직한 직설 선호**: sycophancy 금지. "사기급?" 같은 질문엔 강점 + 약점 동시
- **6 프로젝트 동시 진행**: HaruMate / EIGHT PT / S-PACE 논문 / exp_003,004 / BrandSpace / BioToken
- **연구자 + 사업가 hybrid**: 학술 자산 + 사회 임팩트 둘 다
- **자동 모드 가능**: "잘테니까 알아서 해" 권한 부여 시 9시간 자율 진행 가능
- **단, 안전 룰 절대 지킴**: 메모리 박힌 룰은 어떤 경우에도 위반 X

---


## 12. 하네스 — 다음 세션에서 바로 쓰는 것 (세션 7 정리)

| 종류 | 이름 | 실행 | 용도 |
|---|---|---|---|
| 스크립트 | `tools/emu/run_ui_check.sh [self\|coordinator] [proof] [prefix]` | bash | 빌드→깨끗한 설치→시드→캡처→예외 0 (에뮬 함정 전부 반영) |
| 스크립트 | `tools/emu/seed_prefs.py` | python | 역할·이름·오늘 일정·완료사진 옵션 시드 (UTC) |
| 스크립트 | `tools/emu/tap_checkboxes.py` | python | uiautomator dump 로 체크박스 위치 찾아 탭 (좌표 탭 대신) |
| 스크립트 | `tools/store/make_store_assets.py` | python | 캡처 → 1080x1920 스토어 스크린샷 + 1024x500 그래픽 |
| 테스트 | `hi_buddy_app/test/` 54개 | `flutter test` | theme·모델·서비스 + api_integration(서버 의존 3) |
| 테스트 | `backend/test_cascade.py` 6개 | `pytest` | LLM 캐스케이드 로직 (네트워크 X) |
| E2E | `backend/e2e_backend.py` | 로컬 uvicorn 8010 + `backend/.env` 키 | 실제 공급자로 한국어 일정 생성·수정 스키마 검증 |
| 스킬 | `harumate-cognitive-a11y` | Skill | 12원칙 판정 (Blocker R3/R4/R5/R6) |
| 스킬 | `apple-design` | Skill | HIG 리뷰 (references/hig/*.md) |
| 명령 | `/ux-status` `/ux-screenshot` `/ux-commit-check` `/v3-deploy-check` | 슬래시 | 상태·캡처·커밋 게이트·서버 진단 |
| hook | `.claude/hooks/require_human_gate.sh` | settings.json 등록 후 자동 | 위험 명령 차단 (fail-closed, 자가테스트 4/4) |
| 리뷰 | `/code-review medium <commit>` | Skill | 세션 7에서 실제 버그 5건 잡음 |

**리뷰 루프**: 구현 → run_ui_check → cognitive-a11y → apple-design → code-review → 수정 → 재검증 → ux-commit-check → commit. 3라운드 기준.

**서버 검증 순서**: `pytest test_cascade.py` → `backend/.env` 에 키 넣고 `LLM_CASCADE=upstage python -m uvicorn main:app --port 8010` → `python e2e_backend.py` → main 푸시 → `curl /health` 로 배포·키 확인.

**함정 목록 (다시 밟지 말 것)**
- 에뮬 `adb install -r` 조용한 실패 → 항상 uninstall→install, `lastUpdateTime` 확인
- 모델명 하드코딩 → 전부 ENV. 분기마다 deprecation 확인 (2.0-flash 6/1, llama-3.3 8월, 2.5-flash 10/16)
- `git add -A` 금지 (v3/ 6GB) — commit-check 가 명시 add
- 조사 블로그의 "무료 한도"는 낡음 → 실호출로 확인 (Cerebras 무료 키 402)
- Git Bash curl 로 한글 JSON 보내면 인코딩 깨져 400 → python/httpx 로
- Windows `python3` 은 Store 스텁(exit 49) → anaconda 절대경로
- 키를 채팅에 붙이면 `.env`(gitignore)에만, 출력 마스킹, rotate 권고

---

## 13. 최종 점수 (자체 평가)

| 영역 | 점수 |
|---|---|
| 기술 스택 / 아키텍처 | 88 |
| 코드 품질 | 75 |
| **UX / UI** | **82** (v1.5 4타일, 12원칙 R1~R11) |
| 접근성 | 80 |
| 검증 / 테스팅 | 68 (계측 시작, 실사용자 0) |
| 보안 | 78 |
| 성능 | 70 |
| 배포 / 운영 | 65 (Render 복구·카드, LLM 5단, 인증 우회 잔존) |
| 비즈니스 / 제품 | 35 (사용자 0) |
| 차별화 / 시장 적합성 | 80 |
| **종합** | **~77** (세션 7) |

→ **다음 게이트:** 테스터 12명 × 14일 (프로덕션 승인) + R7/R12 + NFC/온디바이스 판정.

---

**문서 끝.**
**다른 모든 문서는 이 문서에서 출발한다.**
