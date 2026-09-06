---
description: 에뮬 UI 검증 — x64 빌드 → uninstall/install → 역할·일정 시드 → 캡처 → 런타임 예외 0 확인
allowed-tools: Bash(*), Read
argument-hint: [self|coordinator] [proof 0|1] [캡처접두어]
---

세션 7(2026-09-06)에서 확정한 검증 루틴. 상세와 함정은 `tools/emu/run_ui_check.sh` 주석.

```bash
cd /c/Users/wnsdu/Hibuudy
# 에뮬 꺼져 있으면 (백그라운드):
#   /c/Users/wnsdu/AppData/Local/Android/Sdk/emulator/emulator.exe -avd Medium_Phone_API_36.1 -no-snapshot -no-audio -no-boot-anim &
bash tools/emu/run_ui_check.sh "${1:-self}" "${2:-0}" "${3:-ui_}"
```

읽은 후:
- `flutter errors: 0` 이 아니면 그 화면은 실패. logcat 발췌가 원인.
- 캡처는 반드시 **Read 도구로 눈으로 확인** ("다 적용했다" = 캡처 확인까지, `feedback_apply_means_running.md`).
- `lastUpdateTime` 이 방금 시각이 아니면 설치 실패 → 스크린샷은 옛 빌드. 저장소 확인 (`adb shell df -h /data`).
- 다른 화면 캡처는 스크립트 끝에 출력되는 좌표/명령으로 이어서. 체크박스 등은 `tools/emu/tap_checkboxes.py`.
- 당사자 화면 바꿨으면 이어서 `harumate-cognitive-a11y` 스킬로 12원칙 리뷰.
