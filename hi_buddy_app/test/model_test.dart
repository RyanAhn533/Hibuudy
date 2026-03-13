import 'package:flutter_test/flutter_test.dart';
import 'package:hi_buddy_app/models/schedule_item.dart';
import 'package:hi_buddy_app/models/recipe.dart';

void main() {
  group('ScheduleItem', () {
    test('fromJson parses correctly', () {
      final json = {
        'time': '08:00',
        'type': 'COOKING',
        'task': '아침밥 만들기',
        'guide_script': ['냄비를 준비해요', '물을 넣어요'],
        'menus': [
          {'name': '라면', 'image': '', 'video_url': ''},
          {'name': '김치볶음밥', 'image': '', 'video_url': ''},
        ],
      };

      final item = ScheduleItem.fromJson(json);
      expect(item.time, '08:00');
      expect(item.type, 'COOKING');
      expect(item.task, '아침밥 만들기');
      expect(item.guideScript.length, 2);
      expect(item.menus.length, 2);
      expect(item.menus[0].name, '라면');
      expect(item.timeMinutes, 480); // 8 * 60
    });

    test('toJson round-trips correctly', () {
      final item = ScheduleItem(
        time: '12:30',
        type: 'HEALTH',
        task: '운동하기',
        guideScript: ['스트레칭 해요', '달리기 해요'],
      );

      final json = item.toJson();
      final restored = ScheduleItem.fromJson(json);
      expect(restored.time, '12:30');
      expect(restored.type, 'HEALTH');
      expect(restored.task, '운동하기');
      expect(restored.guideScript.length, 2);
    });

    test('timeMinutes calculates correctly', () {
      expect(ScheduleItem(time: '00:00', type: '', task: '').timeMinutes, 0);
      expect(ScheduleItem(time: '23:59', type: '', task: '').timeMinutes, 1439);
      expect(ScheduleItem(time: '12:30', type: '', task: '').timeMinutes, 750);
    });
  });

  group('Schedule', () {
    test('fromJson sorts by time', () {
      final json = {
        'date': '2026-03-13',
        'schedule': [
          {'time': '18:00', 'type': 'HEALTH', 'task': '운동'},
          {'time': '08:00', 'type': 'MORNING_BRIEFING', 'task': '아침'},
          {'time': '12:00', 'type': 'COOKING', 'task': '점심'},
        ],
      };

      final schedule = Schedule.fromJson(json);
      expect(schedule.date, '2026-03-13');
      expect(schedule.items.length, 3);
      expect(schedule.items[0].time, '08:00');
      expect(schedule.items[1].time, '12:00');
      expect(schedule.items[2].time, '18:00');
    });

    test('empty schedule handled', () {
      final schedule = Schedule.fromJson({'date': '2026-01-01'});
      expect(schedule.items, isEmpty);
    });
  });

  group('Recipe', () {
    test('getRecipe returns known recipe', () {
      final recipe = getRecipe('라면');
      expect(recipe, isNotNull);
      expect(recipe!.name, '라면');
      expect(recipe.tools, isNotEmpty);
      expect(recipe.ingredients, isNotEmpty);
      expect(recipe.steps.length, 5);
    });

    test('getRecipe returns null for unknown', () {
      expect(getRecipe('존재하지않는메뉴'), isNull);
    });

    test('all recipes have required fields', () {
      for (final name in getAllRecipeNames()) {
        final r = getRecipe(name)!;
        expect(r.name, isNotEmpty, reason: '$name missing name');
        expect(r.steps, isNotEmpty, reason: '$name missing steps');
      }
    });
  });

  group('HealthRoutine', () {
    test('seated routine exists', () {
      final routine = getHealthRoutine('seated');
      expect(routine, isNotNull);
      expect(routine!.title, '앉아서 하는 운동');
      expect(routine.steps.length, greaterThan(3));
    });

    test('standing routine exists', () {
      final routine = getHealthRoutine('standing');
      expect(routine, isNotNull);
      expect(routine!.title, '서서 하는 운동');
    });

    test('unknown routine returns null', () {
      expect(getHealthRoutine('flying'), isNull);
    });
  });
}
