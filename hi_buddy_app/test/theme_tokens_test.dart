import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:harumate/theme/app_theme.dart';

void main() {
  group('HaruTokens', () {
    test('브랜드 컬러 값 검증', () {
      expect(HaruTokens.primary.toARGB32(), const Color(0xFF4F7CFF).toARGB32());
      expect(HaruTokens.accent.toARGB32(), const Color(0xFFFFB547).toARGB32());
      expect(HaruTokens.danger.toARGB32(), const Color(0xFFE8594A).toARGB32());
    });

    test('Radii 값 순서대로 증가', () {
      expect(HaruTokens.radiusSm < HaruTokens.radiusMd, true);
      expect(HaruTokens.radiusMd < HaruTokens.radiusLg, true);
      expect(HaruTokens.radiusLg < HaruTokens.radiusXl, true);
    });

    test('터치 타겟 최소 48dp (WCAG AAA)', () {
      expect(HaruTokens.minTouchTarget, greaterThanOrEqualTo(48));
    });

    test('Typography 스케일 단조 증가', () {
      expect(HaruTokens.tinySize < HaruTokens.smallSize, true);
      expect(HaruTokens.smallSize < HaruTokens.bodySize, true);
      expect(HaruTokens.bodySize < HaruTokens.h3Size, true);
      expect(HaruTokens.h3Size < HaruTokens.h2Size, true);
      expect(HaruTokens.h2Size < HaruTokens.h1Size, true);
      expect(HaruTokens.h1Size < HaruTokens.displaySize, true);
    });

    test('Font fallback에 Pretendard 포함', () {
      expect(HaruTokens.fontFamily, 'Pretendard');
      expect(HaruTokens.fontFamilyFallback, contains('Pretendard Variable'));
    });
  });

  group('buildAppTheme', () {
    test('일반 모드 테마 생성', () {
      final theme = buildAppTheme();
      expect(theme.useMaterial3, true);
      expect(theme.textTheme.bodyMedium?.fontFamily ?? 'Pretendard',
          contains('Pretendard'));
    });

    test('키오스크 모드 = 다크 배경', () {
      final theme = buildAppTheme(kioskMode: true);
      expect(theme.scaffoldBackgroundColor.toARGB32(),
          HaruTokens.kioskBg.toARGB32());
    });
  });

  group('HiBuddyColors (레거시 호환)', () {
    test('primary가 HaruTokens primary와 동일', () {
      expect(HiBuddyColors.primary.toARGB32(), HaruTokens.primary.toARGB32());
    });

    test('활동별 색상 타입 매핑 동작', () {
      expect(HiBuddyColors.getActivityColor('COOKING'),
          HiBuddyColors.cooking);
      expect(HiBuddyColors.getActivityColor('HEALTH'),
          HiBuddyColors.health);
      expect(HiBuddyColors.getActivityColor('UNKNOWN'),
          HiBuddyColors.general);
    });

    test('활동 라벨 한국어 매핑', () {
      expect(HiBuddyColors.getActivityLabel('COOKING'), '요리');
      expect(HiBuddyColors.getActivityLabel('HEALTH'), '운동');
      expect(HiBuddyColors.getActivityLabel('UNKNOWN'), '일정');
    });
  });
}
