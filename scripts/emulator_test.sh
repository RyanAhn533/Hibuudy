#!/bin/bash
# ─────────────────────────────────────────────────────────
# 하루메이트 에뮬레이터 자동 테스트 스크립트
# ADB로 설치 + 탭 시뮬레이션 + 스크린샷 자동 수집
# ─────────────────────────────────────────────────────────

set -e

ADB="C:/Users/wnsdu/AppData/Local/Android/Sdk/platform-tools/adb.exe"
APK="C:/Users/wnsdu/Desktop/하루메이트-v1.1.0-final.apk"
OUT_DIR="C:/Users/wnsdu/Hibuudy/assets/test_screenshots"
PKG="com.harumate.app"

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/*.png

shot() {
    local name="$1"
    local delay="${2:-1}"
    sleep "$delay"
    "$ADB" exec-out screencap -p > "$OUT_DIR/$name.png"
    echo "   📸 $name.png"
}

tap() {
    "$ADB" shell input tap "$1" "$2"
}

type_text() {
    "$ADB" shell input text "$1"
}

back() {
    "$ADB" shell input keyevent KEYCODE_BACK
}

# ─────────────────────────────────────────────────────────
# 0. Setup
# ─────────────────────────────────────────────────────────
echo "=== [0] 환경 준비 ==="

# 기존 앱 삭제 (깨끗한 첫 실행 상태)
"$ADB" uninstall "$PKG" 2>/dev/null || true
echo "   ✓ 기존 앱 제거"

# APK 설치
echo "   → APK 설치 중 (약 1분)..."
"$ADB" install -r "$APK" 2>&1 | tail -2
echo "   ✓ 설치 완료"

# 화면 unlock
"$ADB" shell input keyevent 82
sleep 1

# 앱 실행
"$ADB" shell am start -n "$PKG/.MainActivity"
echo "   ✓ 앱 실행"
sleep 5  # 초기 로딩

# 해상도 확인 (탭 좌표 기준)
RES=$("$ADB" shell wm size | grep -oP '\d+x\d+' | head -1)
echo "   해상도: $RES"

# ─────────────────────────────────────────────────────────
# 1. 온보딩 Flow
# ─────────────────────────────────────────────────────────
echo ""
echo "=== [1] 온보딩 Flow ==="

shot "01_welcome" 2
echo "   → '시작할게요' 버튼 탭"
tap 540 1800  # 하단 중앙 버튼 (하단에서 100px 위)
shot "02_role_selection" 2

echo "   → '가족이나 학생을 위해' 선택"
tap 540 700  # 첫 번째 옵션
sleep 1
shot "03_role_coord_selected" 0.5

echo "   → '다음' 버튼"
tap 540 1800
shot "04_profile_name" 2

echo "   → 이름 입력 '유진'"
tap 540 750  # 이름 입력 필드
sleep 1
type_text "유진"
sleep 1
shot "05_name_entered" 0.5

echo "   → '크게' 선택"
tap 540 1050  # 크기 선택 2번째
sleep 0.5
shot "06_size_large" 0.5

echo "   → '다음'"
tap 540 1800
shot "07_pair_code" 2

echo "   → '연결됐어요' (또는 '나중에 할게요')"
tap 540 1800  # 맨 아래 '연결됐어요'
shot "08_home_after_onboarding" 3

# ─────────────────────────────────────────────────────────
# 2. 코디 홈 탐색
# ─────────────────────────────────────────────────────────
echo ""
echo "=== [2] 코디 홈 ==="

shot "09_coord_home" 1

echo "   → '일정 만들기' 탭"
tap 270 700  # 좌상단 그리드 카드
shot "10_coord_input" 3

echo "   → '일정표 만들기' 버튼 (AI 호출)"
tap 540 1700
sleep 8  # AI 처리 대기
shot "11_schedule_generated" 1

back
sleep 1
shot "12_back_to_home" 1

# ─────────────────────────────────────────────────────────
# 3. 미리보기 (당사자 화면)
# ─────────────────────────────────────────────────────────
echo ""
echo "=== [3] 당사자 미리보기 ==="

echo "   → '미리보기' 탭"
tap 810 700  # 우상단 그리드
shot "13_user_view" 3

# ─────────────────────────────────────────────────────────
# 4. 프로필 + 도우미
# ─────────────────────────────────────────────────────────
back
sleep 2
echo ""
echo "=== [4] 프로필 ==="
tap 810 900  # 프로필 카드
shot "14_profile" 2

back
sleep 2

# 앱 다시 시작 — 온보딩 리셋하려면 uninstall+reinstall
# 당사자 모드도 보려면 프로필에서 역할 변경 필요
# TODO: 당사자 모드 테스트 추가

# ─────────────────────────────────────────────────────────
# 5. Logcat 에러 수집
# ─────────────────────────────────────────────────────────
echo ""
echo "=== [5] 에러 로그 수집 ==="
"$ADB" logcat -d -b crash | tail -50 > "$OUT_DIR/logcat_crash.txt" 2>&1 || true
"$ADB" logcat -d "*:E" | grep -i "harumate\|flutter" | tail -30 > "$OUT_DIR/logcat_errors.txt" 2>&1 || true
echo "   ✓ 로그 저장됨"

echo ""
echo "=== 완료 ==="
echo "스크린샷: $OUT_DIR"
ls "$OUT_DIR" | head -20
