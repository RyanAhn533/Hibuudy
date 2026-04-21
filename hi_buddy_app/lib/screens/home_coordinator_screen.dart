import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
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
  String _targetName = '담당';
  int _totalCount = 0;
  int _completedCount = 0;
  String? _pairCode;

  @override
  void initState() {
    super.initState();
    _load();
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
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CoordinatorScreen())).then((_) => _load()),
                  ),
                  _QuickAction(
                    icon: Symbols.play_circle,
                    label: '미리보기',
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const UserScreen())),
                  ),
                  _QuickAction(
                    icon: Symbols.monitoring,
                    label: '수행 기록',
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
                  ),
                  _QuickAction(
                    icon: Symbols.settings,
                    label: '프로필',
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
  final VoidCallback onTap;
  const _QuickAction({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: HaruTokens.white,
      borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
            border: Border.all(color: HaruTokens.n200),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 32, color: HaruTokens.primary, fill: 1),
              const SizedBox(height: 8),
              Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: HaruTokens.n900)),
            ],
          ),
        ),
      ),
    );
  }
}
