import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import '../models/schedule_item.dart';

/// Secure API service with input validation and safe error handling.
class ApiService {
  // ── Key accessors (never log or expose these) ──
  static String get _openaiKey => dotenv.env['OPENAI_API_KEY'] ?? '';
  static String get _googleKey => dotenv.env['GOOGLE_API_KEY'] ?? '';
  static String get _googleCseId => dotenv.env['GOOGLE_CSE_ID'] ?? '';
  static String get _youtubeKey =>
      dotenv.env['YOUTUBE_API_KEY'] ?? dotenv.env['GOOGLE_API_KEY'] ?? '';

  /// Validate that required API key exists before making a request.
  static void _requireKey(String key, String serviceName) {
    if (key.isEmpty) {
      throw Exception('$serviceName API 키가 설정되지 않았습니다. .env 파일을 확인하세요.');
    }
  }

  /// Sanitize user input to prevent prompt injection.
  static String _sanitizeInput(String input, {int maxLength = 2000}) {
    // Trim whitespace
    var sanitized = input.trim();
    // Truncate to max length
    if (sanitized.length > maxLength) {
      sanitized = sanitized.substring(0, maxLength);
    }
    // Remove control characters (keep newlines, tabs)
    sanitized = sanitized.replaceAll(RegExp(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'), '');
    return sanitized;
  }

  /// Safe error message that never exposes API keys or sensitive data.
  static String _safeErrorMessage(http.Response resp, String service) {
    final code = resp.statusCode;
    switch (code) {
      case 401:
        return '$service: 인증 실패 - API 키를 확인하세요.';
      case 403:
        return '$service: 접근 거부 - API 키 권한을 확인하세요.';
      case 429:
        return '$service: 요청 한도 초과 - 잠시 후 다시 시도하세요.';
      case >= 500:
        return '$service: 서버 오류 ($code) - 잠시 후 다시 시도하세요.';
      default:
        return '$service: 요청 실패 ($code)';
    }
  }

  // ── OpenAI Chat Completion (JSON mode) ──
  static Future<Map<String, dynamic>> _callGptJson({
    required String system,
    required String user,
    String model = 'gpt-4.1-mini',
    double temperature = 0.3,
  }) async {
    _requireKey(_openaiKey, 'OpenAI');

    final resp = await http.post(
      Uri.parse('https://api.openai.com/v1/chat/completions'),
      headers: {
        'Authorization': 'Bearer $_openaiKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'model': model,
        'response_format': {'type': 'json_object'},
        'temperature': temperature,
        'messages': [
          {'role': 'system', 'content': system},
          {'role': 'user', 'content': user},
        ],
      }),
    );

    if (resp.statusCode != 200) {
      throw Exception(_safeErrorMessage(resp, 'OpenAI'));
    }

    final data = jsonDecode(resp.body);
    final content = data['choices']?[0]?['message']?['content'] ?? '{}';
    final parsed = jsonDecode(content);
    if (parsed is! Map<String, dynamic>) {
      throw Exception('OpenAI: 응답 형식이 올바르지 않습니다.');
    }
    return parsed;
  }

  // ── Generate Schedule from Text ──
  static Future<List<ScheduleItem>> generateSchedule(String rawText) async {
    final sanitized = _sanitizeInput(rawText);
    if (sanitized.isEmpty) {
      throw Exception('일정 내용을 입력해 주세요.');
    }

    const system = '''너는 발달장애인의 하루 일정을 설계하는 코디네이터 도우미다.
사용자가 입력한 텍스트를 읽고 JSON 일정표를 생성한다.
출력 스키마: { "schedule": [ { "time": "HH:MM", "type": "TYPE", "task": "할 일", "guide_script": ["안내문1","안내문2"] } ] }
type은: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST 중 하나.
guide_script 문장은 20~45자 이내, 존댓말, 1~5문장.
한국어만. JSON만 출력.''';

    final data = await _callGptJson(system: system, user: sanitized);
    final list = data['schedule'] as List<dynamic>? ?? [];
    return list
        .map((e) => ScheduleItem.fromJson(e as Map<String, dynamic>))
        .toList()
      ..sort((a, b) => a.timeMinutes.compareTo(b.timeMinutes));
  }

  // ── Edit a single schedule item via GPT ──
  static Future<Map<String, dynamic>> editScheduleItem(
    Map<String, dynamic> currentItem,
    String request,
  ) async {
    final sanitizedRequest = _sanitizeInput(request, maxLength: 500);
    if (sanitizedRequest.isEmpty) {
      throw Exception('수정 요청을 입력해 주세요.');
    }

    const system = '''너는 일정표를 수정하는 코디네이터 도우미다.
사용자 요청에 따라 time(HH:MM), task, type, guide_script를 수정한다.
반드시 JSON만 출력. 한국어만. 기존 의미를 최대한 유지.
type: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST''';

    final user =
        '현재 항목 JSON:\n${jsonEncode(currentItem)}\n\n수정 요청: $sanitizedRequest';
    return _callGptJson(system: system, user: user);
  }

  // ── TTS (OpenAI) ──
  static Future<List<int>> synthesizeTts(String text) async {
    _requireKey(_openaiKey, 'OpenAI TTS');

    final sanitized = _sanitizeInput(text, maxLength: 4096);
    if (sanitized.isEmpty) {
      throw Exception('읽어줄 텍스트가 없습니다.');
    }

    final resp = await http.post(
      Uri.parse('https://api.openai.com/v1/audio/speech'),
      headers: {
        'Authorization': 'Bearer $_openaiKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'model': 'gpt-4o-mini-tts',
        'voice': 'alloy',
        'input': sanitized,
      }),
    );

    if (resp.statusCode != 200) {
      throw Exception(_safeErrorMessage(resp, 'TTS'));
    }
    return resp.bodyBytes.toList();
  }

  // ── YouTube Search ──
  static Future<List<Map<String, String>>> searchYouTube(
    String query, {
    int maxResults = 4,
  }) async {
    _requireKey(_youtubeKey, 'YouTube');

    final sanitized = _sanitizeInput(query, maxLength: 200);
    if (sanitized.isEmpty) return [];

    // Clamp maxResults for safety
    final safeMax = maxResults.clamp(1, 10);

    final uri = Uri.parse('https://www.googleapis.com/youtube/v3/search').replace(
      queryParameters: {
        'part': 'snippet',
        'q': sanitized,
        'type': 'video',
        'maxResults': safeMax.toString(),
        'key': _youtubeKey,
      },
    );

    final resp = await http.get(uri);
    if (resp.statusCode != 200) {
      throw Exception(_safeErrorMessage(resp, 'YouTube'));
    }

    final data = jsonDecode(resp.body);
    final items = data['items'] as List<dynamic>? ?? [];

    return items.map((item) {
      final snippet = item['snippet'] as Map<String, dynamic>? ?? {};
      final videoId = item['id']?['videoId']?.toString() ?? '';
      return {
        'title': snippet['title']?.toString() ?? '',
        'thumbnail': snippet['thumbnails']?['medium']?['url']?.toString() ?? '',
        'url': 'https://www.youtube.com/watch?v=$videoId',
        'videoId': videoId,
      };
    }).toList();
  }

  // ── Google Image Search ──
  static Future<List<Map<String, String>>> searchImages(
    String query, {
    int maxResults = 4,
  }) async {
    _requireKey(_googleKey, 'Google Image');

    final sanitized = _sanitizeInput(query, maxLength: 200);
    if (sanitized.isEmpty) return [];

    final safeMax = maxResults.clamp(1, 10);

    final uri =
        Uri.parse('https://www.googleapis.com/customsearch/v1').replace(
      queryParameters: {
        'q': sanitized,
        'searchType': 'image',
        'num': safeMax.toString(),
        'key': _googleKey,
        'cx': _googleCseId,
        'safe': 'active', // SafeSearch 활성화
      },
    );

    final resp = await http.get(uri);
    if (resp.statusCode != 200) {
      throw Exception(_safeErrorMessage(resp, 'Google Image'));
    }

    final data = jsonDecode(resp.body);
    final items = data['items'] as List<dynamic>? ?? [];

    return items.map((item) {
      return {
        'link': item['link']?.toString() ?? '',
        'thumbnail': item['image']?['thumbnailLink']?.toString() ?? '',
        'title': item['title']?.toString() ?? '',
      };
    }).toList();
  }
}
