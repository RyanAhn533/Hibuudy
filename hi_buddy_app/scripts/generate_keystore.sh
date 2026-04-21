#!/bin/bash
# ─────────────────────────────────────────────
# 하루메이트 Android 릴리즈 키스토어 생성
# v1.1 — 브랜드 업데이트 (Hi-Buddy → HaruMate)
# 실행: bash scripts/generate_keystore.sh
# ─────────────────────────────────────────────

set -e

APP_DIR="$(dirname "$0")/.."
KEYSTORE_FILE="$APP_DIR/harumate-release.jks"
KEY_PROPERTIES="$APP_DIR/android/key.properties"
BACKUP_FILE="$APP_DIR/harumate-keys-BACKUP.txt"

if [ -f "$KEYSTORE_FILE" ]; then
    echo "[!] 키스토어가 이미 존재합니다: $KEYSTORE_FILE"
    echo "    재생성하려면 먼저 삭제하세요 (절대 추천 안 함)"
    exit 1
fi

# keytool 경로 (Android Studio JDK)
KEYTOOL="/c/Program Files/Android/Android Studio/jbr/bin/keytool.exe"
if [ ! -f "$KEYTOOL" ]; then
    KEYTOOL="keytool"
fi

echo "=== 하루메이트 릴리즈 키스토어 생성 ==="
echo ""

# 인자로 비밀번호 받거나 자동 생성
STORE_PASSWORD="${1:-$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-20)}"
KEY_PASSWORD="${2:-$STORE_PASSWORD}"

# 키스토어 생성 (10000일 = 약 27년 유효)
"$KEYTOOL" -genkeypair \
    -keystore "$KEYSTORE_FILE" \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -alias harumate \
    -storepass "$STORE_PASSWORD" \
    -keypass "$KEY_PASSWORD" \
    -dname "CN=Junyoung Ahn,OU=HaruMate,O=HaruMate,L=Seoul,ST=Seoul,C=KR" \
    2>&1 | tail -5

echo ""
echo "[OK] 키스토어 생성 완료"

# key.properties (빌드 스크립트가 읽음)
cat > "$KEY_PROPERTIES" << EOF
storePassword=$STORE_PASSWORD
keyPassword=$KEY_PASSWORD
keyAlias=harumate
storeFile=../../harumate-release.jks
EOF

# Backup file (사용자가 따로 안전한 곳에 저장해야 함)
cat > "$BACKUP_FILE" << EOF
═══════════════════════════════════════════════════════════════════
 하루메이트 HaruMate Android 릴리즈 키 백업
 생성일: $(date +%Y-%m-%d_%H:%M)
 작성자: JY (Ryan.ahn)
═══════════════════════════════════════════════════════════════════

⚠️ 이 파일 + harumate-release.jks 두 개를 반드시 백업하세요.
⚠️ 잃어버리면 Play Store에서 앱 업데이트 영구 불가능합니다.

백업 권장 위치 (최소 2곳):
  - Google Drive (개인 계정)
  - iCloud / OneDrive
  - 외장 USB
  - 비밀번호 매니저 (1Password, Bitwarden 등)

═══════════════════════════════════════════════════════════════════
 KEYSTORE INFO
═══════════════════════════════════════════════════════════════════

Keystore File       : harumate-release.jks
Keystore Password   : $STORE_PASSWORD
Key Alias           : harumate
Key Password        : $KEY_PASSWORD
Validity            : 10000 days (~27 years)
Algorithm           : RSA 2048
Distinguished Name  : CN=Junyoung Ahn, OU=HaruMate, O=HaruMate, L=Seoul, C=KR

═══════════════════════════════════════════════════════════════════
 백업 완료 체크리스트
═══════════════════════════════════════════════════════════════════

[ ] harumate-release.jks 를 Google Drive 업로드
[ ] harumate-keys-BACKUP.txt 를 Google Drive 업로드
[ ] 비밀번호 매니저(선택)에 추가 저장
[ ] 확인 후 이 파일을 안전한 곳으로 이동

═══════════════════════════════════════════════════════════════════
EOF

echo "[OK] key.properties 생성 완료"
echo "[OK] 백업 파일 생성 완료: $BACKUP_FILE"
echo ""
echo "🔴 반드시 별도 장소(Google Drive 등)에 백업하세요"
echo "=== 완료 ==="
