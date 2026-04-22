import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// ══════════════════════════════════════════════════════════
/// ErrorReporter — Firebase Crashlytics 대체 경량 구현
/// · Flutter 에러 전역 캡처
/// · 로컬 파일에 저장 (최대 50개 순환)
/// · 다음 앱 시작 시 서버로 전송 (백엔드 /api/errors)
/// · Firebase 의존성 없이 MVP 수준 크래시 추적
/// ══════════════════════════════════════════════════════════
class ErrorReporter {
  static const String _apiBase = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://hibuudy.onrender.com',
  );
  static const int _maxEntries = 50;
  static const String _logFileName = 'harumate_errors.jsonl';
  static const String _kUnsentKey = 'harumate_error_unsent_count';

  /// Flutter 전역 에러 핸들러 설정. main() 초기에 호출.
  static void install() {
    FlutterError.onError = (details) {
      FlutterError.presentError(details);
      _capture('flutter', details.exceptionAsString(), details.stack?.toString() ?? '');
    };

    PlatformDispatcher.instance.onError = (error, stack) {
      _capture('platform', error.toString(), stack.toString());
      return true;
    };
  }

  /// 수동 에러 기록
  static void report(String tag, Object error, [StackTrace? stack]) {
    _capture(tag, error.toString(), stack?.toString() ?? '');
  }

  /// 쌓인 로그를 서버로 전송 (앱 시작 시 호출 권장)
  static Future<void> flush() async {
    try {
      final file = await _logFile();
      if (!await file.exists()) return;
      final content = await file.readAsString();
      if (content.trim().isEmpty) return;

      // 전송 (fire-and-forget · 실패해도 파일 유지)
      try {
        final resp = await http
            .post(
              Uri.parse('$_apiBase/api/errors'),
              headers: {'Content-Type': 'application/x-ndjson'},
              body: content,
            )
            .timeout(const Duration(seconds: 10));
        if (resp.statusCode == 200 || resp.statusCode == 204) {
          await file.writeAsString(''); // 전송 성공 시 로컬 비움
          final prefs = await SharedPreferences.getInstance();
          await prefs.setInt(_kUnsentKey, 0);
        }
      } catch (_) {
        // 서버 다운? 다음에 재시도
      }
    } catch (_) {}
  }

  // ── 내부 ──

  static void _capture(String tag, String message, String stack) async {
    final entry = {
      'ts': DateTime.now().toIso8601String(),
      'tag': tag,
      'msg': message.substring(0, message.length > 500 ? 500 : message.length),
      'stack': stack.substring(0, stack.length > 2000 ? 2000 : stack.length),
      'platform': defaultTargetPlatform.name,
    };
    debugPrint('[ErrorReporter:$tag] $message');

    try {
      final file = await _logFile();
      // 라인 단위 추가 (JSON Lines)
      final lines = (await file.exists())
          ? (await file.readAsLines())
          : <String>[];
      lines.add(jsonEncode(entry));
      // 최근 50개만 유지
      if (lines.length > _maxEntries) {
        lines.removeRange(0, lines.length - _maxEntries);
      }
      await file.writeAsString('${lines.join('\n')}\n');

      final prefs = await SharedPreferences.getInstance();
      final count = (prefs.getInt(_kUnsentKey) ?? 0) + 1;
      await prefs.setInt(_kUnsentKey, count);
    } catch (_) {}
  }

  static Future<File> _logFile() async {
    final dir = await getApplicationDocumentsDirectory();
    return File('${dir.path}/$_logFileName');
  }
}
