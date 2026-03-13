import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import '../models/schedule_item.dart';

class ApiService {
  static String get _openaiKey => dotenv.env['OPENAI_API_KEY'] ?? '';
  static String get _googleKey => dotenv.env['GOOGLE_API_KEY'] ?? '';
  static String get _googleCseId => dotenv.env['GOOGLE_CSE_ID'] ?? '';
  static String get _youtubeKey =>
      dotenv.env['YOUTUBE_API_KEY'] ?? dotenv.env['GOOGLE_API_KEY'] ?? '';

  // ── OpenAI Chat Completion (JSON mode) ──
  static Future<Map<String, dynamic>> _callGptJson({
    required String system,
    required String user,
    String model = 'gpt-4.1-mini',
    double temperature = 0.3,
  }) async {
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
      throw Exception('OpenAI API error: ${resp.statusCode} ${resp.body}');
    }

    final data = jsonDecode(resp.body);
    final content = data['choices'][0]['message']['content'] ?? '{}';
    return jsonDecode(content) as Map<String, dynamic>;
  }

  // ── Generate Schedule from Text ──
  static Future<List<ScheduleItem>> generateSchedule(String rawText) async {
    const system = '''너는 발달장애인의 하루 일정을 설계하는 코디네이터 도우미다.
사용자가 입력한 텍스트를 읽고 JSON 일정표를 생성한다.
출력 스키마: { "schedule": [ { "time": "HH:MM", "type": "TYPE", "task": "할 일", "guide_script": ["안내문1","안내문2"] } ] }
type은: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST 중 하나.
guide_script 문장은 20~45자 이내, 존댓말, 1~5문장.
한국어만. JSON만 출력.''';

    final data = await _callGptJson(system: system, user: rawText);
    final list = data['schedule'] as List<dynamic>? ?? [];
    return list.map((e) => ScheduleItem.fromJson(e as Map<String, dynamic>)).toList()
      ..sort((a, b) => a.timeMinutes.compareTo(b.timeMinutes));
  }

  // ── Edit a single schedule item via GPT ──
  static Future<Map<String, dynamic>> editScheduleItem(
    Map<String, dynamic> currentItem,
    String request,
  ) async {
    const system = '''너는 일정표를 수정하는 코디네이터 도우미다.
사용자 요청에 따라 time(HH:MM), task, type, guide_script를 수정한다.
반드시 JSON만 출력. 한국어만. 기존 의미를 최대한 유지.
type: MORNING_BRIEFING, NIGHT_WRAPUP, GENERAL, ROUTINE, COOKING, MEAL, HEALTH, CLOTHING, LEISURE, REST''';

    final user =
        '현재 항목 JSON:\n${jsonEncode(currentItem)}\n\n수정 요청: $request';
    return _callGptJson(system: system, user: user);
  }

  // ── TTS (OpenAI) ──
  static Future<List<int>> synthesizeTts(String text) async {
    final resp = await http.post(
      Uri.parse('https://api.openai.com/v1/audio/speech'),
      headers: {
        'Authorization': 'Bearer $_openaiKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'model': 'gpt-4o-mini-tts',
        'voice': 'alloy',
        'input': text,
      }),
    );

    if (resp.statusCode != 200) {
      throw Exception('TTS API error: ${resp.statusCode}');
    }
    return resp.bodyBytes.toList();
  }

  // ── YouTube Search ──
  static Future<List<Map<String, String>>> searchYouTube(
    String query, {
    int maxResults = 4,
  }) async {
    final uri = Uri.parse('https://www.googleapis.com/youtube/v3/search').replace(
      queryParameters: {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': maxResults.toString(),
        'key': _youtubeKey,
      },
    );

    final resp = await http.get(uri);
    if (resp.statusCode != 200) {
      throw Exception('YouTube API error: ${resp.statusCode}');
    }

    final data = jsonDecode(resp.body);
    final items = data['items'] as List<dynamic>? ?? [];

    return items.map((item) {
      final snippet = item['snippet'] as Map<String, dynamic>;
      final videoId = item['id']['videoId'] ?? '';
      return {
        'title': snippet['title']?.toString() ?? '',
        'thumbnail': snippet['thumbnails']?['medium']?['url']?.toString() ?? '',
        'url': 'https://www.youtube.com/watch?v=$videoId',
        'videoId': videoId.toString(),
      };
    }).toList();
  }

  // ── Google Image Search ──
  static Future<List<Map<String, String>>> searchImages(
    String query, {
    int maxResults = 4,
  }) async {
    final uri =
        Uri.parse('https://www.googleapis.com/customsearch/v1').replace(
      queryParameters: {
        'q': query,
        'searchType': 'image',
        'num': maxResults.toString(),
        'key': _googleKey,
        'cx': _googleCseId,
      },
    );

    final resp = await http.get(uri);
    if (resp.statusCode != 200) {
      throw Exception('Image Search API error: ${resp.statusCode}');
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
