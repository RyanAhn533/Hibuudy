import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/database_service.dart';
import '../services/tts_service.dart';
import '../widgets/haru_bottom_bar.dart';
import '../widgets/haru_feedback.dart';
import '../widgets/sos_button.dart';

/// ══════════════════════════════════════════════════════════
/// HelpScreen — 「도움」 탭 (P5 + P11)
/// 1탭 3버튼 (전화 / 문자 / 도움 요청) + 감정 보드 3표정 + 기다리는 중 카드
/// - 전화 사용이 어려운 73.7% (KODDI) → 확인 없이 즉시 실행
/// - Choiceworks 감정·대기 보드 패턴
/// - 카피: 사용자 화면 "~요/~보세요/~님" 클러스터 금지
/// ══════════════════════════════════════════════════════════
class HelpScreen extends StatefulWidget {
  const HelpScreen({super.key});

  @override
  State<HelpScreen> createState() => _HelpScreenState();
}

class _HelpScreenState extends State<HelpScreen> {
  String? _phone;
  String? _contactName;
  String? _mood; // 'good' | 'ok' | 'hard'
  bool _waiting = false;

  static const _kMoodLog = 'harumate_mood_log';

  @override
  void initState() {
    super.initState();
    _loadContact();
  }

  Future<void> _loadContact() async {
    try {
      final contacts = await DatabaseService.getEmergencyContacts();
      if (contacts.isNotEmpty && mounted) {
        setState(() {
          _phone = contacts.first['phone'] as String?;
          _contactName = contacts.first['name'] as String?;
        });
      }
    } catch (_) {
      // 연락처 없으면 119 폴백 (SosButton과 동일)
    }
  }

  Future<void> _launch(Uri uri, String failMsg) async {
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else if (mounted) {
      HaruFeedback.show(context, failMsg, error: true);
    }
  }

  Future<void> _callContact() async {
    DatabaseService.logHelp(source: 'call').catchError((_) {});
    final number = _phone ?? '119';
    await _launch(Uri.parse('tel:$number'), '$number 전화 연결이 안 됨');
  }

  Future<void> _smsContact() async {
    final number = _phone;
    if (number == null) {
      HaruFeedback.show(context, '문자 보낼 사람이 아직 없음', error: true);
      return;
    }
    DatabaseService.logHelp(source: 'sms').catchError((_) {});
    final uri = Uri(
      scheme: 'sms',
      path: number,
      queryParameters: {'body': '도와주세요. 지금 연락 부탁해요.'},
    );
    await _launch(uri, '문자 앱을 열 수 없음');
  }

  Future<void> _pickMood(String mood) async {
    setState(() {
      _mood = mood;
      _waiting = mood == 'hard';
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final log = prefs.getStringList(_kMoodLog) ?? <String>[];
      log.add('${DateTime.now().toIso8601String()}|$mood');
      // 최근 200건만 보존
      final trimmed = log.length > 200 ? log.sublist(log.length - 200) : log;
      await prefs.setStringList(_kMoodLog, trimmed);
    } catch (_) {}

    switch (mood) {
      case 'good':
        await TtsService.speak('좋아. 오늘도 잘 하고 있어.');
        break;
      case 'ok':
        await TtsService.speak('그래. 천천히 해도 괜찮아.');
        break;
      case 'hard':
        await TtsService.speak('힘들구나. 옆에 있을게. 전화가 필요하면 위 버튼을 눌러.');
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    // 이름 있으면 "○○한테 전화", 번호만 있으면 "가족한테 전화", 없으면 "119에 전화"
    final callLabel = _contactName != null
        ? '$_contactName한테 전화'
        : (_phone != null ? '가족한테 전화' : '119에 전화');

    return Scaffold(
      backgroundColor: HaruTokensV2.surfaceBase,
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Symbols.support, size: 24, color: HaruTokensV2.brandWarm, fill: 1),
            SizedBox(width: HaruTokens.space2),
            Text('도움'),
          ],
        ),
        automaticallyImplyLeading: false,
      ),
      bottomNavigationBar: HaruBottomBar.maybe(context),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(HaruTokens.space4),
          children: [
            // ─── 1탭 3버튼 ───
            _BigAction(
              icon: Symbols.call,
              label: callLabel,
              color: HaruTokensV2.brandWarm,
              onTap: _callContact,
            ),
            const SizedBox(height: HaruTokens.space3),
            _BigAction(
              icon: Symbols.sms,
              label: '문자 보내기',
              color: HaruTokensV2.actBodyMain,
              onTap: _smsContact,
            ),
            const SizedBox(height: HaruTokens.space3),
            _BigAction(
              icon: Symbols.sos,
              label: '도움 요청',
              color: HaruTokensV2.danger,
              onTap: () => SosButton.call(context),
            ),

            const SizedBox(height: HaruTokens.space6),

            // ─── 감정 보드 ───
            Text('지금 기분', style: HaruText.h3.copyWith(color: HaruTokensV2.inkPrimary)),
            const SizedBox(height: HaruTokens.space3),
            Row(
              children: [
                Expanded(
                  child: _MoodButton(
                    icon: Symbols.sentiment_satisfied,
                    label: '좋아',
                    color: HaruTokensV2.success,
                    selected: _mood == 'good',
                    onTap: () => _pickMood('good'),
                  ),
                ),
                const SizedBox(width: HaruTokens.space3),
                Expanded(
                  child: _MoodButton(
                    icon: Symbols.sentiment_neutral,
                    label: '보통',
                    color: HaruTokensV2.warn,
                    selected: _mood == 'ok',
                    onTap: () => _pickMood('ok'),
                  ),
                ),
                const SizedBox(width: HaruTokens.space3),
                Expanded(
                  child: _MoodButton(
                    icon: Symbols.sentiment_dissatisfied,
                    label: '힘들어',
                    color: HaruTokensV2.danger,
                    selected: _mood == 'hard',
                    onTap: () => _pickMood('hard'),
                  ),
                ),
              ],
            ),

            // ─── 기다리는 중 카드 (Choiceworks waiting board) ───
            if (_waiting) ...[
              const SizedBox(height: HaruTokens.space5),
              Container(
                padding: const EdgeInsets.all(HaruTokens.space5),
                decoration: BoxDecoration(
                  color: HaruTokensV2.actRestSoft,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
                  border: Border.all(color: HaruTokensV2.actRestMain, width: 2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Symbols.self_improvement,
                            size: 32, color: HaruTokensV2.actRestMain, fill: 1),
                        const SizedBox(width: HaruTokens.space3),
                        Expanded(
                          child: Text(
                            '잠깐 쉬어도 괜찮아',
                            style: HaruText.h2.copyWith(color: HaruTokensV2.inkPrimary),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: HaruTokens.space3),
                    Text(
                      '숨을 천천히 세 번. 그다음 다시 해도 늦지 않아.',
                      style: HaruText.body.copyWith(color: HaruTokensV2.inkBody),
                    ),
                    const SizedBox(height: HaruTokens.space4),
                    SizedBox(
                      width: double.infinity,
                      height: HaruTokensV2.comfortTouchTarget,
                      child: OutlinedButton.icon(
                        onPressed: () => TtsService.speak(
                          '천천히 숨을 들이쉬고, 내쉬고. 한 번 더. 잘하고 있어.',
                        ),
                        icon: const Icon(Symbols.volume_up),
                        label: const Text('같이 숨 쉬기'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _BigAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _BigAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: label,
      child: Material(
        color: color,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        child: InkWell(
          borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
          onTap: onTap,
          child: SizedBox(
            height: 96,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: HaruTokens.space5),
              child: Row(
                children: [
                  Icon(icon, size: 40, color: HaruTokensV2.onBrand, fill: 1),
                  const SizedBox(width: HaruTokens.space4),
                  Expanded(
                    child: Text(
                      label,
                      style: HaruText.h2.copyWith(
                        color: HaruTokensV2.onBrand,
                        fontWeight: FontWeight.w800,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _MoodButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final bool selected;
  final VoidCallback onTap;

  const _MoodButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: selected,
      label: '기분 $label',
      child: Material(
        color: selected ? color.withValues(alpha: 0.15) : HaruTokensV2.surfaceCard,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        child: InkWell(
          borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
          onTap: onTap,
          child: Container(
            height: 104,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
              border: Border.all(
                color: selected ? color : HaruTokensV2.borderSoft,
                width: selected ? 2.5 : 1.5,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 40, color: color, fill: selected ? 1 : 0),
                const SizedBox(height: HaruTokens.space2),
                Text(
                  label,
                  style: HaruText.body.copyWith(
                    color: HaruTokensV2.inkPrimary,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
