import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/schedule_item.dart';
import 'api_service.dart';
import 'session_service.dart';

/// 날짜별 스케줄 저장소.
/// - 날짜별로 분리 저장 (최근 7일 보관)
/// - 마지막으로 저장된 스케줄을 항상 폴백으로 유지
class ScheduleStorage {
  static const _prefix = 'hibuddy_schedule_';
  static const _latestKey = 'hibuddy_latest_date';
  static const _maxDays = 7;

  /// 날짜별 키 생성 (yyyy-MM-dd)
  static String _keyFor(String date) => '$_prefix$date';

  /// 스케줄 저장 (날짜별 + 최신 날짜 기록)
  /// v3.1: 페어 코드 있으면 서버에도 자동 싱크 (코디 ↔ 당사자 공유)
  static Future<void> save(Schedule schedule) async {
    final prefs = await SharedPreferences.getInstance();
    final date = schedule.date;

    await prefs.setString(_keyFor(date), jsonEncode(schedule.toJson()));
    await prefs.setString(_latestKey, date);

    // 오래된 스케줄 정리
    await _cleanup(prefs);

    // 서버 싱크 (fire-and-forget — 실패해도 로컬은 저장됨)
    _syncToServer(schedule);
  }

  static Future<void> _syncToServer(Schedule schedule) async {
    try {
      final pairCode = await SessionService.getPairCode();
      if (pairCode == null || pairCode.isEmpty) return;

      await ApiService.saveScheduleToServer(
        pairCode,
        schedule.date,
        schedule.items.map((i) => i.toJson()).toList(),
      );
    } catch (_) {
      // 서버 오류 무시 — 로컬엔 이미 저장됨
    }
  }

  /// 서버에서 최신 스케줄 가져와서 로컬 업데이트 (페어 코드 기반)
  /// 당사자 앱이 코디가 저장한 일정을 받을 때 사용
  /// 30초마다 호출하면 실시간 싱크 효과
  static Future<bool> pullFromServer() async {
    try {
      final pairCode = await SessionService.getPairCode();
      if (pairCode == null || pairCode.isEmpty) return false;

      final data = await ApiService.loadScheduleFromServer(pairCode);
      if (data == null) return false;

      final date = data['date'] as String?;
      final rawItems = data['data'] as String?;
      if (date == null || rawItems == null) return false;

      final itemsJson = jsonDecode(rawItems) as List;
      final items = itemsJson
          .map((e) => ScheduleItem.fromJson(e as Map<String, dynamic>))
          .toList();

      final schedule = Schedule(date: date, items: items);

      // 로컬에 저장 (중복 서버 push 방지하려고 _syncToServer 건너뜀)
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_keyFor(date), jsonEncode(schedule.toJson()));
      await prefs.setString(_latestKey, date);
      return true;
    } catch (_) {
      return false;
    }
  }

  /// 특정 날짜 스케줄 불러오기
  static Future<Schedule?> loadByDate(String date) async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString(_keyFor(date));
    if (str == null) return null;
    try {
      return Schedule.fromJson(jsonDecode(str) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  /// 오늘 스케줄 불러오기. 없으면 가장 최근 스케줄 반환.
  static Future<Schedule?> load() async {
    final prefs = await SharedPreferences.getInstance();

    // 1) 오늘 날짜로 먼저 시도
    final today = _todayString();
    final todaySchedule = await loadByDate(today);
    if (todaySchedule != null) return todaySchedule;

    // 2) 마지막으로 저장된 날짜의 스케줄 반환 (오프라인 폴백)
    final latestDate = prefs.getString(_latestKey);
    if (latestDate != null) {
      return loadByDate(latestDate);
    }

    // 3) 레거시 키 마이그레이션 (기존 단일 키에서 업그레이드)
    final legacy = prefs.getString('hibuddy_schedule');
    if (legacy != null) {
      try {
        final schedule =
            Schedule.fromJson(jsonDecode(legacy) as Map<String, dynamic>);
        await save(schedule); // 새 형식으로 마이그레이션
        await prefs.remove('hibuddy_schedule');
        return schedule;
      } catch (_) {
        await prefs.remove('hibuddy_schedule');
      }
    }

    return null;
  }

  /// 특정 날짜 스케줄 삭제
  static Future<void> clearByDate(String date) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyFor(date));
  }

  /// 전체 삭제
  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    // Copy to list first to avoid concurrent modification
    final keys = prefs
        .getKeys()
        .where((k) => k.startsWith(_prefix) || k == _latestKey)
        .toList();
    for (final key in keys) {
      await prefs.remove(key);
    }
    // 레거시 키도 삭제
    await prefs.remove('hibuddy_schedule');
  }

  /// 저장된 날짜 목록 (최신순)
  static Future<List<String>> savedDates() async {
    final prefs = await SharedPreferences.getInstance();
    final dates = prefs
        .getKeys()
        .where((k) => k.startsWith(_prefix))
        .map((k) => k.substring(_prefix.length))
        .toList()
      ..sort((a, b) => b.compareTo(a));
    return dates;
  }

  /// 오래된 스케줄 정리
  static Future<void> _cleanup(SharedPreferences prefs) async {
    final dates = prefs
        .getKeys()
        .where((k) => k.startsWith(_prefix))
        .map((k) => k.substring(_prefix.length))
        .toList()
      ..sort((a, b) => b.compareTo(a)); // 최신순

    if (dates.length > _maxDays) {
      for (final old in dates.sublist(_maxDays)) {
        await prefs.remove(_keyFor(old));
      }
    }
  }

  static String _todayString() {
    final now = DateTime.now();
    return '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
  }
}
