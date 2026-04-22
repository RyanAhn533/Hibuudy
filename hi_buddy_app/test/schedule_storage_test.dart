import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:harumate/services/schedule_storage.dart';
import 'package:harumate/models/schedule_item.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('ScheduleStorage', () {
    test('초기엔 null 반환', () async {
      expect(await ScheduleStorage.load(), isNull);
    });

    test('save 후 load 동일', () async {
      final items = [
        ScheduleItem(time: '08:00', type: 'MORNING_BRIEFING', task: '아침 안내'),
        ScheduleItem(time: '12:00', type: 'COOKING', task: '점심 만들기'),
      ];
      final schedule = Schedule(date: '2026-04-22', items: items);
      await ScheduleStorage.save(schedule);

      final loaded = await ScheduleStorage.load();
      expect(loaded, isNotNull);
      expect(loaded!.items.length, 2);
      expect(loaded.items[0].time, '08:00');
      expect(loaded.items[1].task, '점심 만들기');
    });

    test('savedDates 저장된 날짜 목록 반환', () async {
      await ScheduleStorage.save(
        Schedule(date: '2026-04-22', items: []),
      );
      await ScheduleStorage.save(
        Schedule(date: '2026-04-23', items: []),
      );
      final dates = await ScheduleStorage.savedDates();
      expect(dates.length, 2);
      expect(dates[0], '2026-04-23'); // 최신순
    });

    test('clear() 후 빈 상태', () async {
      await ScheduleStorage.save(
        Schedule(date: '2026-04-22', items: []),
      );
      await ScheduleStorage.clear();
      expect(await ScheduleStorage.load(), isNull);
    });

    test('pullFromServer: 페어 코드 없으면 false', () async {
      // SessionService는 pair_code 없는 상태
      expect(await ScheduleStorage.pullFromServer(), false);
    });
  });
}
