import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/schedule_item.dart';

class ScheduleStorage {
  static const _key = 'hibuddy_schedule';

  static Future<void> save(Schedule schedule) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(schedule.toJson()));
  }

  static Future<Schedule?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString(_key);
    if (str == null) return null;
    try {
      return Schedule.fromJson(jsonDecode(str) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
