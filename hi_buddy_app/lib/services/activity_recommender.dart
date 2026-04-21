import 'package:http/http.dart' as http;
import 'dart:convert';

/// ══════════════════════════════════════════════════════════
/// ActivityRecommender — 활동별 유튜브 자동 추천
/// v3.1: 현재 활동 + 장애 수준 기반 맞춤 영상 검색
/// ══════════════════════════════════════════════════════════
class ActivityRecommender {
  static const String _baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://hibuudy.onrender.com',
  );

  /// 활동 타입 + 태스크 + 장애 수준 → 검색 쿼리 생성
  static String _buildQuery(String activityType, String task, String disabilityLevel) {
    // 기본 쿼리: 태스크 텍스트
    String q = task;

    // 활동 타입별 키워드 강화
    final typeKeywords = {
      'COOKING': '쉬운 레시피',
      'MEAL': '집밥',
      'HEALTH': '홈트레이닝',
      'CLOTHING': '옷 입기',
      'LEISURE': '일상 브이로그',
      'MORNING_BRIEFING': '아침 루틴',
      'NIGHT_WRAPUP': '저녁 루틴',
      'REST': '힐링 음악',
      'ROUTINE': '위생 습관',
    };
    final typeKw = typeKeywords[activityType.toUpperCase()] ?? '';
    if (typeKw.isNotEmpty) q = '$q $typeKw';

    // 장애 수준별 키워드 보정
    switch (disabilityLevel) {
      case 'moderate':
        q = '$q 쉽게 천천히';
        break;
      case 'severe':
        q = '$q 짧은 시각';
        break;
      case 'mild':
      default:
        break;
    }

    return q;
  }

  /// 맞춤 영상 3개 가져오기
  static Future<List<Map<String, String>>> recommend({
    required String activityType,
    required String task,
    String disabilityLevel = 'mild',
    int maxResults = 3,
  }) async {
    final query = _buildQuery(activityType, task, disabilityLevel);
    final uri = Uri.parse('$_baseUrl/api/youtube/search').replace(
      queryParameters: {
        'q': query,
        'maxResults': maxResults.toString(),
      },
    );

    try {
      final resp = await http.get(uri).timeout(const Duration(seconds: 15));
      if (resp.statusCode != 200) return [];

      final data = jsonDecode(utf8.decode(resp.bodyBytes)) as List;
      return data.map((item) {
        final m = item as Map<String, dynamic>;
        return {
          'title': (m['title'] ?? '') as String,
          'thumbnail': (m['thumbnail'] ?? '') as String,
          'url': (m['url'] ?? '') as String,
          'videoId': (m['videoId'] ?? '') as String,
        };
      }).toList();
    } catch (_) {
      return [];
    }
  }
}
