#!/bin/bash
# ─────────────────────────────────────────────
# Hi-Buddy 릴리즈 빌드 스크립트
# 사용법: bash scripts/build_release.sh [서버URL] [인증토큰]
#
# 예시:
#   bash scripts/build_release.sh https://hibuddy-api.onrender.com my-secret-token
# ─────────────────────────────────────────────

set -e

API_BASE_URL="${1:-http://10.0.2.2:8000}"
API_TOKEN="${2:-}"

echo "=== Hi-Buddy 릴리즈 빌드 ==="
echo "API_BASE_URL: $API_BASE_URL"
echo ""

# 키스토어 확인
if [ ! -f "android/key.properties" ]; then
    echo "[ERROR] android/key.properties 가 없습니다."
    echo "        먼저 scripts/generate_keystore.sh 를 실행하세요."
    exit 1
fi

# 빌드 인자
DART_DEFINES="--dart-define=API_BASE_URL=$API_BASE_URL"
if [ -n "$API_TOKEN" ]; then
    DART_DEFINES="$DART_DEFINES --dart-define=API_TOKEN=$API_TOKEN"
fi

# Clean + Build
echo "[1/3] flutter clean..."
flutter clean

echo "[2/3] flutter pub get..."
flutter pub get

echo "[3/3] flutter build appbundle (릴리즈)..."
flutter build appbundle --release $DART_DEFINES

echo ""
echo "=== 빌드 완료 ==="
echo "AAB 파일: build/app/outputs/bundle/release/app-release.aab"
echo ""
echo "이 파일을 Google Play Console에 업로드하세요."
echo ""

# APK도 생성 (테스트용)
echo "[추가] APK 빌드 (테스트용)..."
flutter build apk --release $DART_DEFINES
echo "APK 파일: build/app/outputs/flutter-apk/app-release.apk"
