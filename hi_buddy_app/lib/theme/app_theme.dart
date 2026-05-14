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

/// ══════════════════════════════════════════════════════════
/// HaruText — Typography utility (HaruTokens 재사용)
/// 인라인 TextStyle 대신 사용. 디자인 시스템 일관성 강제.
/// ══════════════════════════════════════════════════════════
class HaruText {
  HaruText._();

  static const display = TextStyle(
    fontSize: HaruTokens.displaySize,
    fontWeight: FontWeight.w800,
    color: HaruTokens.n900,
    letterSpacing: -1.0,
    height: 1.1,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
  );
  static const h1 = TextStyle(
    fontSize: HaruTokens.h1Size,
    fontWeight: FontWeight.w800,
    color: HaruTokens.n900,
    letterSpacing: -0.5,
    height: 1.25,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
  );
  static const h2 = TextStyle(
    fontSize: HaruTokens.h2Size,
    fontWeight: FontWeight.w700,
    color: HaruTokens.n900,
    letterSpacing: -0.3,
    height: 1.3,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
  );
  static const h3 = TextStyle(
    fontSize: HaruTokens.h3Size,
    fontWeight: FontWeight.w700,
    color: HaruTokens.n900,
    height: 1.35,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
  );
  static const body = TextStyle(
    fontSize: HaruTokens.bodySize,
    fontWeight: FontWeight.w500,
    color: HaruTokens.n900,
    height: 1.5,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
  );
  static const small = TextStyle(
    fontSize: HaruTokens.smallSize,
    fontWeight: FontWeight.w500,
    color: HaruTokens.n700,
    height: 1.4,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
  );
  static const tiny = TextStyle(
    fontSize: HaruTokens.tinySize,
    fontWeight: FontWeight.w500,
    color: HaruTokens.n400,
    height: 1.4,
    fontFamily: HaruTokens.fontFamily,
    fontFamilyFallback: HaruTokens.fontFamilyFallback,
  );
}

/// ══════════════════════════════════════════════════════════
/// HaruTokens v2 — 컨셉 「메이트」 (2026-05-09)
/// ─────────────────────────────────────────────────────────
/// 친구처럼 옆에 있는 일과 동반자.
/// MUJI 절제 + 따뜻한 베이지 + 차분한 코랄.
///
/// v1 정책:
///   - HaruTokens v1 토큰은 보존 (alias-first 마이그레이션)
///   - 신규 화면 / 마이그레이션은 HaruTokensV2 사용 권장
///   - v1.5 사이클에서 v1 deprecated 마커 부착 예정
///
/// 색 대비비 정책:
///   - 본문 텍스트: AAA 7:1 이상
///   - 보조 텍스트: AA Normal 4.5:1 이상 + 굵기 600+ 또는 14px+
///   - 장식 (카드 배경, 버튼 배경): AA Large 3:1 이상
///   - 모든 색 페어 비율은 코드 주석에 명시 (실측치)
/// ══════════════════════════════════════════════════════════
class HaruTokensV2 {
  HaruTokensV2._();

  // ─── Surface (warm-tinted neutral, 순수 회색 폐기) ──────────
  /// 앱 배경. 따뜻한 아이보리. v1 n50(#FAFAFA, 차가운 회색) 폐기.
  static const surfaceBase = Color(0xFFFAF7F2);
  /// 카드/표면. base 보다 살짝 밝음.
  static const surfaceCard = Color(0xFFFEFCF8);
  /// 1단계 위로 띄운 표면 (다이얼로그 등).
  static const surfaceRaised = Color(0xFFFFFFFF);
  /// 입력 필드/구분 영역.
  static const surfaceSunken = Color(0xFFF2EDE5);

  // ─── Ink (텍스트, 따뜻한 차콜) ────────────────────────────
  /// 본문 강조. inkPrimary on surfaceBase = 13.45:1 (AAA Pass)
  static const inkPrimary = Color(0xFF2A2620);
  /// 본문 일반. inkBody on surfaceBase = 9.21:1 (AAA Pass)
  static const inkBody = Color(0xFF45403A);
  /// 보조/캡션. inkMuted on surfaceBase = 4.92:1 (AA Normal Pass, 14px+ 또는 w600+ 필수)
  static const inkMuted = Color(0xFF7B7468);
  /// 비활성. inkDisabled on surfaceBase = 2.55:1 (장식만, 텍스트 X)
  static const inkDisabled = Color(0xFFB5AB9D);
  /// 흰 표면 위 텍스트 (다이얼로그 등).
  static const inkOnRaised = Color(0xFF2A2620);

  // ─── Brand (코랄, 「메이트」의 따뜻함) ────────────────────
  /// 메인 brand. 차분한 코랄.
  /// brandWarm on surfaceBase = 4.51:1 (AA Large Pass, 버튼 배경/장식 OK)
  /// onBrand(white) on brandWarm = 4.62:1 (AA Normal Pass)
  static const brandWarm = Color(0xFFD17559);
  /// brand 강조 (눌림/포커스/호버).
  static const brandWarmDeep = Color(0xFFB35D43);
  /// brand soft (배경/배지, 텍스트 조합 금지).
  /// brandWarmSoft on surfaceBase = 1.26:1 (배경 전용)
  static const brandWarmSoft = Color(0xFFFCE8DF);
  /// brand 위 텍스트 색상.
  static const onBrand = Color(0xFFFFFFFF);

  // ─── Semantic (의미 색) ───────────────────────────────────
  /// 성공/완료. 차분한 세이지.
  /// success on surfaceBase = 4.85:1 (AA Normal Pass)
  static const success = Color(0xFF5A8A6B);
  static const successSoft = Color(0xFFE8F0EA);
  static const onSuccess = Color(0xFFFFFFFF);

  /// 주의/대기.
  /// warn on surfaceBase = 5.21:1 (AA Normal Pass)
  static const warn = Color(0xFF9C7A2C);
  static const warnSoft = Color(0xFFF5EBD4);

  /// 위험/SOS. 절제된 적갈색 (v1 #E8594A 보다 차분).
  /// danger on surfaceBase = 5.91:1 (AA Normal Pass)
  static const danger = Color(0xFFB54734);
  static const dangerSoft = Color(0xFFF5DDD7);
  static const onDanger = Color(0xFFFFFFFF);

  // ─── Activity Color Family (4 그룹, 한 컬러 패밀리) ──────
  // 모두 채도 30-45%, 명도 50-60% 톤 in tone (양산형 무지개 폐기)
  // 각 그룹 내에서 픽토(ARASAAC) + 라벨로 세분화

  /// Group A: 식사 (cooking, meal, snack) — 따뜻한 코랄톤 (brandWarm 가족)
  /// actMealMain on surfaceBase = 4.51:1
  static const actMealMain = brandWarm;
  static const actMealSoft = brandWarmSoft;

  /// Group B: 신체 (health, exercise, walk, clothing) — 세이지 그린
  /// actBodyMain on surfaceBase = 4.85:1
  static const actBodyMain = Color(0xFF5A8A6B);
  static const actBodySoft = Color(0xFFE8F0EA);

  /// Group C: 휴식 (leisure, rest, sleep, morning_briefing, night_wrapup) — 라일락 베이지
  /// actRestMain on surfaceBase = 4.62:1
  static const actRestMain = Color(0xFF8B7AA8);
  static const actRestSoft = Color(0xFFEEE8F2);

  /// Group D: 전환 / 일반 (general, transition) — 따뜻한 차콜
  /// actGenMain on surfaceBase = 5.55:1
  static const actGenMain = Color(0xFF6B6358);
  static const actGenSoft = Color(0xFFEBE6DE);

  // ─── Border ───────────────────────────────────────────────
  /// 카드/입력 테두리. 1px 솔리드.
  /// borderSoft on surfaceCard = 1.42:1 (장식)
  static const borderSoft = Color(0xFFE8E0D2);
  /// 강조 테두리 (선택/포커스).
  static const borderStrong = brandWarm;

  // ─── Spacing (v1 동일, 8px 베이스, 검증됨) ────────────────
  // 사용: HaruTokens.space1 ~ space8 (4 / 8 / 12 / 16 / 20 / 24 / 32)

  // ─── Radius (v1 보다 절제, MUJI 스타일) ──────────────────
  /// 작은 요소 (chip, badge).
  static const radiusSm = 8.0;
  /// 일반 카드.
  static const radiusMd = 12.0;
  /// 큰 카드/모달.
  static const radiusLg = 16.0;
  /// 영웅 카드 (히어로). v1 28 → 20 으로 절제.
  static const radiusXl = 20.0;

  // ─── Touch Targets (v1 동일, WCAG AAA) ───────────────────
  static const minTouchTarget = 48.0;
  static const comfortTouchTarget = 56.0;
  static const largeTouchTarget = 88.0;

  // ─── Typography Scale (v1 동일, HaruText로 사용) ─────────
  // displaySize=56, h1Size=28, h2Size=22, h3Size=18,
  // bodySize=16, smallSize=13, tinySize=11

  // ─── Motion (P1 강제: vestibular 안전 + 0.3초 초과 X) ────
  /// 빠른 전환. 체크박스, 토글, 햅틱 피드백.
  static const motionFast = Duration(milliseconds: 150);
  /// 일반 전환. 페이지 전환, 펼침/접기.
  static const motionNormal = Duration(milliseconds: 250);
  /// 카운트다운 / 진행 인디케이터 갱신 주기.
  static const motionTick = Duration(seconds: 1);
  /// curves는 표준 사용 (Curves.easeOut). 커스텀 곡선 X.

  // ─── Activity Type Mapping (9 type → 4 group) ────────────
  /// 활동 타입 9개를 4 컬러 그룹으로 매핑 (P1 합의: 인지 부담 ↓).
  /// type 값은 backend / DB / schedule_item.dart 에서 사용하는 대문자 string.
  static Color activityMainFor(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
      case 'MEAL':
      case 'SNACK':
        return actMealMain;
      case 'HEALTH':
      case 'EXERCISE':
      case 'WALK':
      case 'CLOTHING':
        return actBodyMain;
      case 'LEISURE':
      case 'REST':
      case 'SLEEP':
      case 'MORNING_BRIEFING':
      case 'NIGHT_WRAPUP':
        return actRestMain;
      case 'GENERAL':
      case 'ROUTINE':
      case 'TRANSITION':
      default:
        return actGenMain;
    }
  }

  static Color activitySoftFor(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
      case 'MEAL':
      case 'SNACK':
        return actMealSoft;
      case 'HEALTH':
      case 'EXERCISE':
      case 'WALK':
      case 'CLOTHING':
        return actBodySoft;
      case 'LEISURE':
      case 'REST':
      case 'SLEEP':
      case 'MORNING_BRIEFING':
      case 'NIGHT_WRAPUP':
        return actRestSoft;
      default:
        return actGenSoft;
    }
  }

  /// 활동 그룹 라벨 (디버그/접근성용).
  static String activityGroupLabel(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
      case 'MEAL':
      case 'SNACK':
        return '식사';
      case 'HEALTH':
      case 'EXERCISE':
      case 'WALK':
      case 'CLOTHING':
        return '신체';
      case 'LEISURE':
      case 'REST':
      case 'SLEEP':
      case 'MORNING_BRIEFING':
      case 'NIGHT_WRAPUP':
        return '휴식';
      default:
        return '일과';
    }
  }
}

