import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';
import '../models/schedule_item.dart';
import '../services/schedule_storage.dart';
import '../services/ui_mode_service.dart';
import '../theme/app_theme.dart';
import '../widgets/activity_card.dart';
import '../widgets/haru_bottom_bar.dart';
import 'user_screen.dart';

/// ══════════════════════════════════════════════════════════
/// TodayScreen — 「오늘 일과」 타임라인 (P3 + P12)
/// - 지난 항목 회색화 (Tiimo)
/// - simple/kiosk: 스크롤 대신 위/아래 페이지 버튼 (ACM 2024, R9)
/// - 항목 탭 → 오늘 하루(UserScreen)
/// ══════════════════════════════════════════════════════════
class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key});

  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  List<ScheduleItem> _items = const [];
  bool _loading = true;
  int _page = 0;
  static const _pageSize = 3;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final schedule = await ScheduleStorage.load();
    if (!mounted) return;
    final items = schedule?.items ?? const <ScheduleItem>[];
    // 현재 진행 중 항목이 있는 페이지부터 보이게
    final nowMin = DateTime.now().hour * 60 + DateTime.now().minute;
    int activeIdx = 0;
    for (int i = 0; i < items.length; i++) {
      if (items[i].timeMinutes <= nowMin) activeIdx = i;
    }
    setState(() {
      _items = items;
      _loading = false;
      _page = activeIdx ~/ _pageSize;
    });
  }

  int get _activeIndex {
    final nowMin = DateTime.now().hour * 60 + DateTime.now().minute;
    int idx = -1;
    for (int i = 0; i < _items.length; i++) {
      if (_items[i].timeMinutes <= nowMin) idx = i;
    }
    return idx;
  }

  void _open() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const UserScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final paged = UiModeService.isAccessibilityMode;

    return Scaffold(
      backgroundColor: HaruTokensV2.surfaceBase,
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Symbols.checklist, size: 24, color: HaruTokensV2.brandWarm, fill: 1),
            SizedBox(width: HaruTokens.space2),
            Text('오늘 일과'),
          ],
        ),
        automaticallyImplyLeading: false,
      ),
      bottomNavigationBar: HaruBottomBar.maybe(context),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _items.isEmpty
                ? _Empty()
                : paged
                    ? _buildPaged()
                    : _buildList(),
      ),
    );
  }

  Widget _card(int i) {
    final active = _activeIndex;
    final item = _items[i];
    final isPast = i < active;
    final isActive = i == active;
    return Padding(
      padding: const EdgeInsets.only(bottom: HaruTokens.space3),
      child: Opacity(
        opacity: isPast ? 0.45 : 1.0,
        child: Container(
          decoration: isActive
              ? BoxDecoration(
                  borderRadius: BorderRadius.circular(HaruTokensV2.radiusMd),
                  border: Border.all(color: HaruTokensV2.brandWarm, width: 2),
                )
              : null,
          child: ActivityCard(
            type: item.type,
            task: isPast ? '${item.task} · 끝' : item.task,
            time: item.time,
            isActive: isActive,
            onTap: _open,
          ),
        ),
      ),
    );
  }

  Widget _buildList() {
    return ListView.builder(
      padding: const EdgeInsets.all(HaruTokens.space4),
      itemCount: _items.length,
      itemBuilder: (_, i) => _card(i),
    );
  }

  /// 스크롤 선택제: 3개씩 한 페이지, 위/아래 큰 버튼으로 이동
  Widget _buildPaged() {
    final pages = (_items.length + _pageSize - 1) ~/ _pageSize;
    final start = _page * _pageSize;
    final end = (start + _pageSize).clamp(0, _items.length);

    return Padding(
      padding: const EdgeInsets.all(HaruTokens.space4),
      child: Column(
        children: [
          Expanded(
            child: Column(
              children: [for (int i = start; i < end; i++) _card(i)],
            ),
          ),
          Row(
            children: [
              Expanded(
                child: _PageButton(
                  icon: Symbols.keyboard_arrow_up,
                  label: '위로',
                  enabled: _page > 0,
                  onTap: () => setState(() => _page--),
                ),
              ),
              const SizedBox(width: HaruTokens.space3),
              Text(
                '${_page + 1} / $pages',
                style: HaruText.body.copyWith(
                  color: HaruTokensV2.inkBody,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(width: HaruTokens.space3),
              Expanded(
                child: _PageButton(
                  icon: Symbols.keyboard_arrow_down,
                  label: '아래로',
                  enabled: _page < pages - 1,
                  onTap: () => setState(() => _page++),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PageButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool enabled;
  final VoidCallback onTap;

  const _PageButton({
    required this.icon,
    required this.label,
    required this.enabled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: HaruTokensV2.comfortTouchTarget + 8,
      child: OutlinedButton.icon(
        onPressed: enabled ? onTap : null,
        icon: Icon(icon, size: 28),
        label: Text(label, style: HaruText.h3),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(HaruTokens.space8),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Symbols.event_busy, size: 64, color: HaruTokensV2.inkMuted),
            const SizedBox(height: HaruTokens.space4),
            Text(
              '오늘 일정이 아직 없음',
              style: HaruText.h2.copyWith(color: HaruTokensV2.inkPrimary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: HaruTokens.space2),
            Text(
              '선생님이 일정을 만들면 여기에 나타남',
              style: HaruText.body.copyWith(color: HaruTokensV2.inkBody),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
