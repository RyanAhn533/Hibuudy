import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as tz_data;
import 'package:timezone/timezone.dart' as tz;
import 'database_service.dart';
import 'schedule_storage.dart';

/// ══════════════════════════════════════════════════════════
/// NotificationService — 로컬 푸시 알림
///
/// 박민호 페르소나 요구사항:
/// "약 시간, 활동 시작 시간. 당사자 폰에서 자동 울려야 함."
///
/// 지원:
/// 1. 활동 시작 알림 (매일 일정 시간에)
/// 2. 약 복용 알림 (매일 해당 시간)
/// 3. 아침 브리핑 (7:00 매일)
///
/// Firebase 의존성 없음 · 로컬 스케줄링만
/// ══════════════════════════════════════════════════════════
class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) return;
    tz_data.initializeTimeZones();
    tz.setLocalLocation(tz.getLocation('Asia/Seoul'));

    const android = AndroidInitializationSettings('ic_launcher');
    const ios = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    await _plugin.initialize(
      const InitializationSettings(android: android, iOS: ios),
    );
    _initialized = true;
  }

  /// 런타임 권한 요청 (Android 13+, iOS)
  static Future<bool> requestPermission() async {
    await init();
    final android = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    final iosGranted = await _plugin
        .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin>()
        ?.requestPermissions(alert: true, badge: true, sound: true);
    final androidGranted = await android?.requestNotificationsPermission();
    return (androidGranted ?? true) && (iosGranted ?? true);
  }

  /// 예약된 모든 알림 취소
  static Future<void> cancelAll() async {
    await init();
    await _plugin.cancelAll();
  }

  /// 오늘 일정 + 약 알림 전체 리스케줄 (앱 시작 시 호출)
  static Future<void> rescheduleAll() async {
    await init();
    await cancelAll();

    await _scheduleScheduleItems();
    await _scheduleMedicineReminders();
    await _scheduleMorningBriefing();
  }

  // ── 일정 활동 알림 ──
  static Future<void> _scheduleScheduleItems() async {
    final schedule = await ScheduleStorage.load();
    if (schedule == null) return;

    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'schedule',
        '일정 알림',
        channelDescription: '오늘 활동 시작 시간 알림',
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: DarwinNotificationDetails(),
    );

    int id = 0;
    for (final item in schedule.items) {
      final parts = item.time.split(':');
      if (parts.length != 2) continue;
      final hour = int.tryParse(parts[0]);
      final minute = int.tryParse(parts[1]);
      if (hour == null || minute == null) continue;

      final scheduled = _nextInstanceOf(hour, minute);
      await _plugin.zonedSchedule(
        id++,
        '${item.time} · ${item.task}',
        '${_typeLabel(item.type)} 시간이에요',
        scheduled,
        details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        matchDateTimeComponents: DateTimeComponents.time,
      );
    }
  }

  // ── 약 복용 알림 ──
  static Future<void> _scheduleMedicineReminders() async {
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'medicine',
        '약 알림',
        channelDescription: '복약 시간 알림',
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: DarwinNotificationDetails(),
    );

    final meds = await DatabaseService.getMedicineSchedules();
    int id = 100;
    for (final m in meds) {
      final time = (m['time'] as String?) ?? '';
      final parts = time.split(':');
      if (parts.length != 2) continue;
      final hour = int.tryParse(parts[0]);
      final minute = int.tryParse(parts[1]);
      if (hour == null || minute == null) continue;

      final scheduled = _nextInstanceOf(hour, minute);
      await _plugin.zonedSchedule(
        id++,
        '약 드실 시간이에요',
        '${m['name']} ${m['time']}',
        scheduled,
        details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        matchDateTimeComponents: DateTimeComponents.time,
      );
    }
  }

  // ── 아침 브리핑 (7시 고정) ──
  static Future<void> _scheduleMorningBriefing() async {
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'morning',
        '아침 브리핑',
        channelDescription: '오늘 하루 안내',
        importance: Importance.defaultImportance,
      ),
      iOS: DarwinNotificationDetails(),
    );

    await _plugin.zonedSchedule(
      999,
      '좋은 아침이에요',
      '오늘 하루를 확인해보세요',
      _nextInstanceOf(7, 0),
      details,
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      matchDateTimeComponents: DateTimeComponents.time,
    );
  }

  static tz.TZDateTime _nextInstanceOf(int hour, int minute) {
    final now = tz.TZDateTime.now(tz.local);
    var scheduled = tz.TZDateTime(
      tz.local,
      now.year,
      now.month,
      now.day,
      hour,
      minute,
    );
    if (scheduled.isBefore(now)) {
      scheduled = scheduled.add(const Duration(days: 1));
    }
    return scheduled;
  }

  static String _typeLabel(String type) {
    switch (type.toUpperCase()) {
      case 'COOKING':
      case 'MEAL':
        return '요리';
      case 'HEALTH':
        return '운동';
      case 'CLOTHING':
        return '옷 입기';
      case 'LEISURE':
        return '여가';
      case 'MORNING_BRIEFING':
        return '아침 안내';
      case 'NIGHT_WRAPUP':
        return '저녁 마무리';
      case 'REST':
        return '쉬는 시간';
      default:
        return '활동';
    }
  }
}
