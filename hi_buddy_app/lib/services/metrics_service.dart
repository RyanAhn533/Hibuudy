import 'package:shared_preferences/shared_preferences.dart';
import 'database_service.dart';

/// ══════════════════════════════════════════════════════════
/// MetricsService — 3지표 계측 (P0-4)
/// 윤여경(2025) 3지표 + 이행률로 「보통의 하루」 11월 검증과 같은 언어를 만든다.
///   - 완료율  : completion_log(completed=1) / 계획된 일정 수
///   - 도움 요청: needed_help=1 건수 (SOS/도움 탭 전화) — "오류·막힘" 대리 지표
///   - 만족    : 감정 보드 mood 로그 (good/ok/hard)
/// 보호자 화면에는 숫자표 대신 문장 한 줄 (G2/G4: 56.6세 보호자, 감시 아닌 안심 톤).
/// ══════════════════════════════════════════════════════════
class WeeklySummary {
  final int days; // 집계 일수 (최대 7)
  final int activeDays; // 완료 기록이 1건 이상 있는 날
  final int totalDone; // 7일 완료 건수
  final int doneToday;
  final int plannedToday;
  final int helpCount; // 7일 도움 요청
  final int moodGood;
  final int moodOk;
  final int moodHard;

  const WeeklySummary({
    required this.days,
    required this.activeDays,
    required this.totalDone,
    required this.doneToday,
    required this.plannedToday,
    required this.helpCount,
    required this.moodGood,
    required this.moodOk,
    required this.moodHard,
  });

  bool get isEmpty => totalDone == 0 && helpCount == 0 && (moodGood + moodOk + moodHard) == 0;

  /// 보호자용 한 문장. 숫자는 최소, 톤은 "잘 지나가고 있다".
  String get sentence {
    if (isEmpty) return '아직 기록이 없어요. 오늘 일과를 시작하면 여기에 쌓여요.';
    final parts = <String>[];
    if (plannedToday > 0) {
      parts.add('오늘 $plannedToday개 중 $doneToday개 했어요');
    } else if (doneToday > 0) {
      parts.add('오늘 $doneToday개 했어요');
    }
    if (activeDays > 0) parts.add('이번 주 $activeDays일 활동');
    if (helpCount > 0) parts.add('도움 요청 $helpCount번');
    return '${parts.join(' · ')}.';
  }

  /// 기분 요약 (없으면 null)
  String? get moodSentence {
    final total = moodGood + moodOk + moodHard;
    if (total == 0) return null;
    if (moodHard >= 2 && moodHard >= moodGood) {
      return '이번 주 "힘들어"가 $moodHard번. 한 번 물어봐 주세요.';
    }
    if (moodGood > moodHard) return '이번 주 기분은 대체로 좋았어요.';
    return '이번 주 기분은 보통이었어요.';
  }
}

class MetricsService {
  MetricsService._();

  static const _kMoodLog = 'harumate_mood_log';

  static String _dateStr(DateTime d) => d.toIso8601String().substring(0, 10);

  static Future<WeeklySummary> weekly({int plannedToday = 0}) async {
    final now = DateTime.now();
    final today = _dateStr(now);
    final since = now.subtract(const Duration(days: 6));

    int totalDone = 0, doneToday = 0, helpCount = 0;
    final activeDates = <String>{};
    try {
      final logs = await DatabaseService.getCompletionLogs(limit: 500);
      for (final l in logs) {
        final date = (l['date'] ?? '') as String;
        if (date.isEmpty || date.compareTo(_dateStr(since)) < 0) continue;
        if (l['needed_help'] == 1) helpCount++;
        if (l['completed'] == 1) {
          totalDone++;
          activeDates.add(date);
          if (date == today) doneToday++;
        }
      }
    } catch (_) {}

    int good = 0, ok = 0, hard = 0;
    try {
      final prefs = await SharedPreferences.getInstance();
      for (final e in prefs.getStringList(_kMoodLog) ?? const <String>[]) {
        final i = e.indexOf('|');
        if (i < 0) continue;
        final ts = DateTime.tryParse(e.substring(0, i));
        if (ts == null || ts.isBefore(since)) continue;
        switch (e.substring(i + 1)) {
          case 'good':
            good++;
            break;
          case 'ok':
            ok++;
            break;
          case 'hard':
            hard++;
            break;
        }
      }
    } catch (_) {}

    return WeeklySummary(
      days: 7,
      activeDays: activeDates.length,
      totalDone: totalDone,
      doneToday: doneToday,
      plannedToday: plannedToday,
      helpCount: helpCount,
      moodGood: good,
      moodOk: ok,
      moodHard: hard,
    );
  }
}
