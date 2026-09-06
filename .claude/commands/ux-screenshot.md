---
description: APK 빌드 + 설치 + 화면 캡처 + docs/screenshots/ 저장 자동화
allowed-tools: Bash(*), Read
argument-hint: [화면이름 예: home_user / coordinator / onboarding / user]
---

화면 캡처 자동화. 매 마일스톤 시연 캡처 5장 확보용.

```bash
SCREEN="${1:-home}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APK=/c/Users/wnsdu/Hibuudy/hi_buddy_app/build/app/outputs/flutter-apk/app-debug.apk
ADB=/c/Users/wnsdu/AppData/Local/Android/Sdk/platform-tools/adb.exe
OUT=/c/Users/wnsdu/Hibuudy/docs/screenshots
mkdir -p $OUT

echo "=== 1. 에뮬 확인 ==="
DEVICE=$($ADB devices | grep -E 'emulator|device' | grep -v 'List' | head -1 | awk '{print $1}')
[ -z "$DEVICE" ] && { echo "❌ 에뮬 안 켜져있음. 'emulator -avd Medium_Phone_API_36.1 -no-snapshot' 먼저"; exit 1; }
echo "✅ Device: $DEVICE"

echo "=== 2. APK 최신 확인 + 빌드 ==="
cd /c/Users/wnsdu/Hibuudy/hi_buddy_app
[ ! -f $APK ] && /c/flutter/bin/flutter.bat build apk --debug 2>&1 | tail -3
APK_AGE_MIN=$(( ($(date +%s) - $(stat -c %Y $APK)) / 60 ))
if [ $APK_AGE_MIN -gt 30 ]; then
  echo "APK 30분+ 오래됨. 새로 빌드"
  /c/flutter/bin/flutter.bat build apk --debug 2>&1 | tail -3
fi

echo "=== 3. 재설치 + 실행 ==="
$ADB -s $DEVICE shell am force-stop com.harumate.care
$ADB -s $DEVICE install -r $APK 2>&1 | tail -1
$ADB -s $DEVICE shell am start -n com.harumate.care/.MainActivity

echo "=== 4. 부팅 + 캡처 (15초 대기) ==="
sleep 15
OUT_FILE=$OUT/${SCREEN}_${TIMESTAMP}.png
$ADB -s $DEVICE exec-out screencap -p > $OUT_FILE
echo "✅ Saved: $OUT_FILE ($(du -h $OUT_FILE | cut -f1))"
```

읽은 후:
- 캡처 파일 Read 도구로 즉시 시각 검증
- V1 vs V2 비교 시: `git stash` → V1 빌드 → 캡처 → V2 복원 → 비교
- 시연용 5장 확보 시: home_user / user_steps / coordinator / sos / onboarding 순으로 실행
