---
description: 하루메이트 UX 마이그레이션 + 코드 상태 한 번에 확인
allowed-tools: Bash(git:*), Bash(grep:*), Bash(wc:*), Bash(find:*), Grep
argument-hint: (없음)
---

```bash
echo "=== 브랜치 + 최근 5 커밋 ==="
cd /c/Users/wnsdu/Hibuudy
git branch --show-current
git log --oneline -5

echo ""
echo "=== 잔여 양산형 패턴 (UX 점수 디버그) ==="
cd hi_buddy_app
echo "인라인 fontSize: $(grep -rcE 'fontSize: [0-9]+' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "하드코딩 Color(0xFF: $(grep -rcE 'Color\(0xFF' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "이모지 (사용자 화면): $(grep -rcE "['\"][⏳✅🚨💡🎉🔥⚠📌📅🏠👨👩👶🎯💪🍎📞⭐⭕❌📺💬👋🧩📝⚙️]" lib/screens/ lib/widgets/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "H1 ~보세요 클러스터 (직접 Text): $(grep -rcE "Text\('[^']*(보세요|예요|볼까요)" lib/screens/ lib/widgets/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "그라데이션: $(grep -rcE 'LinearGradient|RadialGradient' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"

echo ""
echo "=== 인지접근성 12원칙 자동 grep (docs/RESEARCH_UX_REFERENCE_2026-09.md §3.2) ==="
USER_FILES="lib/screens/home_user_screen.dart lib/screens/user_screen.dart lib/screens/today_screen.dart lib/screens/help_screen.dart lib/screens/agent_screen.dart lib/screens/timer_screen.dart lib/widgets"
echo "R2 아이콘 단독 IconButton (당사자 화면): $(grep -rc 'IconButton(' $USER_FILES 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "R3 하단 고정 바 적용 화면: $(grep -rl 'HaruBottomBar.maybe' lib/screens 2>/dev/null | wc -l) / 5 (user, today, help, agent + timer 예정)"
echo "R4 숨은 제스처 Dismissible/onLongPress: $(grep -rcE 'Dismissible\(|onLongPress' lib/screens lib/widgets 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "R5 직접 showSnackBar (당사자 화면, HaruFeedback 우회): $(grep -rc 'showSnackBar(' $USER_FILES 2>/dev/null | grep -v haru_feedback | awk -F: '{s+=$2} END {print s}')"
echo "R8 Drawer/TabBar: $(grep -rcE 'Drawer\(|TabBar\(' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "R11 그라데이션: $(grep -rcE 'LinearGradient|RadialGradient' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"

echo ""
echo "=== 디자인 시스템 적용률 (HaruTokensV2) ==="
echo "V2 토큰 사용 위치: $(grep -rc 'HaruTokensV2\.' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "V1 토큰 잔여 (alias-first 정책): $(grep -rcE 'HiBuddyColors\.|HaruTokens\.(n[0-9]|primary|white)' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"

echo ""
echo "=== 빌드 산출물 ==="
APK=build/app/outputs/flutter-apk/app-debug.apk
[ -f "$APK" ] && echo "Debug APK: $(stat -c '%y' $APK | cut -d. -f1) ($(du -h $APK | cut -f1))" || echo "Debug APK: 없음 (빌드 필요)"
```

읽은 후:
- **잔여 패턴이 늘었으면 회귀.** 즉시 보고.
- 인라인 fontSize > 100 → M2 마이그레이션 미완. 작업 우선순위.
- 이모지 > 5 → M3 미완.
- V1 alias 사용은 정상 (deprecated 정책).
- APK 빌드 1시간 넘었으면 새로 빌드 권장.
- R4/R5/R8/R11 은 0 이어야 정상. 늘어나면 Blocker (harumate-cognitive-a11y 스킬로 재검토).

JY 5초 안에 현재 상태 파악 가능하도록 보고.
