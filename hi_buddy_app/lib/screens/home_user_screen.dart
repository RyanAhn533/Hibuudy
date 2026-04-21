import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';
import '../services/session_service.dart';
import '../services/schedule_storage.dart';
import '../models/schedule_item.dart';
import '../widgets/sos_button.dart';
import 'user_screen.dart';
import 'agent_screen.dart';

/// ══════════════════════════════════════════════════════════
/// HomeUserScreen — 당사자용 홈
/// Design: Figma Frame 05 (UR4JMkCsmhZgNmtvznzvv3)
/// 유진 피드백: CTA 2개만 · 큰 버튼 · 현재 활동 미리보기
/// ══════════════════════════════════════════════════════════
class HomeUserScreen extends StatefulWidget {
  const HomeUserScreen({super.key});

  @override
  State<HomeUserScreen> createState() => _HomeUserScreenState();
}

class _HomeUserScreenState extends State<HomeUserScreen> {
  String _name = '사용자';
  ScheduleItem? _currentActivity;

  @override
  void initState() {
    super.initState();
    _loadSession();
  }

  Future<void> _loadSession() async {
    final name = await SessionService.getUserName();
    final schedule = await ScheduleStorage.load();
    ScheduleItem? current;
    if (schedule != null && schedule.items.isNotEmpty) {
      final now = DateTime.now();
      final nowMin = now.hour * 60 + now.minute;
      for (final item in schedule.items) {
        if (item.timeMinutes <= nowMin) {
          current = item;
        }
      }
      current ??= schedule.items.first;
    }
    if (!mounted) return;
    setState(() {
      _name = name;
      _currentActivity = current;
    });
  }

  String _koreanDayName() {
    const days = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'];
    return days[DateTime.now().weekday - 1];
  }

  @override
  Widget build(BuildContext context) {
    final timeStr = DateFormat('a h시 m분', 'ko').format(DateTime.now());

    return Scaffold(
      backgroundColor: HaruTokens.n50,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Topbar
              Container(
                padding: const EdgeInsets.all(18),
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
                      '안녕하세요, $_name님',
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: HaruTokens.white),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_koreanDayName()}, $timeStr',
                      style: TextStyle(fontSize: 12, color: HaruTokens.white.withValues(alpha: 0.85)),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Hero — 현재 활동 미리보기
              if (_currentActivity != null)
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: HaruTokens.primarySoft,
                    borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                    border: Border.all(color: HaruTokens.primary),
                  ),
                  child: Column(
                    children: [
                      const Text(
                        '오늘 할 일이 있어요',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: HaruTokens.n900),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '지금은 "${_currentActivity!.task}" 시간이에요',
                        style: const TextStyle(fontSize: 13, color: HaruTokens.n700),
                      ),
                    ],
                  ),
                )
              else
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: HaruTokens.accentSoft,
                    borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                  ),
                  child: const Column(
                    children: [
                      Icon(Symbols.wb_sunny, size: 32, color: HaruTokens.accent, fill: 1),
                      SizedBox(height: 6),
                      Text(
                        '오늘은 자유시간이에요',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: HaruTokens.n900),
                      ),
                      SizedBox(height: 2),
                      Text(
                        '하고 싶은 걸 골라보세요',
                        style: TextStyle(fontSize: 12, color: HaruTokens.n700),
                      ),
                    ],
                  ),
                ),

              const SizedBox(height: 20),

              // Big CTA 1 — 오늘 하루 보기
              Expanded(
                child: _BigCta(
                  label: '오늘 하루 보기',
                  icon: Symbols.play_circle,
                  color: HaruTokens.primary,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const UserScreen())),
                ),
              ),
              const SizedBox(height: 14),

              // Big CTA 2 — 도우미
              Expanded(
                child: _BigCta(
                  label: '도우미에게 물어보기',
                  icon: Symbols.forum,
                  color: HaruTokens.accent,
                  textColor: HaruTokens.n900,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AgentScreen())),
                ),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
      floatingActionButton: SosButton.floatingButton(context),
    );
  }
}

class _BigCta extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final Color textColor;
  final VoidCallback onTap;
  const _BigCta({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
    this.textColor = HaruTokens.white,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(HaruTokens.radiusLg),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokens.radiusLg),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 44, color: textColor, fill: 1),
              const SizedBox(width: 16),
              Text(
                label,
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: textColor, letterSpacing: -0.5),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
