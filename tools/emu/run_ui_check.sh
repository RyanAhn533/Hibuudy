#!/usr/bin/env bash
# run_ui_check.sh — 에뮬 UI 검증 루틴 (세션 7에서 확정, 2026-09-06)
#
# 왜 이 순서인가:
#   - 에뮬 저장소가 91% 라 `adb install -r` 이 INSUFFICIENT_STORAGE 로 *조용히* 실패 → 스크린샷이 옛 빌드였던 사고.
#     → 항상 uninstall 후 install.
#   - x64 전용 debug 빌드 (204MB → 179MB).
#   - 기기 시계 UTC → seed_prefs.py 가 UTC 기준 일정 생성.
#   - 검증 = 캡처 Read + logcat 'ErrorReporter:flutter' 카운트 0.
#
# 사용:
#   bash tools/emu/run_ui_check.sh [self|coordinator] [proof 0|1] [캡처접두어]
#   예) bash tools/emu/run_ui_check.sh self 1 v16_
#
# 에뮬이 안 켜져 있으면 먼저:
#   /c/Users/wnsdu/AppData/Local/Android/Sdk/emulator/emulator.exe -avd Medium_Phone_API_36.1 -no-snapshot -no-audio -no-boot-anim &
set -euo pipefail
export MSYS_NO_PATHCONV=1
ROLE="${1:-self}"; PROOF="${2:-0}"; PREFIX="${3:-ui_}"
ROOT=/c/Users/wnsdu/Hibuudy
APP=$ROOT/hi_buddy_app
ADB=/c/Users/wnsdu/AppData/Local/Android/Sdk/platform-tools/adb.exe
PY=/c/Users/wnsdu/anaconda3/python.exe
FLUTTER=/c/flutter/bin/flutter.bat
SS=$ROOT/docs/screenshots
PKG=com.harumate.care
DEV=emulator-5554

echo "=== 0. 에뮬 부팅 대기 ==="
for i in $(seq 1 40); do
  b=$($ADB -s $DEV shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
  [ "$b" = "1" ] && break; sleep 5
done
[ "${b:-}" = "1" ] || { echo "❌ 에뮬 없음. 위 emulator 명령으로 먼저 켜기"; exit 1; }

echo "=== 1. analyze + x64 debug build ==="
cd "$APP"
$FLUTTER analyze --no-pub 2>&1 | grep -E "error -|warning -|issues found" || true
$FLUTTER build apk --debug --target-platform android-x64 2>&1 | grep -E "✓|rror" | tail -2

echo "=== 2. 깨끗한 설치 (uninstall → install) ==="
$ADB -s $DEV uninstall $PKG >/dev/null 2>&1 || true
$ADB -s $DEV install build/app/outputs/flutter-apk/app-debug.apk 2>&1 | tail -1
$ADB -s $DEV shell dumpsys package $PKG | grep lastUpdateTime

echo "=== 3. 최초 실행(DB 생성) → 시드 ($ROLE, proof=$PROOF) ==="
$ADB -s $DEV shell am start -n $PKG/.MainActivity >/dev/null; sleep 6
$ADB -s $DEV shell am force-stop $PKG
$PY "$ROOT/tools/emu/seed_prefs.py" "$ROLE" "$PROOF" 2>/dev/null | tail -1

echo "=== 4. 실행 + 홈 캡처 ==="
$ADB -s $DEV logcat -c
$ADB -s $DEV shell am start -n $PKG/.MainActivity >/dev/null; sleep 9
mkdir -p "$SS"
$ADB -s $DEV exec-out screencap -p > "$SS/${PREFIX}01_home.png"
echo "cap $SS/${PREFIX}01_home.png"

echo "=== 5. 런타임 예외 ==="
N=$($ADB -s $DEV logcat -d -s flutter 2>&1 | grep -c 'ErrorReporter:flutter' || true)
echo "flutter errors: $N"
[ "$N" = "0" ] || $ADB -s $DEV logcat -d -s flutter 2>&1 | grep -A3 'ErrorReporter:flutter' | head -12

cat <<EOF

다음 (수동/추가 스크립트):
  탭 좌표는 1080x2400 기준. 홈 4타일: 지금(282,1188) 오늘(796,1188) 도움(282,1938) 메이트(796,1938) / 레이아웃 토글(900,214)
  체크박스는 좌표 대신: $PY $ROOT/tools/emu/tap_checkboxes.py   (uiautomator dump 로 위치 탐색)
  캡처:  $ADB -s $DEV exec-out screencap -p > $SS/${PREFIX}NN_name.png
EOF
