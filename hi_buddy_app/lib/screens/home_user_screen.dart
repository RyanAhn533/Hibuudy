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
/// v3.1 (D2): HaruText 토큰 적용 + 다음 활동 미리보기 추가 (실데이터만)
/// ══════════════════════════════════════════════════════════
class HomeUserScreen extends StatefulWidget {
  const HomeUserScreen({super.key});

  @override
  State<HomeUserScreen> createState() => _HomeUserScreenState();
}

class _HomeUserScreenState extends State<HomeUserScreen> {
  String _name = '사용자';
  ScheduleItem? _currentActivity;
  ScheduleItem? _nextActivity;
  int _totalToday = 0;

  @override
  void initState() {
    super.initState();
    _loadSession();
  }

  Future<void> _loadSession() async {
    final name = await SessionService.getUserName();
    final schedule = await ScheduleStorage.load();
    ScheduleItem? current;
    ScheduleItem? next;
    int total = 0;
    if (schedule != null && schedule.items.isNotEmpty) {
      total = schedule.items.length;
      final now = DateTime.now();
      final nowMin = now.hour * 60 + now.minute;
      int currentIdx = -1;
      for (int i = 0; i < schedule.items.length; i++) {
        if (schedule.items[i].timeMinutes <= nowMin) {
          currentIdx = i;
        }
      }
      if (currentIdx >= 0) {
        current = schedule.items[currentIdx];
        if (currentIdx + 1 < schedule.items.length) {
          next = schedule.items[currentIdx + 1];
        }
      } else {
        // 오늘 첫 일정이 아직 시작 전 — 그게 곧 다음 활동
        next = schedule.items.first;
      }
    }
    if (!mounted) return;
    setState(() {
      _name = name;
      _currentActivity = current;
      _nextActivity = next;
      _totalToday = total;
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
          padding: const EdgeInsets.all(HaruTokens.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Topbar — 인사 + 날짜
              Container(
                padding: const EdgeInsets.all(HaruTokens.space5),
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
                      style: HaruText.h3.copyWith(color: HaruTokens.white),
                    ),
                    const SizedBox(height: HaruTokens.space1),
                    Text(
                      '${_koreanDayName()}, $timeStr',
                      style: HaruText.small.copyWith(
                        color: HaruTokens.white.withValues(alpha: 0.85),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: HaruTokens.space3),

              // Hero — 현재 활동 미리보기 + 다음 활동 (실데이터만)
              if (_currentActivity != null)
                Container(
                  padding: const EdgeInsets.all(HaruTokens.space5),
                  decoration: BoxDecoration(
                    color: HaruTokens.primarySoft,
                    borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                    border: Border.all(color: HaruTokens.primary),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(
                            Symbols.schedule,
                            size: 20,
                            color: HaruTokens.primary,
                            fill: 1,
                          ),
                          const SizedBox(width: HaruTokens.space2),
                          Text(
                            '지금 할 일',
                            style: HaruText.small.copyWith(
                              color: HaruTokens.primary,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: HaruTokens.space2),
                      Text(
                        _currentActivity!.task,
                        style: HaruText.h2,
                      ),
                      Text(
                        '${_currentActivity!.time}부터',
                        style: HaruText.small,
                      ),
                      if (_nextActivity != null) ...[
                        const SizedBox(height: HaruTokens.space3),
                        Container(
                          height: 1,
                          color: HaruTokens.n200,
                        ),
                        const SizedBox(height: HaruTokens.space3),
                        Row(
                          children: [
                            const Icon(
                              Symbols.arrow_forward,
                              size: 16,
                              color: HaruTokens.n400,
                            ),
                            const SizedBox(width: HaruTokens.space2),
                            Expanded(
                              child: Text(
                                '다음: ${_nextActivity!.time} ${_nextActivity!.task}',
                                style: HaruText.small,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                )
              else if (_nextActivity != null)
                // 첫 일정이 아직 시작 전 — 다음 활동만 표시
                Container(
                  padding: const EdgeInsets.all(HaruTokens.space5),
                  decoration: BoxDecoration(
                    color: HaruTokens.accentSoft,
                    borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(
                            Symbols.upcoming,
                            size: 20,
                            color: HaruTokens.accent,
                            fill: 1,
                          ),
                          const SizedBox(width: HaruTokens.space2),
                          Text(
                            '곧 시작해요',
                            style: HaruText.small.copyWith(
                              color: HaruTokens.accent,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: HaruTokens.space2),
                      Text(
                        _nextActivity!.task,
                        style: HaruText.h2,
                      ),
                      Text(
                        '${_nextActivity!.time} 시작',
                        style: HaruText.small,
                      ),
                      if (_totalToday > 1) ...[
                        const SizedBox(height: HaruTokens.space2),
                        Text(
                          '오늘 일정 $_totalToday개',
                          style: HaruText.tiny,
                        ),
                      ],
                    ],
                  ),
                )
              else
                // 일정 없음 — 자유시간
                Container(
                  padding: const EdgeInsets.all(HaruTokens.space5),
                  decoration: BoxDecoration(
                    color: HaruTokens.accentSoft,
                    borderRadius: BorderRadius.circular(HaruTokens.radiusMd),
                  ),
                  child: Column(
                    children: [
                      const Icon(
                        Symbols.wb_sunny,
                        size: 32,
                        color: HaruTokens.accent,
                        fill: 1,
                      ),
                      const SizedBox(height: HaruTokens.space2),
                      Text(
                        '오늘은 자유시간이에요',
                        style: HaruText.h3,
                      ),
                      const SizedBox(height: HaruTokens.space1),
                      Text(
                        '하고 싶은 걸 골라보세요',
                        style: HaruText.small,
                      ),
                    ],
                  ),
                ),

              const SizedBox(height: HaruTokens.space5),

              // Big CTA 1 — 오늘 하루 보기
              Expanded(
                child: _BigCta(
                  label: '오늘 하루 보기',
                  icon: Symbols.play_circle,
                  color: HaruTokens.primary,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const UserScreen()),
                  ),
                ),
              ),
              const SizedBox(height: HaruTokens.space3),

              // Big CTA 2 — 도우미
              Expanded(
                child: _BigCta(
                  label: '하루 도우미에게 물어보기',
                  icon: Symbols.forum,
                  color: HaruTokens.accent,
                  textColor: HaruTokens.n900,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const AgentScreen()),
                  ),
                ),
              ),
              const SizedBox(height: HaruTokens.space2),
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
          padding: const EdgeInsets.all(HaruTokens.space5),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 44, color: textColor, fill: 1),
              const SizedBox(width: HaruTokens.space4),
              Flexible(
                child: Text(
                  label,
                  style: HaruText.h2.copyWith(
                    color: textColor,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
