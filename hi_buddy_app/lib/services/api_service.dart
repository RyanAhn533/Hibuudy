import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:http/http.dart' as http;
import '../models/schedule_item.dart';

/// Backend proxy API service.
/// API 키는 서버에서만 관리되며, 앱은 서버만 호출합니다.
class ApiService {
  // ── Configuration (injected via --dart-define at build time) ──
  static const String _baseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'https://hibuudy.onrender.com');
  static const String _authToken =
      String.fromEnvironment('API_TOKEN', defaultValue: 'hibuddy-2026-a7f3e9b1c4d2');

  static const Duration _timeout = Duration(seconds: 30);
  static const int _maxRetries = 2;

  // ── Shared headers ──
  static Map<String, String> get _headers => {
        'Authorization': 'Bearer $_authToken',
        'Content-Type': 'application/json',
      };

  // ── 네트워크 연결 확인 ──
  static Future<bool> isOnline() async {
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ── Retry with exponential backoff ──
  static Future<http.Response> _retryRequest(
    Future<http.Response> Function() request,
  ) async {
    http.Response? lastResponse;
    for (int attempt = 0; attempt <= _maxRetries; attempt++) {
      try {
        final resp = await request().timeout(_timeout);
        if (resp.statusCode < 500) return resp;
        lastResponse = resp;
      } on SocketException {
        throw const NetworkException('인터넷이 연결되지 않았어요.\n와이파이를 확인해 주세요.');
      } catch (e) {
        if (e is NetworkException) rethrow;
        if (attempt == _maxRetries) rethrow;
      }
      // Exponential backoff: 1s, 2s
      await Future.delayed(Duration(seconds: pow(2, attempt).toInt()));
    }
    return lastResponse!;
  }

  // ── Safe error message (발달장애인 사용자 맞춤) ──
  static String _safeError(http.Response resp, String service) {
    switch (resp.statusCode) {
      case 401:
        return '앱을 업데이트해 주세요.';
      case 429:
        return '잠시 쉬었다가 다시 해볼까요?\n너무 많이 눌렀어요.';
      case >= 500:
        return '서버가 잠깐 쉬고 있어요.\n조금 후에 다시 해볼까요?';
      default:
        return '$service 요청이 안 됐어요.\n다시 시도해 주세요.';
    }
  }

  // ── 1. Generate Schedule ──
  static Future<List<ScheduleItem>> generateSchedule(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) {
      throw Exception('일정 내용을 입력해 주세요.');
    }

    final resp = await _retryRequest(() => http.post(
          Uri.parse('$_baseUrl/api/schedule/generate'),
          headers: _headers,
          body: jsonEncode({'text': trimmed}),
        ));

    if (resp.statusCode != 200) {
      throw Exception(_safeError(resp, '일정 생성'));
    }

    final data = jsonDecode(resp.body);
    final list = data['schedule'] as List<dynamic>? ?? [];
    return list
        .map((e) => ScheduleItem.fromJson(e as Map<String, dynamic>))
        .toList()
      ..sort((a, b) => a.timeMinutes.compareTo(b.timeMinutes));
  }

  // ── 2. Edit Schedule Item ──
  static Future<Map<String, dynamic>> editScheduleItem(
    Map<String, dynamic> currentItem,
    String request,
  ) async {
    final trimmed = request.trim();
    if (trimmed.isEmpty) {
      throw Exception('수정 요청을 입력해 주세요.');
    }

    final resp = await _retryRequest(() => http.post(
          Uri.parse('$_baseUrl/api/schedule/edit'),
          headers: _headers,
          body: jsonEncode({
            'current_item': currentItem,
            'request': trimmed,
          }),
        ));

    if (resp.statusCode != 200) {
      throw Exception(_safeError(resp, '일정 수정'));
    }

    final parsed = jsonDecode(resp.body);
    if (parsed is! Map<String, dynamic>) {
      throw Exception('일정 수정: 응답 형식이 올바르지 않습니다.');
    }
    return parsed;
  }

  // ── 3. TTS ──
  static Future<List<int>> synthesizeTts(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) {
      throw Exception('읽어줄 텍스트가 없습니다.');
    }

    final resp = await _retryRequest(() => http.post(
          Uri.parse('$_baseUrl/api/tts'),
          headers: _headers,
          body: jsonEncode({'text': trimmed}),
        ));

    if (resp.statusCode != 200) {
      throw Exception(_safeError(resp, 'TTS'));
    }
    return resp.bodyBytes.toList();
  }

  // ── 4. YouTube Search ──
  static Future<List<Map<String, String>>> searchYouTube(
    String query, {
    int maxResults = 4,
  }) async {
    final trimmed = query.trim();
    if (trimmed.isEmpty) return [];

    final uri = Uri.parse('$_baseUrl/api/youtube/search').replace(
      queryParameters: {
        'q': trimmed,
        'maxResults': maxResults.clamp(1, 10).toString(),
      },
    );

    final resp = await _retryRequest(
        () => http.get(uri, headers: _headers));

    if (resp.statusCode != 200) {
      throw Exception(_safeError(resp, 'YouTube'));
    }

    final items = jsonDecode(resp.body) as List<dynamic>;
    return items.map((item) {
      final m = item as Map<String, dynamic>;
      return {
        'title': m['title']?.toString() ?? '',
        'thumbnail': m['thumbnail']?.toString() ?? '',
        'url': m['url']?.toString() ?? '',
        'videoId': m['videoId']?.toString() ?? '',
      };
    }).toList();
  }

  // ── 5. Google Image Search ──
  static Future<List<Map<String, String>>> searchImages(
    String query, {
    int maxResults = 4,
  }) async {
    final trimmed = query.trim();
    if (trimmed.isEmpty) return [];

    final uri = Uri.parse('$_baseUrl/api/image/search').replace(
      queryParameters: {
        'q': trimmed,
        'maxResults': maxResults.clamp(1, 10).toString(),
      },
    );

    final resp = await _retryRequest(
        () => http.get(uri, headers: _headers));

    if (resp.statusCode != 200) {
      throw Exception(_safeError(resp, 'Google Image'));
    }

    final items = jsonDecode(resp.body) as List<dynamic>;
    return items.map((item) {
      final m = item as Map<String, dynamic>;
      return {
        'link': m['link']?.toString() ?? '',
        'thumbnail': m['thumbnail']?.toString() ?? '',
        'title': m['title']?.toString() ?? '',
      };
    }).toList();
  }

  // ── 6. Save Schedule to Server ──
  static Future<void> saveScheduleToServer(
    String userId,
    String date,
    List<dynamic> schedule,
  ) async {
    final resp = await _retryRequest(() => http.post(
          Uri.parse('$_baseUrl/api/schedule/save'),
          headers: _headers,
          body: jsonEncode({
            'user_id': userId,
            'date': date,
            'schedule': schedule,
          }),
        ));

    if (resp.statusCode != 200) {
      throw Exception(_safeError(resp, '일정 저장'));
    }
  }

  // ── 7. Load Schedule from Server ──
  static Future<Map<String, dynamic>?> loadScheduleFromServer(
    String userId, {
    String? date,
  }) async {
    final params = {'user_id': userId};
    if (date != null && date.isNotEmpty) {
      params['date'] = date;
    }

    final uri = Uri.parse('$_baseUrl/api/schedule/load').replace(
      queryParameters: params,
    );

    try {
      final resp = await _retryRequest(
          () => http.get(uri, headers: _headers));

      if (resp.statusCode == 404) return null;
      if (resp.statusCode != 200) {
        throw Exception(_safeError(resp, '일정 불러오기'));
      }

      return jsonDecode(resp.body) as Map<String, dynamic>;
    } on NetworkException {
      return null; // 오프라인이면 null 반환 (로컬 폴백 사용)
    }
  }
}

/// 네트워크 오류 전용 예외 (오프라인 폴백 판별용)
class NetworkException implements Exception {
  final String message;
  const NetworkException(this.message);

  @override
  String toString() => message;
}
