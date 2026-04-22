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
/// HomeCoordinatorScreen — 보호자/교사용 홈
/// Design: Figma Frame 13 (UR4JMkCsmhZgNmtvznzvv3)
/// 기능: 오늘 진행상황 + 4개 빠른 작업
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
      backgroundColor: HaruTokens.n50,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Topbar
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [HaruTokens.primary, Color(0xFF6B8EFF)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                ),
                child: Column(
                  children: [
                    Text(
                      '$_targetName 담당',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: HaruTokens.white),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 8, height: 8,
                          decoration: BoxDecoration(
                            color: _pairCode != null ? HaruTokens.success : HaruTokens.n400,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          _pairCode != null ? '연결됨 · 코드 $_pairCode' : '아직 연결 안 됨',
                          style: TextStyle(fontSize: 12, color: HaruTokens.white.withValues(alpha: 0.9)),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Section label
              const Padding(
                padding: EdgeInsets.only(left: 4, bottom: 8),
                child: Text(
                  '오늘',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: HaruTokens.n400, letterSpacing: 1),
                ),
              ),

              // Progress card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: HaruTokens.white,
                  borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                  border: Border.all(color: HaruTokens.n200),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 44, height: 44,
                      decoration: const BoxDecoration(color: HaruTokens.success, shape: BoxShape.circle),
                      child: const Icon(Symbols.check, color: HaruTokens.white, size: 22, fill: 1),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _totalCount > 0
                                ? '$_completedCount / $_totalCount 완료'
                                : '아직 일정 없음',
                            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                          ),
                          const SizedBox(height: 6),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(3),
                            child: LinearProgressIndicator(
                              value: progress,
                              minHeight: 6,
                              backgroundColor: HaruTokens.n200,
                              color: HaruTokens.success,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // 사용 안내 — 한 번 끄면 영구 숨김 (다른 앱들처럼 "앞으로 보지 않기")
              if (!_hintDismissed) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: HaruTokens.primarySoft,
                    borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Symbols.lightbulb, color: HaruTokens.primary, size: 22, fill: 1),
                          const SizedBox(width: 8),
                          const Text(
                            '사용 방법',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w800,
                              color: HaruTokens.primary,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _totalCount == 0
                            ? '① "일정 만들기"로 오늘 일정을 먼저 만드세요\n② 저장 후 "오늘 하루 시작"을 누르면 당사자 화면이 열려요'
                            : '"오늘 하루 시작"을 누르면 당사자 화면이 열려요\n당사자에게 폰을 건네주세요',
                        style: const TextStyle(
                          fontSize: 13,
                          color: HaruTokens.n700,
                          height: 1.6,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton(
                          onPressed: _dismissHint,
                          style: TextButton.styleFrom(
                            foregroundColor: HaruTokens.n400,
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            minimumSize: const Size(0, 32),
                          ),
                          child: const Text(
                            '앞으로 보지 않기',
                            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              const Padding(
                padding: EdgeInsets.only(left: 4, bottom: 8),
                child: Text(
                  '빠른 작업',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: HaruTokens.n400, letterSpacing: 1),
                ),
              ),

              // 2x2 grid
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 10,
                crossAxisSpacing: 10,
                childAspectRatio: 1.4,
                children: [
                  _QuickAction(
                    icon: Symbols.edit_note,
                    label: '일정 만들기',
                    subtitle: '① 먼저 일정 입력',
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CoordinatorScreen())).then((_) => _load()),
                  ),
                  _QuickAction(
                    icon: Symbols.play_circle,
                    label: '오늘 하루 열기',
                    subtitle: '② 당사자 화면',
                    highlight: _totalCount > 0,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const UserScreen())),
                  ),
                  _QuickAction(
                    icon: Symbols.monitoring,
                    label: '수행 기록',
                    subtitle: '이번 주 확인',
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
                  ),
                  _QuickAction(
                    icon: Symbols.settings,
                    label: '프로필',
                    subtitle: '이름 · 연락처',
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())).then((_) => _load()),
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
    final bg = highlight ? HaruTokens.primary : HaruTokens.white;
    final fg = highlight ? HaruTokens.white : HaruTokens.n900;
    final iconColor = highlight ? HaruTokens.white : HaruTokens.primary;
    final subColor = highlight
        ? Colors.white.withValues(alpha: 0.8)
        : HaruTokens.n400;

    return Material(
      color: bg,
      borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
            border: Border.all(
              color: highlight ? HaruTokens.primary : HaruTokens.n200,
              width: highlight ? 2 : 1,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 32, color: iconColor, fill: 1),
              const SizedBox(height: 6),
              Text(
                label,
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: fg),
                textAlign: TextAlign.center,
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 2),
                Text(
                  subtitle!,
                  style: TextStyle(fontSize: 10, color: subColor, fontWeight: FontWeight.w500),
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
