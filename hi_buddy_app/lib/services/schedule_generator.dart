/// 오프라인 일정 생성기.
/// LLM 호출 없이 정규식 + 템플릿으로 즉시 일정 생성.
/// 서버 불필요, rate limit 없음, 오프라인 동작.

import '../models/schedule_item.dart';

class ScheduleGenerator {
  /// 자연어 텍스트 → 스케줄 아이템 리스트 (즉시, 오프라인)
  static List<ScheduleItem> generate(String text) {
    final lines = text
        .split(RegExp(r'[\n·•\-]'))
        .map((l) => l.trim())
        .where((l) => l.isNotEmpty)
        .toList();

    final items = <ScheduleItem>[];

    for (final line in lines) {
      final match = RegExp(r'(\d{1,2}:\d{2})\s*(.+)').firstMatch(line);
      if (match == null) continue;

      final time = _normalizeTime(match.group(1)!);
      final task = match.group(2)!.trim();
      final type = _classifyType(task);
      final guide = _generateGuide(type, task);

      items.add(ScheduleItem(
        time: time,
        type: type,
        task: task,
        guideScript: guide,
      ));
    }

    items.sort((a, b) => a.timeMinutes.compareTo(b.timeMinutes));
    return items;
  }

  /// 시간 정규화 (8:00 → 08:00)
  static String _normalizeTime(String raw) {
    final parts = raw.split(':');
    if (parts.length != 2) return raw;
    final h = parts[0].padLeft(2, '0');
    final m = parts[1].padLeft(2, '0');
    return '$h:$m';
  }

  /// 키워드 기반 활동 타입 분류
  static String _classifyType(String task) {
    final t = task.toLowerCase();

    // 아침/마무리
    if (_matchAny(t, ['아침 인사', '일정 안내', '오늘 일정', '날씨'])) {
      return 'MORNING_BRIEFING';
    }
    if (_matchAny(t, ['마무리', '취침', '잠자기', '하루 끝'])) {
      return 'NIGHT_WRAPUP';
    }

    // 요리
    if (_matchAny(t, ['만들기', '요리', '조리', '끓이기', '볶기', '레시피', '굽기'])) {
      return 'COOKING';
    }

    // 식사
    if (_matchAny(t, ['먹기', '식사', '점심', '저녁', '아침밥', '간식', '밥'])) {
      return 'MEAL';
    }

    // 운동
    if (_matchAny(t, ['운동', '체조', '스트레칭', '산책', '걷기', '헬스', '체력'])) {
      return 'HEALTH';
    }

    // 옷
    if (_matchAny(t, ['옷', '갈아입기', '옷 입기', '착용'])) {
      return 'CLOTHING';
    }

    // 여가
    if (_matchAny(t, ['쉬기', '휴식', 'tv', '영화', '게임', '놀이', '여가', '쉬는'])) {
      return 'LEISURE';
    }

    // 위생/루틴
    if (_matchAny(t, ['세수', '양치', '샤워', '정리', '청소', '준비'])) {
      return 'ROUTINE';
    }

    return 'GENERAL';
  }

  static bool _matchAny(String text, List<String> keywords) {
    return keywords.any((kw) => text.contains(kw));
  }

  /// 활동 타입별 가이드 스크립트 템플릿
  static List<String> _generateGuide(String type, String task) {
    switch (type) {
      case 'MORNING_BRIEFING':
        return [
          '좋은 아침이에요.',
          '오늘 하루 계획을 같이 살펴볼까요?',
        ];
      case 'NIGHT_WRAPUP':
        return [
          '오늘 하루 수고했어요.',
          '내일도 좋은 하루 보내요.',
        ];
      case 'COOKING':
        return [
          '지금은 요리 시간이에요.',
          '$task 해볼까요?',
          '레시피를 따라 천천히 해봐요.',
        ];
      case 'MEAL':
        return [
          '지금은 식사 시간이에요.',
          '$task 해볼까요?',
          '맛있게 먹어요.',
        ];
      case 'HEALTH':
        return [
          '지금은 운동 시간이에요.',
          '몸을 천천히 움직여 볼까요?',
          '무리하지 않아도 괜찮아요.',
        ];
      case 'CLOTHING':
        return [
          '옷을 갈아입을 시간이에요.',
          '천천히 한 단계씩 해봐요.',
        ];
      case 'LEISURE':
        return [
          '지금은 쉬는 시간이에요.',
          '편하게 쉬어요.',
        ];
      case 'ROUTINE':
        return [
          '$task 시간이에요.',
          '천천히 해봐요.',
        ];
      default:
        return [
          '지금 할 일은 $task 이에요.',
          '천천히 해봐요.',
        ];
    }
  }
}
