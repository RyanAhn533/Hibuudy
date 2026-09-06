import 'package:shared_preferences/shared_preferences.dart';
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
    await _loadHomeLayout();
  }

  // ── 홈 레이아웃 (Assistive Access grid/row 토글, P9) ──
  static const _kHomeLayout = 'harumate_home_layout';
  /// 'grid' (2x2 모아 보기) | 'row' (줄로 보기)
  static String homeLayout = 'grid';

  static Future<void> _loadHomeLayout() async {
    final prefs = await SharedPreferences.getInstance();
    homeLayout = prefs.getString(_kHomeLayout) ?? 'grid';
  }

  static Future<void> setHomeLayout(String layout) async {
    homeLayout = layout == 'row' ? 'row' : 'grid';
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kHomeLayout, homeLayout);
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
