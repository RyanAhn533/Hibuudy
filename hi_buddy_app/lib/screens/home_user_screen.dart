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
/// HomeUserScreen — 당사자용 홈 (v1.4「메이트」)
/// HaruTokensV2 적용: warm coral brand + warm-tinted surface
/// 폐기: 그라데이션 (P6 적출) / "~님" 호칭 (H1) / "~보세요" (H1)
/// ══════════════════════════════════════════════════════════
class HomeUserScreen extends StatefulWidget {
  const HomeUserScreen({super.key});

  @override
  State<HomeUserScreen> createState() => _HomeUserScreenState();
}

class _HomeUserScreenState extends State<HomeUserScreen> {
  String _name = '';
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
      backgroundColor: HaruTokensV2.surfaceBase,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(HaruTokens.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ─── 헤더 (단일 솔리드, 그라데이션 폐기) ───
              Container(
                padding: const EdgeInsets.all(HaruTokens.space5),
                decoration: BoxDecoration(
                  color: HaruTokensV2.brandWarm,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _name.isEmpty ? '안녕' : '$_name 안녕',
                      style: HaruText.h2.copyWith(
                        color: HaruTokensV2.onBrand,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: HaruTokens.space1),
                    Text(
                      '${_koreanDayName()} $timeStr',
                      style: HaruText.small.copyWith(
                        color: HaruTokensV2.onBrand.withValues(alpha: 0.85),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: HaruTokens.space3),

              // ─── 히어로 카드 (3 상태) ───
              if (_currentActivity != null)
                _HeroCard(
                  badge: '지금 할 일',
                  badgeIcon: Symbols.schedule,
                  badgeColor: HaruTokensV2.brandWarm,
                  title: _currentActivity!.task,
                  subtitle: '${_currentActivity!.time}부터',
                  bgColor: HaruTokensV2.brandWarmSoft,
                  borderColor: HaruTokensV2.brandWarm,
                  next: _nextActivity != null
                      ? '다음: ${_nextActivity!.time} ${_nextActivity!.task}'
                      : null,
                )
              else if (_nextActivity != null)
                _HeroCard(
                  badge: '곧 시작',
                  badgeIcon: Symbols.upcoming,
                  badgeColor: HaruTokensV2.actRestMain,
                  title: _nextActivity!.task,
                  subtitle: '${_nextActivity!.time} 시작',
                  bgColor: HaruTokensV2.actRestSoft,
                  borderColor: HaruTokensV2.actRestMain,
                  next: _totalToday > 1 ? '오늘 일정 $_totalToday개' : null,
                )
              else
                _HeroCard(
                  badge: '자유시간',
                  badgeIcon: Symbols.wb_sunny,
                  badgeColor: HaruTokensV2.actRestMain,
                  title: '오늘은 자유시간',
                  subtitle: null,
                  bgColor: HaruTokensV2.actRestSoft,
                  borderColor: HaruTokensV2.actRestMain,
                  next: null,
                ),

              const SizedBox(height: HaruTokens.space4),

              // ─── CTA 1: 오늘 일정 (강조) ───
              Expanded(
                child: _BigCta(
                  label: '오늘 일정',
                  icon: Symbols.list_alt,
                  color: HaruTokensV2.brandWarm,
                  textColor: HaruTokensV2.onBrand,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const UserScreen()),
                  ),
                ),
              ),
              const SizedBox(height: HaruTokens.space3),

              // ─── CTA 2: 메이트 (보조) ───
              Expanded(
                child: _BigCta(
                  label: '메이트한테 물어보기',
                  icon: Symbols.chat_bubble,
                  color: HaruTokensV2.surfaceCard,
                  textColor: HaruTokensV2.inkPrimary,
                  borderColor: HaruTokensV2.brandWarm,
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

/// 히어로 카드 — 3 상태 통일 위젯
class _HeroCard extends StatelessWidget {
  final String badge;
  final IconData badgeIcon;
  final Color badgeColor;
  final String title;
  final String? subtitle;
  final Color bgColor;
  final Color borderColor;
  final String? next;

  const _HeroCard({
    required this.badge,
    required this.badgeIcon,
    required this.badgeColor,
    required this.title,
    required this.subtitle,
    required this.bgColor,
    required this.borderColor,
    required this.next,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(HaruTokens.space5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        border: Border.all(color: borderColor, width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(badgeIcon, size: 18, color: badgeColor, fill: 0),
              const SizedBox(width: HaruTokens.space2),
              Text(
                badge,
                style: HaruText.small.copyWith(
                  color: badgeColor,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: HaruTokens.space2),
          Text(
            title,
            style: HaruText.h2.copyWith(color: HaruTokensV2.inkPrimary),
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 2),
            Text(
              subtitle!,
              style: HaruText.small.copyWith(color: HaruTokensV2.inkBody),
            ),
          ],
          if (next != null) ...[
            const SizedBox(height: HaruTokens.space3),
            Container(height: 1, color: HaruTokensV2.borderSoft),
            const SizedBox(height: HaruTokens.space3),
            Row(
              children: [
                Icon(Symbols.arrow_forward,
                    size: 14, color: HaruTokensV2.inkMuted),
                const SizedBox(width: HaruTokens.space2),
                Expanded(
                  child: Text(
                    next!,
                    style: HaruText.small.copyWith(color: HaruTokensV2.inkBody),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _BigCta extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final Color textColor;
  final Color? borderColor;
  final VoidCallback onTap;

  const _BigCta({
    required this.label,
    required this.icon,
    required this.color,
    required this.textColor,
    required this.onTap,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
      child: InkWell(
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
            border: borderColor != null
                ? Border.all(color: borderColor!, width: 1.5)
                : null,
          ),
          padding: const EdgeInsets.all(HaruTokens.space5),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.start,
            children: [
              Icon(icon, size: 36, color: textColor, fill: 1),
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
