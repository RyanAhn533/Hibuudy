---
description: UI 변경 commit 전 게이트 — analyze + build + diff 확인 필수
allowed-tools: Bash(*), Read
argument-hint: [commit message 한 줄]
---

UI/위젯/테마 변경 commit 게이트. 메모리 룰 (feedback_apply_means_running.md) 강제.

```bash
MSG="${1:-feat(ui): WIP}"
cd /c/Users/wnsdu/Hibuudy/hi_buddy_app

echo "=== 1. flutter analyze ==="
ANALYZE=$(/c/flutter/bin/flutter.bat analyze 2>&1 | tail -5)
echo "$ANALYZE"
if echo "$ANALYZE" | grep -qE "error -"; then
  echo "❌ ERROR 있음. commit 중단."
  exit 1
fi

echo ""
echo "=== 2. flutter build apk --debug ==="
BUILD=$(/c/flutter/bin/flutter.bat build apk --debug 2>&1 | tail -3)
echo "$BUILD"
echo "$BUILD" | grep -q "Built" || { echo "❌ 빌드 실패. commit 중단."; exit 1; }

echo ""
echo "=== 3. git diff stats ==="
cd /c/Users/wnsdu/Hibuudy
git diff --stat | tail -15

echo ""
echo "=== 4. 잔여 양산형 패턴 ==="
cd hi_buddy_app
INLINE=$(grep -rcE 'fontSize: [0-9]+' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')
EMOJI=$(grep -rcE "['\"][⏳✅🚨💡🎉🔥⚠📌📅🏠👨👩👶🎯💪🍎📞⭐⭕❌📺💬👋🧩📝⚙️]" lib/screens/ lib/widgets/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')
echo "인라인 fontSize: $INLINE, 사용자 화면 이모지: $EMOJI"

echo ""
echo "=== 4b. 인지접근성 자동 grep (Blocker: R4/R5/R8/R11 은 0) ==="
echo "R4 Dismissible/onLongPress: $(grep -rcE 'Dismissible\(|onLongPress' lib/screens lib/widgets 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "R8 Drawer/TabBar: $(grep -rcE 'Drawer\(|TabBar\(' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "R11 그라데이션: $(grep -rcE 'LinearGradient|RadialGradient' lib/ 2>/dev/null | awk -F: '{s+=$2} END {print s}')"
echo "→ 당사자 화면 변경 시 harumate-cognitive-a11y 스킬 + apple-design 스킬 리뷰 결과 첨부"

echo ""
echo "=== 5. commit 준비 완료 — 실행 ==="
cd /c/Users/wnsdu/Hibuudy
git add hi_buddy_app/lib hi_buddy_app/pubspec.yaml docs .claude HANDOFF.md CLAUDE.md
echo "(v3/ 데이터·DB는 .gitignore. git add -A 금지 — 6GB 사고 방지)"
echo "→ git commit -m \"$MSG\" 직접 실행 (자동 실행 X, JY가 git push 같은 거 가드)"
```

읽은 후:
- 위 5단계 모두 통과해야 commit 권장
- 인라인 fontSize 또는 이모지 늘어났으면 회귀 — 직전 변경 검토
- JY가 직접 `git commit` 실행하거나 명시 동의 후 진행
