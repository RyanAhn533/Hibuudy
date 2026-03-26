import 'database_service.dart';

/// 장애 강도별 UI 모드 서비스
/// normal: 기존 UI 그대로
/// simple: 큰 버튼, 적은 옵션, 자동 TTS, 이미지 중심
/// kiosk: 자동 재생, 터치 불필요, 시간 기반 자동 전환, SOS 버튼
class UiModeService {
  static String currentMode = 'normal';

  static Future<void> loadMode() async {
    final profile = await DatabaseService.getProfile();
    currentMode = profile['ui_mode'] as String? ?? 'normal';
  }

  static bool get isSimple => currentMode == 'simple';
  static bool get isKiosk => currentMode == 'kiosk';
  static bool get isNormal => currentMode == 'normal';

  /// simple/kiosk 모드 여부 (공통 큰 글씨/자동 TTS 등)
  static bool get isAccessibilityMode => isSimple || isKiosk;

  static double get fontSize => isNormal ? 16.0 : 22.0;
  static double get headerSize => isNormal ? 20.0 : 28.0;
  static double get buttonHeight => isNormal ? 48.0 : 64.0;
  static double get iconSize => isNormal ? 24.0 : 36.0;

  /// 모드 변경 시 즉시 반영
  static Future<void> setMode(String mode) async {
    currentMode = mode;
    await DatabaseService.updateProfile({'ui_mode': mode});
  }
}
