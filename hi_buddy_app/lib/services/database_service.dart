import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseService {
  static Database? _db;

  static Future<Database> get db async {
    if (_db != null) return _db!;
    _db = await _initDB();
    return _db!;
  }

  static Future<Database> _initDB() async {
    final path = join(await getDatabasesPath(), 'harumate.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        // 사용자 프로필
        await db.execute('''
          CREATE TABLE user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            disability_level TEXT DEFAULT 'mild',
            ui_mode TEXT DEFAULT 'normal',
            tts_speed REAL DEFAULT 0.45,
            wake_time TEXT DEFAULT '08:00',
            sleep_time TEXT DEFAULT '22:00',
            user_type TEXT DEFAULT 'user'
          )
        ''');

        // 식재료 (냉장고)
        await db.execute('''
          CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT '기타',
            added_date TEXT NOT NULL
          )
        ''');

        // 일정 템플릿 (매일 반복)
        await db.execute('''
          CREATE TABLE daily_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER DEFAULT 0,
            time TEXT NOT NULL,
            type TEXT DEFAULT 'GENERAL',
            task TEXT NOT NULL,
            guide_script TEXT DEFAULT '[]'
          )
        ''');

        // 수행 기록
        await db.execute('''
          CREATE TABLE completion_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT,
            activity_type TEXT,
            task TEXT,
            completed INTEGER DEFAULT 0,
            steps_total INTEGER DEFAULT 0,
            steps_completed INTEGER DEFAULT 0,
            needed_help INTEGER DEFAULT 0
          )
        ''');

        // 긴급 연락처
        await db.execute('''
          CREATE TABLE emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            relationship TEXT DEFAULT '기타'
          )
        ''');

        // 약 알림
        await db.execute('''
          CREATE TABLE medicine_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT NOT NULL,
            days TEXT DEFAULT '매일'
          )
        ''');

        // 자주 가는 장소
        await db.execute('''
          CREATE TABLE places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT DEFAULT ''
          )
        ''');

        // 기본 프로필 생성
        await db.insert('user_profile', {
          'name': '사용자',
          'disability_level': 'mild',
          'ui_mode': 'normal',
          'tts_speed': 0.45,
          'wake_time': '08:00',
          'sleep_time': '22:00',
          'user_type': 'user',
        });
      },
    );
  }

  // ── 프로필 ──
  static Future<Map<String, dynamic>> getProfile() async {
    final d = await db;
    final rows = await d.query('user_profile', limit: 1);
    if (rows.isEmpty) {
      return {'name': '사용자', 'disability_level': 'mild', 'ui_mode': 'normal', 'tts_speed': 0.45};
    }
    return rows.first;
  }

  static Future<void> updateProfile(Map<String, dynamic> data) async {
    final d = await db;
    final rows = await d.query('user_profile', limit: 1);
    if (rows.isEmpty) {
      await d.insert('user_profile', data);
    } else {
      await d.update('user_profile', data, where: 'id = ?', whereArgs: [rows.first['id']]);
    }
  }

  // ── 식재료 ──
  static Future<List<Map<String, dynamic>>> getIngredients() async {
    final d = await db;
    return d.query('ingredients', orderBy: 'added_date DESC');
  }

  static Future<void> addIngredient(String name, {String category = '기타'}) async {
    final d = await db;
    await d.insert('ingredients', {
      'name': name,
      'category': category,
      'added_date': DateTime.now().toIso8601String(),
    });
  }

  static Future<void> removeIngredient(int id) async {
    final d = await db;
    await d.delete('ingredients', where: 'id = ?', whereArgs: [id]);
  }

  // ── 수행 기록 ──
  static Future<void> logCompletion({
    required String date,
    required String activityType,
    required String task,
    required bool completed,
    int stepsTotal = 0,
    int stepsCompleted = 0,
    bool neededHelp = false,
  }) async {
    final d = await db;
    await d.insert('completion_log', {
      'date': date,
      'activity_type': activityType,
      'task': task,
      'completed': completed ? 1 : 0,
      'steps_total': stepsTotal,
      'steps_completed': stepsCompleted,
      'needed_help': neededHelp ? 1 : 0,
    });
  }

  static Future<List<Map<String, dynamic>>> getCompletionLogs({String? date, int limit = 50}) async {
    final d = await db;
    if (date != null) {
      return d.query('completion_log', where: 'date = ?', whereArgs: [date], orderBy: 'id DESC', limit: limit);
    }
    return d.query('completion_log', orderBy: 'date DESC, id DESC', limit: limit);
  }

  // ── 긴급 연락처 ──
  static Future<List<Map<String, dynamic>>> getEmergencyContacts() async {
    final d = await db;
    return d.query('emergency_contacts');
  }

  static Future<void> addEmergencyContact(String name, String phone, {String relationship = '기타'}) async {
    final d = await db;
    await d.insert('emergency_contacts', {'name': name, 'phone': phone, 'relationship': relationship});
  }

  static Future<void> removeEmergencyContact(int id) async {
    final d = await db;
    await d.delete('emergency_contacts', where: 'id = ?', whereArgs: [id]);
  }

  // ── 약 알림 ──
  static Future<List<Map<String, dynamic>>> getMedicineSchedules() async {
    final d = await db;
    return d.query('medicine_schedule');
  }

  static Future<void> addMedicine(String name, String time, {String days = '매일'}) async {
    final d = await db;
    await d.insert('medicine_schedule', {'name': name, 'time': time, 'days': days});
  }

  static Future<void> removeMedicine(int id) async {
    final d = await db;
    await d.delete('medicine_schedule', where: 'id = ?', whereArgs: [id]);
  }

  // ── 자주 가는 장소 ──
  static Future<List<Map<String, dynamic>>> getPlaces() async {
    final d = await db;
    return d.query('places');
  }

  static Future<void> addPlace(String name, {String address = ''}) async {
    final d = await db;
    await d.insert('places', {'name': name, 'address': address});
  }

  static Future<void> removePlace(int id) async {
    final d = await db;
    await d.delete('places', where: 'id = ?', whereArgs: [id]);
  }
}
