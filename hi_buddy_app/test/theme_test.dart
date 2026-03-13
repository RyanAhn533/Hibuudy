import 'package:flutter_test/flutter_test.dart';
import 'package:hi_buddy_app/theme/app_theme.dart';

void main() {
  group('HiBuddyColors', () {
    test('getActivityColor returns distinct colors per type', () {
      final types = [
        'COOKING', 'HEALTH', 'CLOTHING', 'LEISURE',
        'MORNING_BRIEFING', 'NIGHT_WRAPUP', 'REST',
      ];

      final colors = types.map(HiBuddyColors.getActivityColor).toSet();
      // All types should have distinct colors
      expect(colors.length, types.length);
    });

    test('getActivityEmoji returns emoji for all types', () {
      final types = [
        'COOKING', 'MEAL', 'HEALTH', 'CLOTHING', 'LEISURE',
        'MORNING_BRIEFING', 'NIGHT_WRAPUP', 'REST', 'ROUTINE', 'UNKNOWN',
      ];

      for (final type in types) {
        final emoji = HiBuddyColors.getActivityEmoji(type);
        expect(emoji, isNotEmpty, reason: 'No emoji for $type');
      }
    });

    test('getActivityLabel returns Korean labels', () {
      expect(HiBuddyColors.getActivityLabel('COOKING'), '요리');
      expect(HiBuddyColors.getActivityLabel('HEALTH'), '운동');
      expect(HiBuddyColors.getActivityLabel('CLOTHING'), '옷 입기');
      expect(HiBuddyColors.getActivityLabel('MORNING_BRIEFING'), '아침 안내');
    });

    test('getActivityBgColor returns lighter color than activity color', () {
      // Background colors should have higher lightness
      final types = ['COOKING', 'HEALTH', 'REST'];
      for (final type in types) {
        final color = HiBuddyColors.getActivityColor(type);
        final bgColor = HiBuddyColors.getActivityBgColor(type);
        // bg should be lighter (higher luminance)
        expect(
          bgColor.computeLuminance(),
          greaterThan(color.computeLuminance()),
          reason: 'BG color for $type should be lighter than activity color',
        );
      }
    });
  });

  group('Theme', () {
    test('buildAppTheme creates valid ThemeData', () {
      final theme = buildAppTheme();
      expect(theme, isNotNull);
      expect(theme.useMaterial3, true);
      expect(theme.scaffoldBackgroundColor, HiBuddyColors.bg);
    });
  });
}
