/// API 통합 테스트 - 백엔드 서버를 통한 테스트
///
/// 실행 방법:
///   1. 백엔드 서버 실행: cd backend && uvicorn main:app --reload
///   2. 테스트 실행:
///      cd hi_buddy_app
///      flutter test test/api_integration_test.dart \
///        --dart-define=API_BASE_URL=http://localhost:8000 \
///        --dart-define=API_TOKEN=your-token-here

import 'package:flutter_test/flutter_test.dart';
import 'package:hi_buddy_app/services/api_service.dart';

void main() {
  group('OpenAI API (via backend)', () {
    test('일정 생성 (generateSchedule)', () async {
      final items = await ApiService.generateSchedule(
        '08:00 · 아침 인사\n12:00 · 라면 먹기\n18:00 · 운동하기',
      );

      print('--- 생성된 일정 ---');
      for (final item in items) {
        print('[${item.time}] ${item.type} - ${item.task}');
        for (final g in item.guideScript) {
          print('  > $g');
        }
      }

      expect(items, isNotEmpty);
      expect(items.length, greaterThanOrEqualTo(3));

      // 시간순 정렬 확인
      for (int i = 1; i < items.length; i++) {
        expect(
          items[i].timeMinutes,
          greaterThanOrEqualTo(items[i - 1].timeMinutes),
          reason: '일정이 시간순으로 정렬되어야 합니다',
        );
      }
    }, timeout: const Timeout(Duration(seconds: 30)));

    test('일정 항목 수정 (editScheduleItem)', () async {
      final original = {
        'time': '12:00',
        'type': 'COOKING',
        'task': '라면 먹기',
        'guide_script': ['물을 끓여요', '면을 넣어요'],
      };

      final result = await ApiService.editScheduleItem(
        original,
        '시간을 13:00으로 바꾸고, 김치볶음밥으로 변경해줘',
      );

      print('--- 수정 결과 ---');
      print(result);

      expect(result, isNotNull);
      expect(
        result.containsKey('time') || result.containsKey('task'),
        true,
      );
    }, timeout: const Timeout(Duration(seconds: 30)));

    test('TTS 음성 합성', () async {
      final bytes = await ApiService.synthesizeTts('안녕하세요, 하이버디입니다.');

      print('--- TTS 결과 ---');
      print('생성된 오디오: ${bytes.length} bytes');

      expect(bytes, isNotEmpty);
      expect(bytes.length, greaterThan(1000));
    }, timeout: const Timeout(Duration(seconds: 15)));
  });

  group('YouTube API (via backend)', () {
    test('유튜브 검색', () async {
      final results = await ApiService.searchYouTube(
        '발달장애 요리 교육',
        maxResults: 3,
      );

      print('--- YouTube 검색 결과 ---');
      for (final r in results) {
        print('${r['title']} → ${r['url']}');
      }

      expect(results, isNotEmpty);
      expect(results.first['videoId'], isNotEmpty);
      expect(results.first['title'], isNotEmpty);
    }, timeout: const Timeout(Duration(seconds: 15)));
  });

  group('Google Image API (via backend)', () {
    test('이미지 검색', () async {
      final results = await ApiService.searchImages('라면 요리', maxResults: 3);

      print('--- 이미지 검색 결과 ---');
      for (final r in results) {
        print('${r['title']} → ${r['link']}');
      }

      expect(results, isNotEmpty);
      expect(results.first['link'], isNotEmpty);
    }, timeout: const Timeout(Duration(seconds: 15)));
  });

  group('End-to-End Flow', () {
    test('전체 플로우: 일정 생성 → TTS → YouTube 검색', () async {
      // 1) 일정 생성
      final items = await ApiService.generateSchedule(
        '08:00 · 오늘 일정 안내\n12:00 · 간장계란밥 만들기\n15:00 · 앉아서 운동\n22:00 · 하루 마무리',
      );
      expect(items, isNotEmpty);
      print('일정 ${items.length}개 생성 완료');

      // 2) 첫 번째 항목의 TTS 생성
      final firstTask = items.first.task;
      final ttsBytes = await ApiService.synthesizeTts(
        '지금은 $firstTask 시간이에요.',
      );
      expect(ttsBytes, isNotEmpty);
      print('TTS ${ttsBytes.length} bytes 생성 완료');

      // 3) YouTube 검색
      final videos = await ApiService.searchYouTube(
        '간장계란밥 만들기 쉬운',
        maxResults: 2,
      );
      expect(videos, isNotEmpty);
      print('YouTube ${videos.length}개 결과 검색 완료');

      print('\n전체 플로우 테스트 성공!');
    }, timeout: const Timeout(Duration(seconds: 60)));
  });
}
