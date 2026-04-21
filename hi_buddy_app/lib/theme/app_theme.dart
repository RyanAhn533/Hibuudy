import 'package:flutter/material.dart';

/// ══════════════════════════════════════════════════════════
/// HaruMate Design System v3.0
/// Figma: https://www.figma.com/design/UR4JMkCsmhZgNmtvznzvv3
/// 김유진 페르소나 리뷰 반영 · 2026-04-19
/// ══════════════════════════════════════════════════════════
class HaruTokens {
  // ── Brand Colors ──
  static const primary = Color(0xFF4F7CFF);
  static const primarySoft = Color(0xFFE6EEFF);
  static const accent = Color(0xFFFFB547);
  static const accentSoft = Color(0xFFFFF4E0);

  // ── Semantic Colors ──
  static const success = Color(0xFF3FB765);
  static const successSoft = Color(0xFFE7F6EC);
  static const danger = Color(0xFFE8594A);
  static const dangerSoft = Color(0xFFFDE9E6);
  static const warning = Color(0xFFFFB547);

  // ── Neutrals ──
  static const n50 = Color(0xFFFAFAFA);
  static const n100 = Color(0xFFF4F5F7);
  static const n200 = Color(0xFFE5E7EB);
  static const n400 = Color(0xFF9AA0A6);
  static const n700 = Color(0xFF3A3D42);
  static const n900 = Color(0xFF1A1C1F);
  static const white = Color(0xFFFFFFFF);

  // ── Kiosk Dark Mode ──
  static const kioskBg = Color(0xFF0B1220);
  static const kioskCard = Color(0xFF15213D);
  static const kioskMuted = Color(0xFF8AA6D3);

  // ── Radii ──
  static const radiusSm = 12.0;
  static const radiusMd = 16.0;
  static const radiusLg = 20.0;
  static const radiusXl = 28.0;

  // ── Spacing ──
  static const space1 = 4.0;
  static const space2 = 8.0;
  static const space3 = 12.0;
  static const space4 = 16.0;
  static const space5 = 20.0;
  static const space6 = 24.0;
  static const space8 = 32.0;

  // ── Touch Targets (WCAG AAA) ──
  static const minTouchTarget = 48.0;
  static const comfortTouchTarget = 56.0;
  static const largeTouchTarget = 88.0;

  // ── Typography Scale ──
  static const displaySize = 56.0;
  static const h1Size = 28.0;
  static const h2Size = 22.0;
  static const h3Size = 18.0;
  static const bodySize = 16.0;
  static const smallSize = 13.0;
  static const tinySize = 11.0;

  // ── Font Family ──
  /// Pretendard 우선 · 없을 시 시스템 폰트 폴백
  static const fontFamily = 'Pretendard';
  static const fontFamilyFallback = <String>[
    'Pretendard Variable',
    'Apple SD Gothic Neo',
    'Noto Sans KR',
    'Roboto',
  ];
}

/// ══════════════════════════════════════════════════════════
/// Legacy 호환 레이어 — 기존 코드 안 깨짐
/// 새 코드는 HaruTokens 직접 쓰기 권장
/// ══════════════════════════════════════════════════════════
class HiBuddyColors {
  // ── Primary mapping (재매핑됨) ──
  static const primary = HaruTokens.primary;
  static const primaryLight = Color(0xFF7B9AFF); // lighter variant
  static const primaryBg = HaruTokens.primarySoft;
  static const secondary = HaruTokens.accent;
  static const secondaryLight = Color(0xFFFFD88A);
  static const success = HaruTokens.success;
  static const successBg = HaruTokens.successSoft;
  static const warning = HaruTokens.warning;
  static const danger = HaruTokens.danger;
  static const bg = HaruTokens.n50;
  static const cardBg = HaruTokens.white;
  static const text = HaruTokens.n900;
  static const textMuted = HaruTokens.n400;
  static const border = HaruTokens.n200;

  // ── Activity Colors (유지 · 일정 타입별 시각 구분) ──
  static const cooking = Color(0xFFFF8A3C);
  static const cookingBg = Color(0xFFFFF4EC);
  static const health = HaruTokens.success;
  static const healthBg = HaruTokens.successSoft;
  static const clothing = Color(0xFF8B5CF6);
  static const clothingBg = Color(0xFFF5F1FF);
  static const leisure = Color(0xFFEC5E93);
  static const leisureBg = Color(0xFFFDF0F6);
  static const morning = HaruTokens.accent;
  static const morningBg = HaruTokens.accentSoft;
  static const night = Color(0xFF6B7AE8);
  static const nightBg = HaruTokens.primarySoft;
  static const rest = Color(0xFF3FB7C9);
  static const restBg = Color(0xFFE3F6FA);
  static const general = HaruTokens.n400;
  static const generalBg = HaruTokens.n100;

  static Color getActivityColor(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
      case 'MEAL':
        return cooking;
      case 'HEALTH':
        return health;
      case 'CLOTHING':
        return clothing;
      case 'LEISURE':
        return leisure;
      case 'MORNING_BRIEFING':
        return morning;
      case 'NIGHT_WRAPUP':
        return night;
      case 'REST':
        return rest;
      default:
        return general;
    }
  }

  static Color getActivityBgColor(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
      case 'MEAL':
        return cookingBg;
      case 'HEALTH':
        return healthBg;
      case 'CLOTHING':
        return clothingBg;
      case 'LEISURE':
        return leisureBg;
      case 'MORNING_BRIEFING':
        return morningBg;
      case 'NIGHT_WRAPUP':
        return nightBg;
      case 'REST':
        return restBg;
      default:
        return generalBg;
    }
  }

  /// ⚠️ DEPRECATED — 김유진 피드백: 이모지 히어로 제거 방침
  /// 새 화면은 Material Symbols 또는 ARASAAC 픽토그램 사용
  /// 단, 현재 레시피 데이터 호환 위해 유지
  static String getActivityEmoji(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
        return '🍳';
      case 'MEAL':
        return '🍽️';
      case 'HEALTH':
        return '💪';
      case 'CLOTHING':
        return '👔';
      case 'LEISURE':
        return '🎮';
      case 'MORNING_BRIEFING':
        return '🌅';
      case 'NIGHT_WRAPUP':
        return '🌙';
      case 'REST':
        return '☕';
      case 'ROUTINE':
        return '🧹';
      default:
        return '📋';
    }
  }

  /// Material Symbols 이름으로 매핑 (v3.0 신규)
  static String getActivityIcon(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
        return 'restaurant';
      case 'MEAL':
        return 'dinner_dining';
      case 'HEALTH':
        return 'fitness_center';
      case 'CLOTHING':
        return 'checkroom';
      case 'LEISURE':
        return 'sports_esports';
      case 'MORNING_BRIEFING':
        return 'wb_sunny';
      case 'NIGHT_WRAPUP':
        return 'bedtime';
      case 'REST':
        return 'self_care';
      case 'ROUTINE':
        return 'cleaning_services';
      default:
        return 'event_note';
    }
  }

  static String getActivityLabel(String type) {
    switch (type.toUpperCase()) {
      case 'MORNING_BRIEFING':
        return '아침 안내';
      case 'NIGHT_WRAPUP':
        return '마무리 안내';
      case 'COOKING':
        return '요리';
      case 'MEAL':
        return '식사';
      case 'HEALTH':
        return '운동';
      case 'CLOTHING':
        return '옷 입기';
      case 'LEISURE':
        return '여가';
      case 'REST':
        return '쉬는 시간';
      case 'ROUTINE':
        return '준비/위생';
      default:
        return '일정';
    }
  }
}

/// ══════════════════════════════════════════════════════════
/// Text Theme Builder
/// 모든 screen에서 일관된 한글 타이포 보장
/// ══════════════════════════════════════════════════════════
TextTheme _buildTextTheme() {
  const base = TextStyle(
    color: HaruTokens.n900,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
    height: 1.5,
    letterSpacing: -0.2,
  );

  return TextTheme(
    // Display — 온보딩 Welcome
    displayLarge: base.copyWith(fontSize: HaruTokens.displaySize, fontWeight: FontWeight.w800, height: 1.2, letterSpacing: -1.0),
    // Headings
    headlineLarge: base.copyWith(fontSize: HaruTokens.h1Size, fontWeight: FontWeight.w800, height: 1.3, letterSpacing: -0.5),
    headlineMedium: base.copyWith(fontSize: HaruTokens.h2Size, fontWeight: FontWeight.w700, height: 1.4),
    headlineSmall: base.copyWith(fontSize: HaruTokens.h3Size, fontWeight: FontWeight.w700, height: 1.45),
    // Titles
    titleLarge: base.copyWith(fontSize: HaruTokens.h3Size, fontWeight: FontWeight.w700),
    titleMedium: base.copyWith(fontSize: HaruTokens.bodySize, fontWeight: FontWeight.w600),
    // Body
    bodyLarge: base.copyWith(fontSize: HaruTokens.bodySize, fontWeight: FontWeight.w400, height: 1.6),
    bodyMedium: base.copyWith(fontSize: HaruTokens.smallSize, fontWeight: FontWeight.w400, height: 1.6),
    bodySmall: base.copyWith(fontSize: HaruTokens.tinySize, fontWeight: FontWeight.w500, color: HaruTokens.n400),
    // Labels
    labelLarge: base.copyWith(fontSize: HaruTokens.smallSize, fontWeight: FontWeight.w700),
    labelMedium: base.copyWith(fontSize: HaruTokens.tinySize, fontWeight: FontWeight.w700, color: HaruTokens.n400, letterSpacing: 0.5),
    labelSmall: base.copyWith(fontSize: 10, fontWeight: FontWeight.w500, color: HaruTokens.n400),
  );
}

/// ══════════════════════════════════════════════════════════
/// App Theme Builder
/// ══════════════════════════════════════════════════════════
ThemeData buildAppTheme({bool kioskMode = false}) {
  final bgColor = kioskMode ? HaruTokens.kioskBg : HaruTokens.n50;
  final cardColor = kioskMode ? HaruTokens.kioskCard : HaruTokens.white;

  return ThemeData(
    useMaterial3: true,
    colorScheme: kioskMode
        ? const ColorScheme.dark(
            primary: HaruTokens.primary,
            secondary: HaruTokens.accent,
            error: HaruTokens.danger,
            surface: HaruTokens.kioskCard,
            onPrimary: HaruTokens.white,
            onSurface: HaruTokens.white,
          )
        : const ColorScheme.light(
            primary: HaruTokens.primary,
            secondary: HaruTokens.accent,
            error: HaruTokens.danger,
            surface: HaruTokens.white,
            surfaceContainerHighest: HaruTokens.n100,
            onPrimary: HaruTokens.white,
            onSurface: HaruTokens.n900,
            outline: HaruTokens.n200,
          ),
    scaffoldBackgroundColor: bgColor,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
    textTheme: _buildTextTheme(),

    // ── AppBar ──
    appBarTheme: AppBarTheme(
      backgroundColor: bgColor,
      foregroundColor: kioskMode ? HaruTokens.white : HaruTokens.n900,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: HaruTokens.h3Size,
        fontWeight: FontWeight.w800,
        color: kioskMode ? HaruTokens.white : HaruTokens.n900,
        fontFamily: HaruTokens.fontFamily,
        fontFamilyFallback: HaruTokens.fontFamilyFallback,
      ),
    ),

    // ── Elevated Button (Primary CTA) ──
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: HaruTokens.primary,
        foregroundColor: HaruTokens.white,
        minimumSize: const Size(double.infinity, HaruTokens.comfortTouchTarget),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(HaruTokens.radiusSm)),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.2,
        ),
        elevation: 0,
      ),
    ),

    // ── Outlined Button (Secondary) ──
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: HaruTokens.primary,
        minimumSize: const Size(double.infinity, HaruTokens.comfortTouchTarget),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        side: const BorderSide(color: HaruTokens.primary, width: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(HaruTokens.radiusSm)),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
      ),
    ),

    // ── Text Button ──
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: HaruTokens.primary,
        minimumSize: const Size(64, HaruTokens.minTouchTarget),
        padding: const EdgeInsets.symmetric(horizontal: 16),
        textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
      ),
    ),

    // ── Card ──
    cardTheme: CardThemeData(
      elevation: 0,
      color: cardColor,
      shadowColor: Colors.black.withValues(alpha: 0.04),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
        side: BorderSide(color: kioskMode ? HaruTokens.kioskCard : HaruTokens.n200, width: 1),
      ),
      margin: EdgeInsets.zero,
    ),

    // ── Input ──
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: cardColor,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
        borderSide: const BorderSide(color: HaruTokens.n200, width: 1.5),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
        borderSide: const BorderSide(color: HaruTokens.n200, width: 1.5),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
        borderSide: const BorderSide(color: HaruTokens.primary, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(HaruTokens.radiusSm),
        borderSide: const BorderSide(color: HaruTokens.danger, width: 1.5),
      ),
      hintStyle: const TextStyle(color: HaruTokens.n400, fontSize: 14),
      labelStyle: const TextStyle(color: HaruTokens.n700, fontSize: 13, fontWeight: FontWeight.w600),
    ),

    // ── Chip ──
    chipTheme: ChipThemeData(
      backgroundColor: HaruTokens.n100,
      selectedColor: HaruTokens.primary,
      labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: HaruTokens.n700),
      secondaryLabelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: HaruTokens.white),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      side: BorderSide.none,
    ),

    // ── Dialog ──
    dialogTheme: DialogThemeData(
      backgroundColor: cardColor,
      elevation: 8,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(HaruTokens.radiusLg)),
      titleTextStyle: const TextStyle(
        fontSize: HaruTokens.h3Size,
        fontWeight: FontWeight.w800,
        color: HaruTokens.n900,
        fontFamily: HaruTokens.fontFamily,
      ),
      contentTextStyle: const TextStyle(
        fontSize: HaruTokens.bodySize,
        height: 1.6,
        color: HaruTokens.n700,
        fontFamily: HaruTokens.fontFamily,
      ),
    ),

    // ── Bottom Sheet ──
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: cardColor,
      elevation: 8,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(HaruTokens.radiusXl)),
      ),
    ),

    // ── SnackBar ──
    snackBarTheme: SnackBarThemeData(
      backgroundColor: HaruTokens.n900,
      contentTextStyle: const TextStyle(color: HaruTokens.white, fontSize: 14, fontWeight: FontWeight.w600),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(HaruTokens.radiusSm)),
      behavior: SnackBarBehavior.floating,
    ),

    // ── Divider ──
    dividerTheme: const DividerThemeData(
      color: HaruTokens.n200,
      thickness: 1,
      space: 1,
    ),

    // ── Icon ──
    iconTheme: const IconThemeData(color: HaruTokens.n700, size: 24),

    // ── Visual Density ──
    visualDensity: VisualDensity.standard,
  );
}
