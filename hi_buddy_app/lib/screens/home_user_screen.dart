import 'dart:async';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../theme/app_theme.dart';
import '../services/session_service.dart';
import '../services/schedule_storage.dart';
import '../services/ui_mode_service.dart';
import '../models/schedule_item.dart';
import '../widgets/now_next_card.dart';
import 'user_screen.dart';
import 'today_screen.dart';
import 'help_screen.dart';
import 'agent_screen.dart';

/// ══════════════════════════════════════════════════════════
/// HomeUserScreen — 당사자용 홈 (v1.5「메이트」루트 4타일)
/// Apple Assistive Access 구조 이식:
///   - 루트 타일 ≤ 4 (R1): 지금 할 일 / 오늘 일과 / 도움 / 메이트
///   - 그리드 ⇄ 줄 레이아웃 토글 (P9), 선택은 기기에 저장
///   - 아이콘 + 라벨 항상 쌍 (R2), 그라데이션 0, 이모지 0
///   - 상단에 「지금 | 다음」 2칸 + 남은 시간 링 (P1, P2)
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
  Timer? _minuteTick;

  @override
  void initState() {
    super.initState();
    _loadSession();
    // 홈을 켜둔 채로 다음 일정 시각을 넘기면 지금/다음·헤더 시각을 다시 계산 (1분 주기)
    _minuteTick = Timer.periodic(const Duration(minutes: 1), (_) => _loadSession());
  }

  @override
  void dispose() {
    _minuteTick?.cancel();
    super.dispose();
  }

  Future<void> _loadSession() async {
    final name = await SessionService.getUserName();
    final schedule = await ScheduleStorage.load();
    ScheduleItem? current;
    ScheduleItem? next;
    if (schedule != null && schedule.items.isNotEmpty) {
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
    });
  }

  String _koreanDayName() {
    const days = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'];
    return days[DateTime.now().weekday - 1];
  }

  Future<void> _push(Widget screen) async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
    // 돌아오면 지금/다음 갱신
    _loadSession();
  }

  Future<void> _toggleLayout() async {
    final next = UiModeService.homeLayout == 'grid' ? 'row' : 'grid';
    await UiModeService.setHomeLayout(next);
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final timeStr = DateFormat('a h시 m분', 'ko').format(DateTime.now());
    final isGrid = UiModeService.homeLayout == 'grid';

    final tiles = <_TileSpec>[
      _TileSpec(
        icon: Symbols.play_circle,
        label: '지금 할 일',
        color: HaruTokensV2.brandWarm,
        filled: true,
        onTap: () => _push(const UserScreen()),
      ),
      _TileSpec(
        icon: Symbols.checklist,
        label: '오늘 일과',
        color: HaruTokensV2.actRestMain,
        onTap: () => _push(const TodayScreen()),
      ),
      _TileSpec(
        icon: Symbols.support,
        label: '도움',
        color: HaruTokensV2.danger,
        onTap: () => _push(const HelpScreen()),
      ),
      _TileSpec(
        icon: Symbols.chat_bubble,
        label: '메이트',
        color: HaruTokensV2.actBodyMain,
        onTap: () => _push(const AgentScreen()),
      ),
    ];

    return Scaffold(
      backgroundColor: HaruTokensV2.surfaceBase,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(HaruTokens.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ─── 헤더 (단일 솔리드) + 레이아웃 토글 ───
              Container(
                padding: const EdgeInsets.all(HaruTokens.space4),
                decoration: BoxDecoration(
                  color: HaruTokensV2.brandWarm,
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
                ),
                child: Row(
                  children: [
                    Expanded(
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
                    _LayoutToggle(isGrid: isGrid, onTap: _toggleLayout),
                  ],
                ),
              ),
              const SizedBox(height: HaruTokens.space3),

              // ─── 지금 | 다음 ───
              NowNextCard(
                current: _currentActivity,
                next: _nextActivity,
                onTap: () => _push(const UserScreen()),
              ),
              const SizedBox(height: HaruTokens.space4),

              // ─── 루트 4타일 ───
              Expanded(
                child: isGrid ? _Grid(tiles: tiles) : _Rows(tiles: tiles),
              ),
            ],
          ),
        ),
      ),
      // SOS FAB 는 「도움」 타일이 대체 (simple 모드에서 메이트 타일을 덮는 문제 방지)
      floatingActionButton: null,
    );
  }
}

class _TileSpec {
  final IconData icon;
  final String label;
  final Color color;
  final bool filled;
  final VoidCallback onTap;
  const _TileSpec({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
    this.filled = false,
  });
}

class _Grid extends StatelessWidget {
  final List<_TileSpec> tiles;
  const _Grid({required this.tiles});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: Row(
            children: [
              Expanded(child: _Tile(spec: tiles[0])),
              const SizedBox(width: HaruTokens.space3),
              Expanded(child: _Tile(spec: tiles[1])),
            ],
          ),
        ),
        const SizedBox(height: HaruTokens.space3),
        Expanded(
          child: Row(
            children: [
              Expanded(child: _Tile(spec: tiles[2])),
              const SizedBox(width: HaruTokens.space3),
              Expanded(child: _Tile(spec: tiles[3])),
            ],
          ),
        ),
      ],
    );
  }
}

class _Rows extends StatelessWidget {
  final List<_TileSpec> tiles;
  const _Rows({required this.tiles});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (int i = 0; i < tiles.length; i++) ...[
          Expanded(child: _Tile(spec: tiles[i], horizontal: true)),
          if (i < tiles.length - 1) const SizedBox(height: HaruTokens.space3),
        ],
      ],
    );
  }
}

class _Tile extends StatelessWidget {
  final _TileSpec spec;
  final bool horizontal;
  const _Tile({required this.spec, this.horizontal = false});

  @override
  Widget build(BuildContext context) {
    final fg = spec.filled ? HaruTokensV2.onBrand : HaruTokensV2.inkPrimary;
    final iconColor = spec.filled ? HaruTokensV2.onBrand : spec.color;
    final icon = Icon(spec.icon, size: horizontal ? 36 : 44, color: iconColor, fill: 1);
    final label = Text(
      spec.label,
      style: HaruText.h2.copyWith(color: fg, fontWeight: FontWeight.w800),
      textAlign: horizontal ? TextAlign.start : TextAlign.center,
      maxLines: 2,
      overflow: TextOverflow.ellipsis,
    );

    return Semantics(
      button: true,
      label: spec.label,
      child: Material(
        color: spec.filled ? spec.color : HaruTokensV2.surfaceCard,
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
        child: InkWell(
          borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
          onTap: spec.onTap,
          child: Container(
            padding: const EdgeInsets.all(HaruTokens.space4),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(HaruTokensV2.radiusLg),
              border: spec.filled
                  ? null
                  : Border.all(color: spec.color, width: 2),
            ),
            child: horizontal
                ? Row(
                    children: [
                      icon,
                      const SizedBox(width: HaruTokens.space4),
                      Expanded(child: label),
                    ],
                  )
                : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      icon,
                      const SizedBox(height: HaruTokens.space3),
                      label,
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}

/// 그리드 ⇄ 줄 토글. 아이콘+라벨 (R2).
class _LayoutToggle extends StatelessWidget {
  final bool isGrid;
  final VoidCallback onTap;
  const _LayoutToggle({required this.isGrid, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final label = isGrid ? '줄로' : '모아서';
    return Semantics(
      button: true,
      label: '화면 배치 바꾸기. 지금은 ${isGrid ? "모아 보기" : "줄로 보기"}',
      child: Material(
        color: HaruTokensV2.onBrand.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
        child: InkWell(
          borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
          onTap: onTap,
          child: Container(
            constraints: const BoxConstraints(
              minWidth: HaruTokensV2.minTouchTarget,
              minHeight: HaruTokensV2.minTouchTarget,
            ),
            padding: const EdgeInsets.symmetric(
              horizontal: HaruTokens.space3,
              vertical: HaruTokens.space2,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isGrid ? Symbols.view_agenda : Symbols.grid_view,
                  size: 22,
                  color: HaruTokensV2.onBrand,
                ),
                const SizedBox(width: HaruTokens.space1),
                Text(
                  label,
                  style: HaruText.small.copyWith(
                    color: HaruTokensV2.onBrand,
                    fontWeight: FontWeight.w800,
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
