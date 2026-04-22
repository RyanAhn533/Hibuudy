import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:harumate/services/chat_memory.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('ChatMemory', () {
    test('초기엔 빈 리스트', () async {
      expect(await ChatMemory.getActive(), isEmpty);
    });

    test('addTurn 후 getActive에 반영', () async {
      await ChatMemory.addTurn('저녁 뭐 먹지', '김치볶음밥 어때요');
      final history = await ChatMemory.getActive();
      expect(history.length, 2);
      expect(history[0]['role'], 'user');
      expect(history[0]['content'], '저녁 뭐 먹지');
      expect(history[1]['role'], 'assistant');
    });

    test('최대 3턴 = 6개 엔트리 유지', () async {
      for (int i = 0; i < 5; i++) {
        await ChatMemory.addTurn('user$i', 'assistant$i');
      }
      final history = await ChatMemory.getActive();
      expect(history.length, 6); // 3 turns × 2 entries
    });

    test('clear() 후 빈 상태', () async {
      await ChatMemory.addTurn('테스트', '응답');
      await ChatMemory.clear();
      expect(await ChatMemory.getActive(), isEmpty);
    });

    test('getSummary 빈 세션이면 빈 문자열', () async {
      expect(await ChatMemory.getSummary(), '');
    });

    test('getSummary 내용 있으면 최근 대화 요약', () async {
      await ChatMemory.addTurn('라면 끓이는 법', '냄비에 물을 부어요');
      final summary = await ChatMemory.getSummary();
      expect(summary, contains('최근 대화'));
    });
  });
}
