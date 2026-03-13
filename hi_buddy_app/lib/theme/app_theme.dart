import 'package:flutter/material.dart';

class HiBuddyColors {
  static const primary = Color(0xFF4F46E5);
  static const primaryLight = Color(0xFF818CF8);
  static const primaryBg = Color(0xFFEEF2FF);
  static const secondary = Color(0xFFF59E0B);
  static const secondaryLight = Color(0xFFFCD34D);
  static const success = Color(0xFF10B981);
  static const successBg = Color(0xFFD1FAE5);
  static const warning = Color(0xFFF59E0B);
  static const danger = Color(0xFFEF4444);
  static const bg = Color(0xFFF8FAFC);
  static const cardBg = Colors.white;
  static const text = Color(0xFF1E293B);
  static const textMuted = Color(0xFF64748B);
  static const border = Color(0xFFE2E8F0);

  // Activity-specific
  static const cooking = Color(0xFFF97316);
  static const cookingBg = Color(0xFFFFF7ED);
  static const health = Color(0xFF10B981);
  static const healthBg = Color(0xFFECFDF5);
  static const clothing = Color(0xFF8B5CF6);
  static const clothingBg = Color(0xFFF5F3FF);
  static const leisure = Color(0xFFEC4899);
  static const leisureBg = Color(0xFFFDF2F8);
  static const morning = Color(0xFFF59E0B);
  static const morningBg = Color(0xFFFFFBEB);
  static const night = Color(0xFF6366F1);
  static const nightBg = Color(0xFFEEF2FF);
  static const rest = Color(0xFF06B6D4);
  static const restBg = Color(0xFFECFEFF);
  static const general = Color(0xFF64748B);
  static const generalBg = Color(0xFFF8FAFC);

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

ThemeData buildAppTheme() {
  return ThemeData(
    useMaterial3: true,
    colorSchemeSeed: HiBuddyColors.primary,
    scaffoldBackgroundColor: HiBuddyColors.bg,
    appBarTheme: const AppBarTheme(
      backgroundColor: HiBuddyColors.primary,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w800,
        color: Colors.white,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: HiBuddyColors.primary,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
      ),
    ),
    cardTheme: CardThemeData(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      color: HiBuddyColors.cardBg,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: HiBuddyColors.border),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
  );
}
