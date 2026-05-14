import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';
import '../services/session_service.dart';
import '../services/schedule_storage.dart';
import '../services/database_service.dart';
import 'coordinator_screen.dart';
import 'user_screen.dart';
import 'profile_screen.dart';

/// ══════════════════════════════════════════════════════════
/// HomeCoordinatorScreen — 보호자/교사용 홈 (v1.4「메이트」)
/// HaruTokensV2 적용, 그라데이션 폐기, 진행률 시각 강화 (P2 합의)
/// ══════════════════════════════════════════════════════════
class HomeCoordinatorScreen extends StatefulWidget {
  const HomeCoordinatorScreen({super.key});

  @override
  State<HomeCoordinatorScreen> createState() => _HomeCoordinatorScreenState();
}

class _HomeCoordinatorScreenState extends State<HomeCoordinatorScreen> {
  static const _kHintDismissedKey = 'coord_home_hint_dismissed_v1';

  String _targetName = '담당';
  int _totalCount = 0;
  int _completedCount = 0;
  String? _pairCode;
  bool _hintDismissed = false;

  @override
  void initState() {
    super.initState();
    _load();
    _loadHintState();
  }

  Future<void> _loadHintState() async {
    final prefs = await SharedPreferences.getInstance();
    final dismissed = prefs.getBool(_kHintDismissedKey) ?? false;
    if (mounted) setState(() => _hintDismissed = dismissed);
  }

  Future<void> _dismissHint() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kHintDismissedKey, true);
    if (mounted) setState(() => _hintDismissed = true);
  }

  Future<void> _load() async {
    final name = await SessionService.getUserName();
    final code = await SessionService.getPairCode();
    final schedule = await ScheduleStorage.load();
    int total = 0, done = 0;
    if (schedule != null) {
      total = schedule.items.length;
      final today = DateTime.now().toIso8601String().substring(0, 10);
      try {
        final logs = await DatabaseService.getCompletionLogs(date: today);
        done = logs.where((l) => l['completed'] == 1).length;
      } catch (_) {}
    }
    if (!mounted) return;
    setState(() {
      _targetName = name;
      _totalCount = total;
      _completedCount = done;
      _pairCode = code;
    });
  }

  @override
  Widget build(BuildContext context) {
    final progress = _totalCount > 0 ? _completedCount / _totalCount : 0.0;

    return Scaffold(
      backgroundColor: HaruTokensV2.surfaceBase,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(HaruTokens.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ─── Topbar (단일 솔리드) ───
              Container(
                padding: const EdgeInsets.all(HaruTokens.space4),
                decoration: BoxDecoration(
                  color: HaruTokensV2.brandWarm,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$_targetName 담당',
                      style: HaruText.h3.copyWith(
                        color: HaruTokensV2.onBrand,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: HaruTokens.space1),
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: _pairCode != null
                                ? HaruTokensV2.success
                                : HaruTokensV2.inkDisabled,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          _pairCode != null
                              ? '연결됨 · 코드 $_pairCode'
                              : '아직 연결 안 됨',
                          style: HaruText.small.copyWith(
                            color: HaruTokensV2.onBrand.withValues(alpha: 0.9),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: HaruTokens.space5),

              // ─── 오늘 진행률 (P2: 큰 시각화) ───
              Padding(
                padding: const EdgeInsets.only(left: 4, bottom: 8),
                child: Text('오늘',
                    style: HaruText.tiny.copyWith(
                      color: HaruTokensV2.inkMuted,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                    )),
              ),

              Container(
                padding: const EdgeInsets.all(HaruTokens.space4),
                decoration: BoxDecoration(
                  color: HaruTokensV2.surfaceCard,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
                  border: Border.all(color: HaruTokensV2.borderSoft),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: const BoxDecoration(
                            color: HaruTokensV2.success,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Symbols.check,
                              color: HaruTokensV2.onSuccess, size: 22, fill: 1),
                        ),
                        const SizedBox(width: HaruTokens.space3),
                        Expanded(
                          child: Text(
                            _totalCount > 0
                                ? '$_completedCount / $_totalCount 완료'
                                : '아직 일정 없음',
                            style: HaruText.h3,
                          ),
                        ),
                        if (_totalCount > 0)
                          Text(
                            '${(progress * 100).toInt()}%',
                            style: HaruText.h3.copyWith(
                              color: HaruTokensV2.success,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: HaruTokens.space3),
                    // P2: 진행 바 6px → 12px (큰 시각화)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(HaruTokensV2.radiusSm),
                      child: LinearProgressIndicator(
                        value: progress,
                        minHeight: 12,
                        backgroundColor: HaruTokensV2.surfaceSunken,
                        color: HaruTokensV2.success,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: HaruTokens.space5),

              // ─── 사용 안내 (한 번 끄면 영구) ───
              if (!_hintDismissed) ...[
                Container(
                  padding: const EdgeInsets.all(HaruTokens.space4),
                  decoration: BoxDecoration(
                    color: HaruTokensV2.brandWarmSoft,
                    borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Symbols.lightbulb,
                              color: HaruTokensV2.brandWarm,
                              size: 20,
                              fill: 0),
                          const SizedBox(width: HaruTokens.space2),
                          Text('사용 방법',
                              style: HaruText.small.copyWith(
                                color: HaruTokensV2.brandWarmDeep,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.5,
                              )),
                        ],
                      ),
                      const SizedBox(height: HaruTokens.space2),
                      Text(
                        _totalCount == 0
                            ? '① "일정 만들기"로 오늘 일정을 먼저 만들어요\n② 저장 후 "오늘 일과 시작"으로 당사자 화면을 열어요'
                            : '"오늘 일과 시작"으로 당사자 화면을 열어요\n당사자에게 폰을 건네주세요',
                        style: HaruText.small.copyWith(
                          color: HaruTokensV2.inkBody,
                          height: 1.6,
                        ),
                      ),
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton(
                          onPressed: _dismissHint,
                          style: TextButton.styleFrom(
                            foregroundColor: HaruTokensV2.inkMuted,
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 4),
                            minimumSize: const Size(0, 32),
                          ),
                          child: Text('앞으로 보지 않기',
                              style: HaruText.small.copyWith(
                                color: HaruTokensV2.inkMuted,
                                fontWeight: FontWeight.w600,
                              )),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: HaruTokens.space4),
              ],

              Padding(
                padding: const EdgeInsets.only(left: 4, bottom: 8),
                child: Text('빠른 작업',
                    style: HaruText.tiny.copyWith(
                      color: HaruTokensV2.inkMuted,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                    )),
              ),

              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: HaruTokens.space3,
                crossAxisSpacing: HaruTokens.space3,
                childAspectRatio: 1.4,
                children: [
                  _QuickAction(
                    icon: Symbols.edit_note,
                    label: '일정 만들기',
                    subtitle: '먼저 일정 입력',
                    onTap: () => Navigator.push(context,
                            MaterialPageRoute(builder: (_) => const CoordinatorScreen()))
                        .then((_) => _load()),
                  ),
                  _QuickAction(
                    icon: Symbols.play_circle,
                    label: '오늘 일과 시작',
                    subtitle: '당사자 화면',
                    highlight: _totalCount > 0,
                    onTap: () => Navigator.push(context,
                        MaterialPageRoute(builder: (_) => const UserScreen())),
                  ),
                  _QuickAction(
                    icon: Symbols.monitoring,
                    label: '수행 기록',
                    subtitle: '이번 주 확인',
                    onTap: () => Navigator.push(context,
                        MaterialPageRoute(builder: (_) => const ProfileScreen())),
                  ),
                  _QuickAction(
                    icon: Symbols.settings,
                    label: '내 정보',
                    subtitle: '이름 · 연락처',
                    onTap: () => Navigator.push(context,
                            MaterialPageRoute(builder: (_) => const ProfileScreen()))
                        .then((_) => _load()),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? subtitle;
  final bool highlight;
  final VoidCallback onTap;

  const _QuickAction({
    required this.icon,
    required this.label,
    required this.onTap,
    this.subtitle,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    final bg = highlight ? HaruTokensV2.brandWarm : HaruTokensV2.surfaceCard;
    final fg = highlight ? HaruTokensV2.onBrand : HaruTokensV2.inkPrimary;
    final iconColor =
        highlight ? HaruTokensV2.onBrand : HaruTokensV2.brandWarm;
    final subColor = highlight
        ? HaruTokensV2.onBrand.withValues(alpha: 0.85)
        : HaruTokensV2.inkMuted;
    final borderColor =
        highlight ? HaruTokensV2.brandWarm : HaruTokensV2.borderSoft;

    return Material(
      color: bg,
      borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(HaruTokens.space2),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
            border: Border.all(
              color: borderColor,
              width: highlight ? 2 : 1,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 32, color: iconColor, fill: 1),
              const SizedBox(height: HaruTokens.space1),
              Text(
                label,
                style: HaruText.small.copyWith(
                  fontWeight: FontWeight.w700,
                  color: fg,
                ),
                textAlign: TextAlign.center,
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 2),
                Text(
                  subtitle!,
                  style: HaruText.tiny.copyWith(color: subColor),
                  textAlign: TextAlign.center,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
