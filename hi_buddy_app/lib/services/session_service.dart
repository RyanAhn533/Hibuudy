import 'package:shared_preferences/shared_preferences.dart';

/// 사용자 역할 — 첫 실행 온보딩에서 결정
enum UserRole {
  /// 당사자 본인 — 간단한 UI, CTA 2개
  self,
  /// 보호자/교사/복지사 — 전체 UI, 편집 권한
  coordinator,
}

/// UI 크기 모드 — 접근성
enum FontSizeMode {
  normal,
  large,
  xlarge,
}

/// 사용자 세그먼트 — 발달장애·노인·치매·청소년
/// v3.0에서는 dd만 완성, 나머지는 준비 중 (waitlist 수집)
enum UserSegment {
  /// 발달장애 · 자립생활 (활성)
  dd,
  /// 어르신 · 일상 관리 (준비 중)
  senior,
  /// 기억 보조 · 치매 (준비 중)
  dementia,
  /// 청소년 · 자립훈련 (준비 중)
  youth,
}

extension UserSegmentInfo on UserSegment {
  String get label {
    switch (this) {
      case UserSegment.dd: return '발달장애 · 자립생활';
      case UserSegment.senior: return '어르신 · 일상 관리';
      case UserSegment.dementia: return '기억 보조 · 치매';
      case UserSegment.youth: return '청소년 · 자립훈련';
    }
  }

  String get icon {
    switch (this) {
      case UserSegment.dd: return 'diversity_3';
      case UserSegment.senior: return 'elderly';
      case UserSegment.dementia: return 'psychology';
      case UserSegment.youth: return 'school';
    }
  }

  bool get isAvailable => this == UserSegment.dd;
}

/// ══════════════════════════════════════════════════════════
/// SessionService
/// 첫 실행 여부 · 역할 · 페어링 코드를 SharedPreferences에 저장
/// ══════════════════════════════════════════════════════════
class SessionService {
  static const _kOnboardedKey = 'harumate_onboarded_v1';
  static const _kRoleKey = 'harumate_role';
  static const _kSegmentKey = 'harumate_segment';
  static const _kFontSizeKey = 'harumate_font_size';
  static const _kPairCodeKey = 'harumate_pair_code';
  static const _kPairedAtKey = 'harumate_paired_at';
  static const _kUserNameKey = 'harumate_user_name';

  // ── 온보딩 완료 여부 ──
  static Future<bool> isOnboarded() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kOnboardedKey) ?? false;
  }

  static Future<void> completeOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kOnboardedKey, true);
  }

  // ── 역할 ──
  static Future<UserRole> getRole() async {
    final prefs = await SharedPreferences.getInstance();
    final v = prefs.getString(_kRoleKey);
    return v == 'coordinator' ? UserRole.coordinator : UserRole.self;
  }

  static Future<void> setRole(UserRole role) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kRoleKey, role == UserRole.coordinator ? 'coordinator' : 'self');
  }

  // ── 세그먼트 ──
  static Future<UserSegment> getSegment() async {
    final prefs = await SharedPreferences.getInstance();
    final v = prefs.getString(_kSegmentKey);
    return UserSegment.values.firstWhere(
      (e) => e.name == v,
      orElse: () => UserSegment.dd,
    );
  }

  static Future<void> setSegment(UserSegment seg) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kSegmentKey, seg.name);
  }

  // ── 이름 ──
  static Future<String> getUserName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kUserNameKey) ?? '사용자';
  }

  static Future<void> setUserName(String name) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kUserNameKey, name.trim().isEmpty ? '사용자' : name.trim());
  }

  // ── 글자 크기 ──
  static Future<FontSizeMode> getFontSize() async {
    final prefs = await SharedPreferences.getInstance();
    final v = prefs.getString(_kFontSizeKey) ?? 'large';
    return FontSizeMode.values.firstWhere(
      (e) => e.name == v,
      orElse: () => FontSizeMode.large,
    );
  }

  static Future<void> setFontSize(FontSizeMode mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kFontSizeKey, mode.name);
  }

  /// 글자 크기 배수 (1.0 = 보통)
  static double fontScale(FontSizeMode mode) {
    switch (mode) {
      case FontSizeMode.normal:
        return 1.0;
      case FontSizeMode.large:
        return 1.15;
      case FontSizeMode.xlarge:
        return 1.3;
    }
  }

  // ── 페어링 코드 ──
  static Future<String?> getPairCode() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kPairCodeKey);
  }

  static Future<void> setPairCode(String code) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kPairCodeKey, code);
    await prefs.setString(_kPairedAtKey, DateTime.now().toIso8601String());
  }

  static Future<void> clearPairCode() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kPairCodeKey);
    await prefs.remove(_kPairedAtKey);
  }

  /// 6자리 랜덤 페어링 코드 생성 (유진 피드백 반영: 4→6자리)
  static String generatePairCode() {
    final now = DateTime.now().microsecondsSinceEpoch;
    final code = (now % 900000 + 100000).toString();
    return code;
  }

  // ── 전체 초기화 (디버그/로그아웃용) ──
  static Future<void> reset() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kOnboardedKey);
    await prefs.remove(_kRoleKey);
    await prefs.remove(_kSegmentKey);
    await prefs.remove(_kFontSizeKey);
    await prefs.remove(_kPairCodeKey);
    await prefs.remove(_kPairedAtKey);
    await prefs.remove(_kUserNameKey);
  }
}
