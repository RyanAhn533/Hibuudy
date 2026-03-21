#!/bin/bash
# ─────────────────────────────────────────────
# Hi-Buddy Android 릴리즈 키스토어 생성 스크립트
# 실행: bash scripts/generate_keystore.sh
# ─────────────────────────────────────────────

set -e

KEYSTORE_DIR="$(dirname "$0")/.."
KEYSTORE_FILE="$KEYSTORE_DIR/hibuddy-release.jks"
KEY_PROPERTIES="$KEYSTORE_DIR/android/key.properties"

if [ -f "$KEYSTORE_FILE" ]; then
    echo "[!] 키스토어가 이미 존재합니다: $KEYSTORE_FILE"
    echo "    삭제하고 다시 생성하려면 파일을 먼저 삭제하세요."
    exit 1
fi

echo "=== Hi-Buddy 릴리즈 키스토어 생성 ==="
echo ""

# 비밀번호 입력
read -sp "키스토어 비밀번호 (6자 이상): " STORE_PASSWORD
echo ""
read -sp "키 비밀번호 (6자 이상): " KEY_PASSWORD
echo ""

# 키스토어 생성
keytool -genkeypair \
    -v \
    -keystore "$KEYSTORE_FILE" \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -alias hibuddy \
    -storepass "$STORE_PASSWORD" \
    -keypass "$KEY_PASSWORD" \
    -dname "CN=Hi-Buddy,OU=HEART Lab,O=Yonsei University,L=Seoul,ST=Seoul,C=KR"

echo ""
echo "[OK] 키스토어 생성 완료: $KEYSTORE_FILE"

# key.properties 생성
cat > "$KEY_PROPERTIES" << EOF
storePassword=$STORE_PASSWORD
keyPassword=$KEY_PASSWORD
keyAlias=hibuddy
storeFile=../../hibuddy-release.jks
EOF

echo "[OK] key.properties 생성 완료: $KEY_PROPERTIES"
echo ""
echo "⚠️  주의: 다음 파일은 절대 git에 올리지 마세요:"
echo "    - hibuddy-release.jks"
echo "    - android/key.properties"
echo ""
echo "=== 완료 ==="
