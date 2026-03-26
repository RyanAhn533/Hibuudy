import 'dart:convert';
import 'package:http/http.dart' as http;

/// 날씨 서비스 — wttr.in 무료 API 사용 (키 불필요)
class WeatherService {
  static const String _baseUrl = 'https://wttr.in';
  static const String _defaultCity = 'Seoul';

  /// 현재 날씨 가져오기
  /// 반환: {'temp': double, 'description': String, 'condition': String, 'humidity': String, 'feelsLike': double}
  static Future<Map<String, dynamic>> getCurrentWeather({String? city}) async {
    final location = city ?? _defaultCity;
    final url = '$_baseUrl/$location?format=j1&lang=ko';

    final response = await http
        .get(Uri.parse(url), headers: {'Accept': 'application/json'})
        .timeout(const Duration(seconds: 10));

    if (response.statusCode != 200) {
      throw Exception('날씨 정보를 가져올 수 없어요 (${response.statusCode})');
    }

    final data = jsonDecode(response.body);
    final current = data['current_condition'][0];

    final temp = double.tryParse(current['temp_C'] ?? '0') ?? 0.0;
    final feelsLike =
        double.tryParse(current['FeelsLikeC'] ?? '0') ?? 0.0;
    final humidity = current['humidity'] ?? '';
    // 한국어 설명 (wttr.in lang=ko 지원)
    final description =
        (current['lang_ko'] != null && (current['lang_ko'] as List).isNotEmpty)
            ? current['lang_ko'][0]['value'] as String
            : current['weatherDesc'][0]['value'] as String;
    final condition = current['weatherCode'] ?? '0';

    return {
      'temp': temp,
      'feelsLike': feelsLike,
      'humidity': humidity,
      'description': description,
      'condition': condition,
    };
  }

  /// 온도 기반 옷차림 추천 (한국어)
  static String getClothingAdvice(double temp) {
    if (temp <= -10) {
      return '많이 추워요! 패딩, 목도리, 장갑 꼭 챙기세요.';
    } else if (temp <= 0) {
      return '아주 추워요. 두꺼운 겨울옷 입으세요.';
    } else if (temp <= 5) {
      return '추워요. 코트나 패딩을 입으세요.';
    } else if (temp <= 10) {
      return '쌀쌀해요. 자켓이나 가디건을 챙기세요.';
    } else if (temp <= 15) {
      return '선선해요. 긴팔에 얇은 겉옷이 좋아요.';
    } else if (temp <= 20) {
      return '활동하기 좋은 날씨예요. 긴팔이면 딱이에요.';
    } else if (temp <= 25) {
      return '따뜻해요. 반팔이나 얇은 긴팔이 좋아요.';
    } else if (temp <= 30) {
      return '더워요. 시원한 반팔, 반바지 입으세요.';
    } else {
      return '많이 더워요! 가장 시원한 옷을 입고 물 많이 마시세요.';
    }
  }

  /// 날씨 코드를 이모지로 변환
  static String getWeatherEmoji(String condition) {
    final code = int.tryParse(condition) ?? 0;

    // wttr.in weather codes
    if (code == 113) return '☀️'; // 맑음
    if (code == 116) return '⛅'; // 구름 조금
    if (code == 119 || code == 122) return '☁️'; // 흐림
    if (code == 143 || code == 248 || code == 260) return '🌫️'; // 안개
    if ([176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 353, 356, 359]
        .contains(code)) {
      return '🌧️'; // 비
    }
    if ([179, 182, 185, 227, 230, 320, 323, 326, 329, 332, 335, 338, 350, 362,
            365, 368, 371, 374, 377]
        .contains(code)) {
      return '🌨️'; // 눈
    }
    if ([200, 386, 389, 392, 395].contains(code)) return '⛈️'; // 천둥

    return '🌤️'; // 기본
  }
}
