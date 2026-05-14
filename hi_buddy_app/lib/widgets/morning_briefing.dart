import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';
import '../services/weather_service.dart';
import '../services/tts_service.dart';
import '../services/session_service.dart';
import '../services/database_service.dart';

/// ══════════════════════════════════════════════════════════
/// MorningBriefing — 날씨 + 옷차림 + 일정 요약 + 인사 (v1.4「메이트」)
/// HaruTokensV2 적용:
///   - 그라데이션 폐기 (P6 적출)
///   - 날씨/옷 이모지 폐기 → Material Symbols
///   - "이에요/예요/볼까요" 클러스터 검수
///   - actRest 그룹 색 사용 (브리핑은 휴식 그룹)
/// ══════════════════════════════════════════════════════════
class MorningBriefing extends StatefulWidget {
  final int activityCount;

  const MorningBriefing({super.key, this.activityCount = 0});

  @override
  State<MorningBriefing> createState() => _MorningBriefingState();
}

class _MorningBriefingState extends State<MorningBriefing> {
  Map<String, dynamic>? _weather;
  String? _clothingAI;
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
      final name = await SessionService.getUserName();
      final profile = await DatabaseService.getProfile();
      final level = (profile['disability_level'] as String?) ?? 'mild';
      final clothing = await WeatherService.getClothingAdviceAI(
        temp: weather['temp'] as double,
        description: (weather['description'] as String?) ?? '',
        name: name == '사용자' ? '' : name,
        disabilityLevel: level,
      );
      if (mounted) {
        setState(() {
          _weather = weather;
          _clothingAI = clothing;
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
      final clothing = _clothingAI ?? WeatherService.getClothingAdvice(temp);
      briefing += ' 지금 날씨는 $desc, ${temp.round()}도. $clothing';
    }

    if (widget.activityCount > 0) {
      briefing += ' 오늘 활동 ${widget.activityCount}개.';
    }

    TtsService.speak(briefing);
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return '좋은 아침';
    if (hour < 18) return '좋은 오후';
    return '좋은 저녁';
  }

  /// condition string (clear/sunny/cloudy/rain/snow 등) → Material Symbols
  IconData _weatherIcon(String condition) {
    final c = condition.toLowerCase();
    if (c.contains('clear') || c.contains('sun')) return Symbols.wb_sunny;
    if (c.contains('cloud')) return Symbols.cloud;
    if (c.contains('rain') || c.contains('drizzle')) return Symbols.rainy;
    if (c.contains('snow')) return Symbols.weather_snowy;
    if (c.contains('thunder')) return Symbols.thunderstorm;
    if (c.contains('fog') || c.contains('mist')) return Symbols.foggy;
    return Symbols.cloud;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(HaruTokens.space5),
      decoration: BoxDecoration(
        color: HaruTokensV2.actRestSoft,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        border: Border.all(color: HaruTokensV2.borderSoft),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ─── 인사 ───
          Text(
            _getGreeting(),
            style: HaruText.h1.copyWith(color: HaruTokensV2.inkPrimary),
          ),
          const SizedBox(height: HaruTokens.space1),
          Text(
            DateFormat('M월 d일 (E)', 'ko').format(DateTime.now()),
            style: HaruText.body.copyWith(color: HaruTokensV2.inkBody),
          ),

          // ─── 날씨 섹션 ───
          if (_loading) ...[
            const SizedBox(height: HaruTokens.space4),
            Row(
              children: [
                const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                const SizedBox(width: HaruTokens.space3),
                Text('날씨 정보 가져오는 중',
                    style: HaruText.body.copyWith(color: HaruTokensV2.inkMuted)),
              ],
            ),
          ] else if (_weather != null) ...[
            const SizedBox(height: HaruTokens.space4),
            _buildWeatherSection(),
          ],

          // ─── 일정 요약 ───
          if (widget.activityCount > 0) ...[
            const SizedBox(height: HaruTokens.space3),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: HaruTokens.space4,
                vertical: HaruTokens.space2 + 2,
              ),
              decoration: BoxDecoration(
                color: HaruTokensV2.successSoft,
                borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Symbols.event_note,
                      color: HaruTokensV2.success, size: 22, fill: 0),
                  const SizedBox(width: HaruTokens.space2),
                  Text(
                    '오늘 활동 ${widget.activityCount}개',
                    style: HaruText.h3.copyWith(color: HaruTokensV2.success),
                  ),
                ],
              ),
            ),
          ],

          // ─── TTS 다시 듣기 ───
          const SizedBox(height: HaruTokens.space3),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () {
                _hasSpokeOnce = false;
                _speakBriefing();
              },
              icon: const Icon(Symbols.volume_up, size: 24),
              label: Text('다시 듣기', style: HaruText.h3),
              style: OutlinedButton.styleFrom(
                foregroundColor: HaruTokensV2.inkPrimary,
                side: const BorderSide(color: HaruTokensV2.borderSoft),
                padding: const EdgeInsets.symmetric(vertical: HaruTokens.space4),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
                ),
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
    final clothing = _clothingAI ?? WeatherService.getClothingAdvice(temp);

    return Container(
      padding: const EdgeInsets.all(HaruTokens.space4),
      decoration: BoxDecoration(
        color: HaruTokensV2.surfaceCard,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
        border: Border.all(color: HaruTokensV2.borderSoft),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 날씨 + 온도
          Row(
            children: [
              Icon(_weatherIcon(condition),
                  size: 40, color: HaruTokensV2.actRestMain, fill: 1),
              const SizedBox(width: HaruTokens.space3),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${temp.round()}°C',
                    style: HaruText.h1.copyWith(color: HaruTokensV2.inkPrimary),
                  ),
                  Text(
                    '$desc · 체감 ${feelsLike.round()}°C',
                    style: HaruText.body.copyWith(color: HaruTokensV2.inkBody),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: HaruTokens.space3),
          // 옷차림 추천
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(HaruTokens.space3),
            decoration: BoxDecoration(
              color: HaruTokensV2.warnSoft,
              borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
            ),
            child: Row(
              children: [
                Icon(Symbols.checkroom,
                    size: 22, color: HaruTokensV2.warn, fill: 0),
                const SizedBox(width: HaruTokens.space2),
                Expanded(
                  child: Text(
                    clothing,
                    style: HaruText.body.copyWith(
                      color: HaruTokensV2.inkPrimary,
                      fontWeight: FontWeight.w600,
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
