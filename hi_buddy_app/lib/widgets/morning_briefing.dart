import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../services/weather_service.dart';
import '../services/tts_service.dart';

/// 아침 브리핑 위젯 — 날씨 + 옷차림 + 일정 요약 + 인사
class MorningBriefing extends StatefulWidget {
  final int activityCount;

  const MorningBriefing({super.key, this.activityCount = 0});

  @override
  State<MorningBriefing> createState() => _MorningBriefingState();
}

class _MorningBriefingState extends State<MorningBriefing> {
  Map<String, dynamic>? _weather;
  bool _loading = true;
  bool _hasSpokeOnce = false;

  @override
  void initState() {
    super.initState();
    _loadWeather();
  }

  Future<void> _loadWeather() async {
    try {
      final weather = await WeatherService.getCurrentWeather();
      if (mounted) {
        setState(() {
          _weather = weather;
          _loading = false;
        });
        _speakBriefing();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
        });
        _speakBriefing();
      }
    }
  }

  void _speakBriefing() {
    if (_hasSpokeOnce) return;
    _hasSpokeOnce = true;

    final greeting = _getGreeting();
    String briefing = '$greeting.';

    if (_weather != null) {
      final temp = _weather!['temp'] as double;
      final desc = _weather!['description'] as String;
      final clothing = WeatherService.getClothingAdvice(temp);
      briefing += ' 지금 날씨는 $desc, ${temp.round()}도예요. $clothing';
    }

    if (widget.activityCount > 0) {
      briefing += ' 오늘 활동은 ${widget.activityCount}개 있어요.';
    }

    TtsService.speak(briefing);
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return '좋은 아침이에요';
    if (hour < 18) return '좋은 오후예요';
    return '좋은 저녁이에요';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [HiBuddyColors.primaryBg, Color(0xFFDBEAFE)],
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 인사
          Text(
            _getGreeting(),
            style: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w800,
              color: HiBuddyColors.text,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '오늘도 하루메이트랑 함께 해볼까요?  ${DateFormat('yyyy-MM-dd HH:mm').format(DateTime.now())}',
            style: const TextStyle(
              fontSize: 16,
              color: HiBuddyColors.textMuted,
            ),
          ),

          // 날씨 섹션
          if (_loading) ...[
            const SizedBox(height: 16),
            const Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                SizedBox(width: 10),
                Text(
                  '날씨 정보를 가져오고 있어요...',
                  style: TextStyle(fontSize: 16, color: HiBuddyColors.textMuted),
                ),
              ],
            ),
          ] else if (_weather != null) ...[
            const SizedBox(height: 16),
            _buildWeatherSection(),
          ],

          // 일정 요약
          if (widget.activityCount > 0) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: HiBuddyColors.successBg,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.event_note, color: HiBuddyColors.success, size: 22),
                  const SizedBox(width: 8),
                  Text(
                    '오늘 활동 ${widget.activityCount}개',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: HiBuddyColors.success,
                    ),
                  ),
                ],
              ),
            ),
          ],

          // TTS 버튼
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () {
                _hasSpokeOnce = false;
                _speakBriefing();
              },
              icon: const Icon(Icons.volume_up, size: 24),
              label: const Text(
                '다시 듣기',
                style: TextStyle(fontSize: 18),
              ),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeatherSection() {
    final temp = _weather!['temp'] as double;
    final feelsLike = _weather!['feelsLike'] as double;
    final desc = _weather!['description'] as String;
    final condition = _weather!['condition'] as String;
    final emoji = WeatherService.getWeatherEmoji(condition);
    final clothing = WeatherService.getClothingAdvice(temp);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withAlpha(180),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 날씨 + 온도
          Row(
            children: [
              Text(emoji, style: const TextStyle(fontSize: 40)),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${temp.round()}°C',
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w800,
                      color: HiBuddyColors.text,
                    ),
                  ),
                  Text(
                    '$desc  체감 ${feelsLike.round()}°C',
                    style: const TextStyle(
                      fontSize: 16,
                      color: HiBuddyColors.textMuted,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          // 옷차림 추천
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: HiBuddyColors.morningBg,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Text('👔', style: TextStyle(fontSize: 22)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    clothing,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: HiBuddyColors.text,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
