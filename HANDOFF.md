# 하루메이트 — Master Handoff

> **목적:** 새 Claude 세션 또는 새 환경에서 **5분 안에 모든 상황 파악 + 즉시 작업 재개** 가능하도록 설계한 단일 진입점.
> **마지막 갱신:** 2026-05-22
> **읽는 순서:** 이 파일 → CLAUDE.md → docs/JY_WAKEUP.md → docs/UX_v1.4_PROGRESS.md

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
컨셉       : 「메이트」 (친구 톤, warm coral + warm-tinted neutral, MUJI 절제)
```

---

## 1. 즉시 실행 — 새 환경 부팅

```bash
cd /c/Users/wnsdu/Hibuudy

# 0) 현재 상태 5초 파악
git branch --show-current                      # feature/uiux-polish-v134 (UI 작업 중)
git log --oneline -5                           # 최근 변경
git status                                     # 미커밋 변경

# 1) 핸드오프 문서 (5분)
cat HANDOFF.md                                  # 이 파일
cat docs/JY_WAKEUP.md                           # 직전 세션 종료 상태
cat docs/UX_v1.4_PROGRESS.md | head -80         # UX 진행 상세

# 2) 슬래시 명령 사용 가능 (settings.json 박힌 후)
# /ux-status / /ux-screenshot / /ux-commit-check / /v3-deploy-check
```

**⚠️ settings.json 우선 작성 (Claude Code 자기수정 차단으로 자동 작성 불가):**
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
│  ├ LLM 캐스케이드: Claude Haiku 4.5 → Gemini 2.0 → Groq      │
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

### 진행 (12 commits)

```
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

**점수:** UX/UI 55 → **75** (목표 90까지 -15).

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

## 7. Pending Gates (JY 결정 받을 거)

1. **settings.json 박기** (5분) ← Claude Code 자동 차단, JY 직접
2. **buildAppTheme() 전역 ElevatedButton V2** (30분) — "시작할게요" 등 잔여 v1 primary 버튼 전역 코랄 통일
3. **작은 카드 이모지** (`icon: '📝'/'📺'/'💬'/'⚙️'` string → IconData) 30분
4. **ARASAAC 픽토 다운로드** (1-2시간 + CC BY-NC-SA 라이선스 표기)
5. **M4 모션** (5일) — 카운트다운 시각화 + 활동 전환 의식
6. **에뮬 캡처 5장** — 일정 데이터 + 키오스크 모드 토글 필요

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
# 1. 환경 부팅 (1분)
cd /c/Users/wnsdu/Hibuudy
git status
git log --oneline -5

# 2. settings.json 박기 (5분, 처음만)
# 위 §1의 cat > .claude/settings.json 명령

# 3. 상태 점검 (1분)
/ux-status                                     # 또는 cat docs/JY_WAKEUP.md

# 4. 작업 선택 (위 §7 Pending Gates 중 하나)
#    - 최우선: buildAppTheme() 전역 V2 매핑 (시각 임팩트 최대)
#    - 또는 작은 카드 이모지 정리
#    - 또는 ARASAAC 픽토

# 5. 변경 후 commit 게이트
/ux-commit-check                               # analyze + build + diff 자동
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

## 12. 최종 점수 (자체 평가)

| 영역 | 점수 |
|---|---|
| 기술 스택 / 아키텍처 | 88 |
| 코드 품질 | 75 |
| **UX / UI** | **75** (v1.4 진행 중, 목표 90) |
| 접근성 | 72 |
| 검증 / 테스팅 | 60 (실사용자 0) |
| 보안 | 78 |
| 성능 | 70 |
| 배포 / 운영 | 60 |
| 비즈니스 / 제품 | 35 (사용자 0) |
| 차별화 / 시장 적합성 | 80 |
| **종합** | **~73** (Indie 출시 임박 사이드 프로젝트 상위) |

→ **다음 게이트:** 사용자 12명 확보 (Play 정식 출시) + UI v1.4 완성 (M3-M5).

---

**문서 끝.**
**다른 모든 문서는 이 문서에서 출발한다.**
