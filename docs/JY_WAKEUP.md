# JY 기상 summary

> **마지막 갱신:** 2026-09-06 (세션 7 — 4개월 공백 후 팔로우업 + 리서치 + v1.5 「4타일」 자율 구현 3라운드)
> **세션:** JY "공부하고 올 테니 최대한 디벨롭, 리뷰·검증 3회" 권한 → 자율 진행

---

## TL;DR (5줄)

1. **v1.5 루트 4타일 홈 + Assistive Access 구조 구현·에뮬 검증 완료** (지금|다음 2칸, 하단 고정 뒤로/홈, 도움 탭, 오늘 일과, 타임아웃 0). 3 commits, 런타임 예외 0.
2. **리서치 2편**: `docs/RESEARCH_UX_REFERENCE_2026-09.md` (수요통계·벤치마크·12원칙·IA), `docs/COMPETITIVE_TECH_ROADMAP_2026-09.md` (「보통의 하루」 해부 + SOTA 기술 로드맵 P0~P3).
3. **🔴 Render 백엔드 서스펜드** (503 Service Suspended). 대시보드 로그인 필요 → JY 직접.
4. **✅ 브랜치 `feature/uiux-polish-v134` origin에 push 완료** (0a62e02, 17 commits). main 대비 1 behind (README 9-01 커밋) — 머지 전 rebase.
5. **「보통의 하루」는 베낀 게 아님** — 알람+사진/NFC 인증 3종, 로펌 계열, 45명 기관 배포. 우리가 뒤진 건 "완료 인증"과 "실사용 데이터" 둘. 11월 검증 발표 추적.

---

## ⚠️ JY 직접 해야 할 것

1. **Render 대시보드** → hibuudy.onrender.com 서스펜드 사유 확인·재가동 (Free hours / 미배포 정리 / 결제). 앱 테스터가 지금 일정 생성·TTS 못 씀.
2. **`.claude/settings.json`** 생성 (HANDOFF §1 명령 복붙, 5분). hook 4개월째 미작동.
3. ~~push 확인~~ ✅ 완료. 머지 시 `git rebase origin/main` 먼저.
4. 결정 4개 (COMPETITIVE_TECH_ROADMAP §6): 완료 인증 기본값 / 보호자 목소리 클로닝 동의 문구 / Wear OS 기기 / 서울시복지재단 접촉 시점.

---

## 🎯 한 번에 보기

```bash
cd /c/Users/wnsdu/Hibuudy
git log --oneline -4                                   # bb00ed2 R1, fbc3ea3 R2, (R3)
ls docs/screenshots/v15_*                              # 에뮬 캡처 11장
cat docs/COMPETITIVE_TECH_ROADMAP_2026-09.md | head -40
```

에뮬 검증 루틴 (이번 세션에서 확정, `/ux-screenshot` 갱신 필요):
```bash
# 에뮬 저장소 5.8G 중 5.1G 사용 → install -r 이 조용히 실패함. 반드시 uninstall → install.
flutter build apk --debug --target-platform android-x64      # 204MB → 179MB
adb uninstall com.harumate.care && adb install build/app/outputs/flutter-apk/app-debug.apk
# 당사자 역할 + 오늘 일정 시드: scratchpad/seed_prefs.py (기기 시계 UTC 기준)
```

---

## 🔥 이번 세션 변경 (3 라운드)

### Round 1 `bb00ed2` — 구조
- `HomeUserScreen` 루트 4타일 (지금 할 일 / 오늘 일과 / 도움 / 메이트) + grid⇄row 토글(저장)
- `NowNextCard` 지금|다음 2칸 + 남은시간 링 (1분 갱신, 색 고정)
- `HaruBottomBar` 당사자 하단 고정 [뒤로][홈] — user/today/help/agent/timer
- `HelpScreen` 1탭 전화/문자/SOS + 감정 보드 + 기다리는 중 카드
- `TodayScreen` 회색화 + simple/kiosk 페이지 버튼
- `HaruFeedback` 스낵바 타임아웃 제거(확인 버튼)
- `buildAppTheme` 전역 V2 (Gate 2) · home_screen 이모지→IconData (Gate 3)

### Round 2 `fbc3ea3` — 리뷰 반영 (cognitive-a11y 12원칙 + HIG)
- R2: user/agent/step/timer 아이콘 단독 버튼 전부 아이콘+라벨 56pt
- R3: self 역할 상단 뒤로 제거 (하단 바만)
- P6: UserScreen 활동 헤더/타임라인 이모지 → 픽토
- R11: 마지막 그라데이션 제거 → **전체 0건**
- 카피 클러스터 정리 (오늘 하루 빈 화면·오프라인 배너·메이트 hint/오류)

### Round 3 `0a62e02` — 잔여
- 날씨 옷차림 카피 친구 톤 · `_headerText` 전 타입 라벨 · 체크박스 48pt

### Round 3b — `/code-review medium bb00ed2` 8건 반영 (실제 버그 5 + 위생 3)
- **backend**: `/api/v3/*` 가 bearer 인증 없이 마운트되던 것 → `dependencies=[Depends(verify_token)]` + 기본 OFF(`USE_V3_ORCHESTRATOR=true` 명시 시만, 실패 시 부팅 중단)
- **AndroidManifest**: `<queries>` tel/sms/https 추가 — Android 11+ 에서 `canLaunchUrl` 이 항상 false 라 SOS/전화/문자가 전부 실패하던 잠재 버그
- **HomeUserScreen**: 1분 타이머로 지금/다음 재계산 (켜둔 채 시각 넘기면 stale 이던 것) · SOS FAB 제거(도움 타일이 대체, simple 모드 메이트 타일 가림 방지)
- **TodayScreen**: 페이지 모드 카드 Flexible + ActivityCard maxLines 2 (큰 글자 오버플로)
- **hook**: python 프로브(Store 스텁 회피) · fail-closed · `--force-with-lease` 허용 앵커. 자가 테스트 4/4 통과. **settings.json 등록은 여전히 JY**
- agent_plan_card 이모지·12px 제거 (미사용 위젯이지만 /ux-status 회귀 지표 오염 방지)
- 미반영: "v3/ 를 커밋하라" — JY 결정 사안 (v3 코드 830KB, 데이터는 gitignore 됨)

### 도구
- `.claude/skills/apple-design/` (dickwu, vendored) — HIG 53문서 리뷰어
- `.claude/skills/harumate-cognitive-a11y/SKILL.md` — 12원칙 감사 (우리 것)
- `.claude/skills/_flutter_official/`, `_ecc/` — 참조용 (gitignore)
- `/ux-status` R-grep 추가, `/ux-commit-check` `git add -A` 제거 (v3 6GB 사고 방지)

---

## 🚧 Pending Gates (다음 세션)

1. Render 재가동 (JY)
2. settings.json (JY)
3. **P0-2 완료 인증 옵션** (사진/NFC, 기관 모드 ON) — 로드맵 §4
4. **P0-3 이행률 로그** (sqflite 1테이블 + 코디 홈 문장형 요약)
5. **P0-4 3지표 계측** (완료율·오류·만족)
6. `/ux-screenshot` 명령을 uninstall→install + seed 방식으로 갱신
7. ARASAAC/국내 심볼 (기존 Gate 4), M4 모션 잔여

---

## 📊 점수 (자체 평가)

| 영역 | 세션 6 | 세션 7 | 90 목표 |
|---|---|---|---|
| UX/UI | 75 | **82** (4타일·하단바·2칸·R1~R11 통과) | 90 |
| 접근성 | 72 | **80** (아이콘+라벨 100%, 타임아웃 0, 48pt) | 88 |
| 검증 | 60 | 60 (실사용자 0, 계측 미착수) | 80 |
| 배포/운영 | 60 | **40** (Render 서스펜드) | 80 |

**문서 끝.** 매 세션 종료 시 갱신.
